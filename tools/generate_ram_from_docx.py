#!/usr/bin/env python3
"""Genera emparejamientos RAM desde la tabla operativa de un DOCX.

El script extrae la tabla resumen del RAM, preserva creditos parciales del
tipo ``2/5`` y valida que el uso acumulado de cada asignatura LUT no supere su
capacidad maxima.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import zipfile
from collections import OrderedDict
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from matcher_core import (  # noqa: E402
    export_ram_markdown,
    get_ulpgc_credits,
    load_lut_course_by_code,
    load_ulpgc_courses,
    parse_float_credits,
    search_lut_courses,
    validate_assignments,
)

DOCX_DEFAULT = Path("informacion/RAM_v2627_decimosexta_correccion.docx")
JSON_DEFAULT = Path("emparejamientos.json")
MARKDOWN_DEFAULT = Path("RAM_emparejamientos.md")
VALIDATION_DEFAULT = Path("RAM_emparejamientos_validacion.md")
TABLE_DEFAULT = 2
WORD_NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}


def normalize_spaces(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def extract_docx_tables(docx_path: Path) -> list[list[list[str]]]:
    with zipfile.ZipFile(docx_path) as archive:
        xml = archive.read("word/document.xml")

    root = ET.fromstring(xml)
    tables: list[list[list[str]]] = []
    for table_xml in root.findall(".//w:tbl", WORD_NS):
        table: list[list[str]] = []
        for row_xml in table_xml.findall("w:tr", WORD_NS):
            row: list[str] = []
            for cell_xml in row_xml.findall("w:tc", WORD_NS):
                texts = [node.text or "" for node in cell_xml.findall(".//w:t", WORD_NS)]
                row.append(normalize_spaces("".join(texts)))
            table.append(row)
        tables.append(table)
    return tables


def split_subject(raw_subject: str) -> tuple[str, str]:
    subject = normalize_spaces(raw_subject)
    subject = re.sub(r"\[(?:\d+|[1-2])\s*sem\]", "", subject, flags=re.IGNORECASE).strip()
    subject = re.sub(r"Falta física estadística y sistemas cuanticos", "", subject, flags=re.IGNORECASE).strip()
    subject = re.sub(r"Espacios de medida e integración", "", subject, flags=re.IGNORECASE).strip()
    if " - " in subject:
        short, name = subject.split(" - ", 1)
    elif " – " in subject:
        short, name = subject.split(" – ", 1)
    else:
        short, name = "", subject
    return short.strip(), name.strip()


def parse_semester(raw_name: str) -> str:
    match = re.search(r"\[([^\]]*sem)\]", raw_name, flags=re.IGNORECASE)
    return match.group(1).replace(" ", "") if match else ""


def parse_credit_cell(value: str, lut_max_fallback: float) -> tuple[float, float]:
    text = normalize_spaces(value).replace(",", ".")
    if not text:
        return lut_max_fallback, lut_max_fallback

    if "-" in text:
        numbers = [parse_float_credits(part) for part in re.findall(r"\d+(?:\.\d+)?", text)]
        if numbers:
            return min(numbers), max(numbers)

    if "/" in text:
        assigned_text, max_text = text.split("/", 1)
        return parse_float_credits(assigned_text), parse_float_credits(max_text)

    if ";" in text:
        # Celdas historicas pueden incluir "5; 2/5"; la tabla operativa no
        # deberia necesitarlas, pero se conserva la parte fraccionaria si existe.
        for part in reversed([part.strip() for part in text.split(";")]):
            if "/" in part:
                return parse_credit_cell(part, lut_max_fallback)
        text = text.split(";")[-1].strip()

    value_float = parse_float_credits(text)
    return value_float, value_float


def find_lut_by_title(title: str) -> dict | None:
    normalized = normalize_spaces(re.sub(r"\[[^\]]+\]", "", title)).lower()
    for candidate in search_lut_courses(normalized, limit=20):
        if normalize_spaces(candidate.get("name", "")).lower() == normalized:
            return candidate
    return None


def resolve_lut_course(code: str, title: str, notes: list[str]) -> dict | None:
    course = load_lut_course_by_code(code)
    clean_title = normalize_spaces(re.sub(r"\[[^\]]+\]", "", title))
    if not course:
        by_title = find_lut_by_title(clean_title)
        if by_title:
            notes.append(
                f"{code}: no aparece en catalogo LUT; se usa {by_title['code']} por coincidencia exacta de titulo."
            )
            return by_title
        notes.append(f"{code}: no aparece en catalogo LUT ni se encontro coincidencia exacta por titulo.")
        return None

    catalog_title = normalize_spaces(course.get("name", ""))
    if clean_title and catalog_title.lower() != clean_title.lower():
        by_title = find_lut_by_title(clean_title)
        if by_title and by_title.get("code") != code:
            notes.append(
                f"{code}: el DOCX lo asocia a '{clean_title}', pero el catalogo LUT identifica ese titulo como "
                f"{by_title['code']}; se usa {by_title['code']}."
            )
            return by_title
        notes.append(
            f"{code}: titulo DOCX '{clean_title}' no coincide exactamente con catalogo '{catalog_title}'."
        )
    return course


def build_assignments_from_table(table: list[list[str]]) -> tuple[OrderedDict[str, list[dict]], list[str], list[str]]:
    assignments: OrderedDict[str, list[dict]] = OrderedDict()
    notes: list[str] = []
    skipped: list[str] = []
    current_ulpgc = ""
    current_entry: dict | None = None

    for row in table[1:]:
        cells = row + [""] * (6 - len(row))
        ulpgc_code, ulpgc_subject, _ulpgc_credits, lut_code, lut_title, credit_cell = cells[:6]

        if ulpgc_code.startswith("ASIGNATURAS"):
            continue

        if ulpgc_code:
            current_ulpgc = ulpgc_code
            current_entry = None

        if not current_ulpgc:
            continue

        if not lut_code and not lut_title and credit_cell and current_entry:
            assigned, lut_max = parse_credit_cell(credit_cell, current_entry["lut_credits"])
            current_entry["ulpgc_credits"] = assigned
            current_entry["lut_credits"] = lut_max
            continue

        if not lut_code:
            if ulpgc_code:
                _short, subject_name = split_subject(ulpgc_subject)
                skipped.append(f"{ulpgc_code} {subject_name}: sin asignatura LUT en tabla operativa.")
            continue

        lut_course = resolve_lut_course(lut_code, lut_title, notes)
        semester = parse_semester(lut_title)
        lut_max_fallback = parse_float_credits(lut_course.get("credits_max", 0)) if lut_course else 0.0
        assigned, lut_max = parse_credit_cell(credit_cell, lut_max_fallback)
        if not lut_max and lut_max_fallback:
            lut_max = lut_max_fallback
        if not assigned and lut_max:
            assigned = lut_max
        if "-" in credit_cell and "/" not in credit_cell:
            notes.append(
                f"{current_ulpgc}/{lut_code}: el DOCX indica rango {credit_cell} ECTS; "
                f"se usa {assigned:g}/{lut_max:g} para representar el minimo operativo."
            )

        entry = {
            "lut_code": lut_course.get("code", lut_code) if lut_course else lut_code,
            "lut_name": lut_course.get("name", normalize_spaces(re.sub(r"\[[^\]]+\]", "", lut_title))) if lut_course else lut_title,
            "ulpgc_credits": assigned,
            "lut_credits": lut_max,
            "lut_semester": semester,
        }
        assignments.setdefault(current_ulpgc, [])
        assignments[current_ulpgc].append(entry)
        current_entry = entry

    return assignments, notes, skipped


def write_assignments_json(
    output_path: Path,
    assignments: OrderedDict[str, list[dict]],
    courses_dict: dict[str, dict],
    source_docx: Path,
    table_number: int,
    notes: list[str],
    skipped: list[str],
) -> None:
    output_data = {
        "source_docx": str(source_docx).replace("\\", "/"),
        "source_table": f"Tabla {table_number}",
        "notes": notes + skipped,
        "total_ulpgc_assigned": len(assignments),
        "assignments": [],
    }

    for ulpgc_code, entries in assignments.items():
        course = courses_dict.get(ulpgc_code, {})
        output_data["assignments"].append({
            "ulpgc_code": ulpgc_code,
            "ulpgc_name": course.get("name", "N/A"),
            "ulpgc_credits": get_ulpgc_credits(course) if course else 0.0,
            "ulpgc_type": course.get("type", "N/A"),
            "lut_courses": [
                {
                    "lut_code": entry["lut_code"],
                    "lut_name": entry["lut_name"],
                    "lut_semester": entry["lut_semester"],
                    "ulpgc_credits_assigned": entry["ulpgc_credits"],
                    "lut_credits_max": entry["lut_credits"],
                }
                for entry in entries
            ],
        })

    output_path.write_text(json.dumps(output_data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_validation_markdown(
    output_path: Path,
    source_docx: Path,
    table_number: int,
    validation: dict,
    notes: list[str],
    skipped: list[str],
) -> None:
    deficits = [item for item in validation["ulpgc_balance"] if item["status"] == "deficit"]
    lines = [
        "# Validacion de emparejamientos RAM",
        "",
        f"- Fuente operativa: `{source_docx.as_posix()}`.",
        f"- Tabla usada: `Tabla {table_number}`.",
        f"- Estado creditos/capacidad: {'OK' if validation['ok'] else 'ERROR'}.",
        "",
        "## Ambiguedades documentales",
        "",
    ]
    for note in notes + skipped:
        lines.append(f"- {note}")
    if not notes and not skipped:
        lines.append("- Ninguna.")

    lines.extend(["", "## Deficits por asignatura", ""])
    for item in deficits:
        lines.append(
            f"- `{item['ulpgc_code']}` {item['ulpgc_name']}: "
            f"{item['assigned_lut_credits']:g}/{item['ulpgc_credits']:g} ECTS ({item['difference']:g})."
        )
    if not deficits:
        lines.append("- Ninguno.")

    lines.extend(["", "## Errores", ""])
    for error in validation["errors"]:
        lines.append(f"- {error}")
    if not validation["errors"]:
        lines.append("- Ninguno.")

    lines.extend(["", "## Advertencias", ""])
    for warning in validation["warnings"]:
        lines.append(f"- {warning}")
    if not validation["warnings"]:
        lines.append("- Ninguna.")

    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Genera emparejamientos RAM desde un DOCX")
    parser.add_argument("--docx", type=Path, default=DOCX_DEFAULT)
    parser.add_argument("--table", type=int, default=TABLE_DEFAULT, help="Numero de tabla DOCX, base 1")
    parser.add_argument("--json-output", type=Path, default=JSON_DEFAULT)
    parser.add_argument("--md-output", type=Path, default=MARKDOWN_DEFAULT)
    parser.add_argument("--validation-output", type=Path, default=VALIDATION_DEFAULT)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    tables = extract_docx_tables(args.docx)
    if args.table < 1 or args.table > len(tables):
        raise SystemExit(f"Tabla {args.table} fuera de rango; el DOCX contiene {len(tables)} tablas.")

    courses = load_ulpgc_courses()
    courses_dict = {course["code"]: course for course in courses}
    assignments, notes, skipped = build_assignments_from_table(tables[args.table - 1])
    validation = validate_assignments(assignments, courses_dict)

    if args.dry_run:
        print(json.dumps({
            "assignments": len(assignments),
            "notes": notes,
            "skipped": skipped,
            "validation": validation,
        }, ensure_ascii=False, indent=2))
        return 0 if validation["ok"] else 1

    write_assignments_json(args.json_output, assignments, courses_dict, args.docx, args.table, notes, skipped)
    export_ram_markdown(assignments, courses_dict, courses, output_file=str(args.md_output))
    write_validation_markdown(args.validation_output, args.docx, args.table, validation, notes, skipped)

    if not validation["ok"]:
        print(json.dumps(validation, ensure_ascii=False, indent=2))
        return 1

    print(
        json.dumps(
            {
                "ok": True,
                "assignments": len(assignments),
                "json": str(args.json_output),
                "markdown": str(args.md_output),
                "validation": str(args.validation_output),
                "notes": notes + skipped,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
