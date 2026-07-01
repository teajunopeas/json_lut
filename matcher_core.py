#!/usr/bin/env python3
"""Core reutilizable para el matcher ULPGC -> LUT.

Este modulo contiene la logica de datos, scoring, filtros, asignaciones y
exportacion sin depender de la interfaz interactiva de Rich ni de input().
"""

from __future__ import annotations

import json
import sqlite3
from itertools import combinations
from pathlib import Path
from typing import Any

DB_PATH = Path("lut_courses.db")
ULPGC_PATH = Path("ulpgc_courses.json")
MODEL_NAME = "all-MiniLM-L6-v2"
LOCAL_MODEL_PATH = Path("models/all-MiniLM-L6-v2")
MATCH_THRESHOLD = 75.0
SEARCH_LIMIT = 40
RESULT_LIMIT = 10
MORE_RESULTS_STEP = 20

_MODEL: Any | None = None
_UTIL: Any | None = None


def normalize_credit_value(value: str | int | float | None) -> float:
    """Convierte un valor de creditos a float con 0.0 como fallback."""
    return parse_float_credits(value)


def normalize_ulpgc_course(course: dict) -> dict:
    """Devuelve una asignatura ULPGC con claves y tipos consistentes."""
    normalized = dict(course)
    normalized.pop("is_manadatory", None)

    credits_value = course.get("credits")
    if credits_value in (None, ""):
        credits_value = course.get("ects")
    credits_float = normalize_credit_value(credits_value)

    normalized["credits"] = credits_float
    normalized["ects"] = credits_float
    normalized["credits_min"] = credits_float
    normalized["credits_max"] = credits_float

    if "semester" in normalized:
        try:
            normalized["semester"] = int(normalized["semester"])
        except (TypeError, ValueError):
            pass

    return normalized


def get_ulpgc_credits(course: dict) -> float:
    """Devuelve los ECTS canonicos de una asignatura ULPGC normalizada."""
    credits_max = course.get("credits_max")
    if credits_max not in (None, ""):
        return parse_float_credits(credits_max)

    credits = course.get("credits")
    if credits not in (None, ""):
        return parse_float_credits(credits)

    return parse_float_credits(course.get("ects", 0))


def get_model() -> Any:
    """Carga el modelo de embeddings una sola vez por proceso."""
    global _MODEL, _UTIL
    if _MODEL is None:
        from sentence_transformers import SentenceTransformer, util

        _UTIL = util
        if LOCAL_MODEL_PATH.exists():
            _MODEL = SentenceTransformer(str(LOCAL_MODEL_PATH), local_files_only=True)
        else:
            _MODEL = SentenceTransformer(MODEL_NAME)
            LOCAL_MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
            _MODEL.save(str(LOCAL_MODEL_PATH))
    return _MODEL


def load_ulpgc_courses(path: Path = ULPGC_PATH) -> list[dict]:
    """Carga asignaturas ULPGC y comprueba que todas tengan keywords."""
    with open(path, encoding="utf-8-sig") as file:
        courses = [normalize_ulpgc_course(course) for course in json.load(file)]

    missing_keywords = [
        course.get("code", "SIN_CODIGO")
        for course in courses
        if not course.get("keywords")
    ]
    if missing_keywords:
        missing = ", ".join(missing_keywords)
        raise ValueError(f"Faltan keywords en {path}: {missing}")

    return courses


def prepare_text(content: str, outcomes: str, name: str = "") -> str:
    """Une los campos descriptivos disponibles para calcular embeddings."""
    parts = []
    if content and len(str(content).strip()) > 20:
        parts.append(str(content))
    if outcomes and len(str(outcomes).strip()) > 20:
        parts.append(str(outcomes))
    if not parts and name:
        parts.append(str(name))
    return " ".join(parts).strip()


def similarity_percent(source_text: str, target_text: str) -> float:
    """Calcula similitud semantica entre dos textos como porcentaje."""
    if not source_text or not target_text:
        return 0.0

    model = get_model()
    util = _UTIL
    source_emb = model.encode(source_text, convert_to_tensor=True)
    target_emb = model.encode(target_text, convert_to_tensor=True)
    return round(util.cos_sim(source_emb, target_emb).item() * 100, 1)


def format_fts_query(keywords: list[str]) -> str:
    """Construye una consulta FTS con keywords compuestas como frases."""
    quoted_keywords = []
    for keyword in keywords:
        safe_keyword = str(keyword).replace('"', '""').strip()
        if safe_keyword:
            quoted_keywords.append(f'"{safe_keyword}"')
    return " OR ".join(quoted_keywords)


def search_keywords(keywords: list[str], limit: int = SEARCH_LIMIT) -> list[dict]:
    """Devuelve candidatos LUT encontrados por FTS a partir de keywords."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    query = format_fts_query(keywords)
    sql = """
        SELECT code, name, credits_min, credits_max, course_level, periods, language,
               is_exchange, equivalent_courses, content, learning_outcomes
        FROM courses
        WHERE (courses MATCH ?)
          AND (
            (content IS NOT NULL AND content != '')
            OR (learning_outcomes IS NOT NULL AND learning_outcomes != '')
          )
        ORDER BY rank LIMIT ?
    """
    cursor = conn.execute(sql, (query, limit))
    results = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return results


def score_similarity(course: dict, candidates: list[dict]) -> list[dict]:
    """Ordena candidatos por similitud de contenido y resultados."""
    model = get_model()
    util = _UTIL
    ulpgc_content = prepare_text(course.get("content", ""), "", course.get("name", ""))
    ulpgc_outcomes = prepare_text("", course.get("learningOutcomes", ""), course.get("name", ""))
    ulpgc_combined = prepare_text(
        course.get("content", ""),
        course.get("learningOutcomes", ""),
        course.get("name", ""),
    )

    ulpgc_content_emb = model.encode(ulpgc_content, convert_to_tensor=True)
    ulpgc_outcomes_emb = model.encode(ulpgc_outcomes, convert_to_tensor=True)
    ulpgc_combined_emb = model.encode(ulpgc_combined, convert_to_tensor=True)

    scored = []
    for candidate in candidates:
        lut_content = prepare_text(candidate.get("content", ""), "", candidate.get("name", ""))
        lut_outcomes = prepare_text("", candidate.get("learning_outcomes", ""), candidate.get("name", ""))
        lut_combined = prepare_text(
            candidate.get("content", ""),
            candidate.get("learning_outcomes", ""),
            candidate.get("name", ""),
        )

        lut_content_emb = model.encode(lut_content, convert_to_tensor=True)
        lut_outcomes_emb = model.encode(lut_outcomes, convert_to_tensor=True)
        lut_combined_emb = model.encode(lut_combined, convert_to_tensor=True)

        content_score = round(util.cos_sim(ulpgc_content_emb, lut_content_emb).item() * 100, 1)
        outcomes_score = round(util.cos_sim(ulpgc_outcomes_emb, lut_outcomes_emb).item() * 100, 1)
        combined_score = round(util.cos_sim(ulpgc_combined_emb, lut_combined_emb).item() * 100, 1)
        best_score = max(content_score, outcomes_score, combined_score)

        scored.append({
            **candidate,
            "content_score": content_score,
            "outcomes_score": outcomes_score,
            "combined_score": combined_score,
            "best_score": best_score,
            "meets_threshold": best_score >= MATCH_THRESHOLD,
        })

    scored.sort(key=lambda item: item["best_score"], reverse=True)
    return scored


def parse_float_credits(value: str | int | float) -> float:
    """Normaliza un valor de creditos a float."""
    if value is None:
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    try:
        text = str(value).replace(",", ".").strip()
        return float(text)
    except ValueError:
        return 0.0


def course_matches_filters(course: dict, config: dict) -> bool:
    """Comprueba si una asignatura ULPGC pasa los filtros activos."""
    if course.get("type") == "optativa" and not config["show_optatives"]:
        return False

    semester_filter = config.get("semester_filter")
    if semester_filter not in (None, "", "todos"):
        try:
            selected = parse_semester_filter(semester_filter)
            return int(course.get("semester", 0)) in selected
        except (TypeError, ValueError):
            return False

    return True


def semester_filter_label(config: dict) -> str:
    """Devuelve una etiqueta legible del filtro de semestre activo."""
    semester_filter = config.get("semester_filter")
    if semester_filter in (None, "", "todos"):
        return "Todos"
    return str(semester_filter)


def parse_semester_filter(semester_filter: str | int | None) -> set[int]:
    """Convierte una entrada tipo '5,6' o '5-6' en un conjunto de semestres."""
    if semester_filter in (None, "", "todos"):
        return set()

    text = str(semester_filter).replace(" ", "")
    values: set[int] = set()
    for token in text.split(","):
        if not token:
            continue
        if "-" in token:
            start_text, end_text = token.split("-", 1)
            start = int(start_text)
            end = int(end_text)
            low, high = sorted((start, end))
            values.update(range(low, high + 1))
            continue
        values.add(int(token))
    return values


def is_master_or_higher(course_level: str | None) -> bool:
    """Detecta si el nivel LUT corresponde a master o superior."""
    if not course_level:
        return False
    normalized = str(course_level).strip().lower()
    return any(keyword in normalized for keyword in ("master", "maister", "postgraduate", "doctoral", "doctor"))


def lut_level_filter_label(config: dict) -> str:
    """Devuelve una etiqueta legible del filtro de nivel LUT."""
    return "sí" if config.get("show_master_or_higher", True) else "no"


def lut_period_filter_label(config: dict) -> str:
    """Devuelve una etiqueta legible del filtro de periodo LUT."""
    lut_period_filter = config.get("lut_period_filter")
    if lut_period_filter in (None, "", "todos"):
        return "Todos"
    return str(lut_period_filter)


def parse_period_filter(period_filter: str | int | None) -> set[str]:
    """Convierte una entrada tipo '1,2' o '1-2' en un conjunto de periodos."""
    if period_filter in (None, "", "todos"):
        return set()

    text = str(period_filter).replace(" ", "")
    values: set[str] = set()
    for token in text.split(","):
        if not token:
            continue
        if "-" in token:
            start_text, end_text = token.split("-", 1)
            start = int(start_text)
            end = int(end_text)
            low, high = sorted((start, end))
            values.update(str(number) for number in range(low, high + 1))
            continue
        values.add(str(int(token)))
    return values


def period_matches_filter(periods: str | None, period_filter: str | int | None) -> bool:
    """Comprueba si un curso LUT se ofrece en el periodo solicitado."""
    if period_filter in (None, "", "todos"):
        return True
    if not periods:
        return False

    wanted = parse_period_filter(period_filter)
    available = [part.strip() for part in str(periods).split(",") if part.strip()]
    return any(period in wanted for period in available)


def filter_lut_candidates(candidates: list[dict], config: dict) -> list[dict]:
    """Aplica los filtros activos sobre los candidatos LUT."""
    filtered = candidates
    if not config.get("show_master_or_higher", True):
        filtered = [
            candidate for candidate in filtered
            if not is_master_or_higher(candidate.get("course_level"))
        ]

    lut_period_filter = config.get("lut_period_filter")
    if lut_period_filter not in (None, "", "todos"):
        filtered = [
            candidate for candidate in filtered
            if period_matches_filter(candidate.get("periods"), lut_period_filter)
        ]

    return filtered


def deduplicate_candidates(scored: list[dict]) -> list[dict]:
    """Elimina candidatos LUT duplicados conservando la mejor puntuación."""
    unique: dict[str, dict] = {}
    for candidate in scored:
        code = candidate.get("code")
        if code is None:
            continue
        existing = unique.get(code)
        if existing is None or candidate["best_score"] > existing["best_score"]:
            unique[code] = candidate
    return sorted(unique.values(), key=lambda item: item["best_score"], reverse=True)


def load_lut_course_by_code(code: str) -> dict | None:
    """Carga un curso LUT por código desde la base de datos."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.execute(
        """
        SELECT code, name, credits_min, credits_max, course_level, periods, language,
               is_exchange, equivalent_courses, content, learning_outcomes
        FROM courses
        WHERE code = ?
        """,
        (code,),
    )
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def search_lut_courses(query: str, limit: int = 20) -> list[dict]:
    """Busca cursos LUT por codigo, nombre, contenido o learning outcomes."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    pattern = f"%{query}%"
    sql = """
        SELECT code, name, credits_min, credits_max, course_level, periods, language,
               is_exchange, equivalent_courses, content, learning_outcomes
        FROM courses
        WHERE code LIKE ?
           OR name LIKE ?
           OR content LIKE ?
           OR learning_outcomes LIKE ?
        LIMIT ?
    """
    rows = conn.execute(sql, (pattern, pattern, pattern, pattern, limit)).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_candidate_capacity(candidate: dict, lut_assignments: dict[str, list[str]], assignments: dict[str, list[dict]]) -> float:
    """Devuelve los créditos libres de un curso LUT tras asignaciones previas."""
    candidate_credits = parse_float_credits(candidate.get("credits_max", 0))
    if candidate_credits == 0.0:
        candidate_credits = parse_float_credits(candidate.get("credits_min", 0))

    used_credits = 0.0
    candidate_code = candidate.get("code", "")
    for ulpgc_code in lut_assignments.get(candidate_code, []):
        for entry in assignments.get(ulpgc_code, []):
            if entry.get("lut_code") == candidate_code:
                used_credits += parse_float_credits(entry.get("ulpgc_credits", 0))

    return max(0.0, candidate_credits - used_credits)


def find_combo_candidates(
    course: dict,
    candidates: list[dict],
    assignments: dict[str, list[dict]],
    lut_assignments: dict[str, list[str]],
    config: dict,
    max_combo: int = 2,
    limit: int = 10,
) -> list[dict]:
    """Busca combinaciones de cursos LUT que cubran un ULPGC por créditos."""
    target_credits = get_ulpgc_credits(course)
    if target_credits <= 0:
        return []

    deduped = deduplicate_candidates(candidates)
    existing_codes = {candidate["code"] for candidate in deduped if candidate.get("code")}
    for lut_code in lut_assignments:
        if lut_code in existing_codes:
            continue
        candidate = load_lut_course_by_code(lut_code)
        if not candidate:
            continue
        if get_candidate_capacity(candidate, lut_assignments, assignments) <= 0:
            continue
        deduped.append(candidate)

    deduped = filter_lut_candidates(deduped, config)
    scored_candidates = score_similarity(course, deduped)
    combo_candidates = []
    for candidate in scored_candidates:
        remaining_capacity = get_candidate_capacity(candidate, lut_assignments, assignments)
        if remaining_capacity <= 0:
            continue
        combo_candidate = {**candidate, "remaining_capacity": remaining_capacity}
        combo_candidates.append(combo_candidate)

    combo_candidates = combo_candidates[:min(20, len(combo_candidates))]
    combos = []
    for size in range(1, max_combo + 1):
        for combo in combinations(combo_candidates, size):
            total_capacity = sum(item["remaining_capacity"] for item in combo)
            if total_capacity < target_credits:
                continue
            if size > 1 and total_capacity > target_credits * 1.3:
                continue

            avg_score = sum(item["best_score"] for item in combo) / size
            closeness = 1.0 - abs(total_capacity - target_credits) / target_credits
            combos.append({
                "candidates": combo,
                "total_capacity": total_capacity,
                "avg_score": avg_score,
                "closeness": closeness,
                "overshoot": total_capacity - target_credits,
            })

    combos.sort(key=lambda item: (item["closeness"], item["avg_score"]), reverse=True)
    return combos[:limit]


def can_use_same_lut(candidate: dict, ulpgc_credits: float, lut_assignments: dict[str, list[str]], assignments: dict[str, list[dict]]) -> tuple[bool, float]:
    """Comprueba si un curso LUT tiene creditos suficientes libres para otra asignacion."""
    candidate_code = candidate.get("code")
    candidate_credits = parse_float_credits(candidate.get("credits_max", 0))
    if candidate_credits == 0.0:
        candidate_credits = parse_float_credits(candidate.get("credits_min", 0))

    assigned_courses = lut_assignments.get(candidate_code, [])
    used_credits = 0.0
    for ulpgc_code in assigned_courses:
        for assignment in assignments.get(ulpgc_code, []):
            used_credits += parse_float_credits(assignment.get("ulpgc_credits", 0))
    remaining = candidate_credits - used_credits
    return remaining >= ulpgc_credits, remaining


def unassign_course(ulpgc_code: str, assignments: dict[str, list[dict]], lut_assignments: dict[str, list[str]]) -> None:
    """Elimina todas las asignaciones ULPGC a cursos LUT (libera el ULPGC)."""
    if ulpgc_code not in assignments:
        return
    for entry in assignments[ulpgc_code]:
        lut_code = entry.get("lut_code")
        if lut_code in lut_assignments and ulpgc_code in lut_assignments[lut_code]:
            lut_assignments[lut_code].remove(ulpgc_code)
            if not lut_assignments[lut_code]:
                del lut_assignments[lut_code]
    del assignments[ulpgc_code]


def build_ram_matches(assignments: dict[str, list[dict]], courses_dict: dict[str, dict]) -> list[dict]:
    """Convierte assignments al formato esperado por generate_ram_markdown."""
    ram_matches = []
    for ulpgc_code, entries in assignments.items():
        for entry in entries:
            lut_code = entry.get("lut_code", "")
            lut_detail = load_lut_course_by_code(lut_code) or {}
            ram_matches.append({
                "ulpgc_code": ulpgc_code,
                "lut_code": lut_code,
                "lut_name": entry.get("lut_name", "N/A"),
                "assigned_ects": parse_float_credits(entry.get("ulpgc_credits", 0)),
                "lut_total_ects": parse_float_credits(entry.get("lut_credits", 0)),
                "lut_semester": lut_detail.get("periods", ""),
                "lut_content": lut_detail.get("content", ""),
                "lut_learning_outcomes": lut_detail.get("learning_outcomes", ""),
            })
    return ram_matches


def generate_ram_markdown(ram_matches: list, ulpgc_courses: list) -> str:
    """Genera el Markdown completo del RAM siguiendo el formato oficial ULPGC."""
    from itertools import groupby

    ulpgc_map = {c["code"]: c for c in ulpgc_courses}
    # Para el RAM conviene mostrar solo la base local mas defendible, no duplicar
    # contenidos y resultados. La seleccion se ha revisado caso a caso.
    preferred_ulpgc_basis = {
        "49188": "content",
        "49189": "learningOutcomes",
        "49190": "content",
        "49192": "content",
        "49193": "content",
        "49194": "learningOutcomes",
        "49195": "content",
        "49196": "content",
        "49197": "learningOutcomes",
        "49199": "learningOutcomes",
        "49200": "learningOutcomes",
        "49204": "learningOutcomes",
        "49210": "content",
    }

    mandatory = [
        m for m in ram_matches
        if ulpgc_map.get(m["ulpgc_code"], {}).get("is_mandatory", True)
    ]
    elective = [
        m for m in ram_matches
        if not ulpgc_map.get(m["ulpgc_code"], {}).get("is_mandatory", True)
    ]

    md_lines = []
    md_lines.append("# RAM 2627 - Tabla de Emparejamientos")
    md_lines.append("")
    md_lines.append("> Generado automaticamente. Revisar antes de enviar.")
    md_lines.append("")
    md_lines.append("## Tabla Resumen")
    md_lines.append("")

    def render_section(title: str, matches: list) -> str:
        if not matches:
            return ""
        section_lines = []
        section_lines.append(f"### {title}")
        section_lines.append("")

        sorted_matches = sorted(matches, key=lambda x: x["ulpgc_code"])
        for ulpgc_code, group in groupby(sorted_matches, key=lambda x: x["ulpgc_code"]):
            section_lines.append("| ULPGC | ECTS ULPGC | LUT | ECTS destino |")
            section_lines.append("|---|---:|---|---:|")
            items = list(group)
            ulpgc_info = ulpgc_map.get(ulpgc_code, {})
            ulpgc_name = ulpgc_info.get("name", "")
            ulpgc_sem = ulpgc_info.get("semester", "")
            ulpgc_ects = get_ulpgc_credits(ulpgc_info)
            ulpgc_label = f"**{ulpgc_code}** - {ulpgc_name} [{ulpgc_sem} sem]"

            for index, item in enumerate(items):
                total_lut_ects = item.get("lut_total_ects", item.get("assigned_ects"))
                assigned = item["assigned_ects"]
                if assigned == total_lut_ects:
                    ects_str = (
                        str(int(assigned))
                        if assigned == int(assigned)
                        else str(assigned)
                    )
                else:
                    total_fmt = (
                        int(total_lut_ects)
                        if total_lut_ects == int(total_lut_ects)
                        else total_lut_ects
                    )
                    ects_str = f"{assigned}/{total_fmt}"

                lut_sem = item.get("lut_semester", "")
                lut_label = (
                    f"**{item['lut_code']}** - {item['lut_name']} [{lut_sem}]"
                    if lut_sem else
                    f"**{item['lut_code']}** - {item['lut_name']}"
                )

                if index == 0:
                    section_lines.append(
                        f"| {ulpgc_label} | {ulpgc_ects} | {lut_label} | {ects_str} |"
                    )
                else:
                    section_lines.append(
                        f"|  |  | {lut_label} | {ects_str} |"
                    )

            section_lines.append("")

        section_lines.append("")
        return "\n".join(section_lines)

    md_lines.append(render_section("ASIGNATURAS OBLIGATORIAS", mandatory))
    md_lines.append(render_section("ASIGNATURAS OPTATIVAS", elective))

    md_lines.append("---")
    md_lines.append("")
    md_lines.append("## Detalle de la Comparativa")
    md_lines.append("")

    emparejamiento_num = 1
    sorted_all = sorted(ram_matches, key=lambda x: x["ulpgc_code"])
    for ulpgc_code, group in groupby(sorted_all, key=lambda x: x["ulpgc_code"]):
        items = list(group)
        ulpgc_info = ulpgc_map.get(ulpgc_code, {})
        ulpgc_name = ulpgc_info.get("name", "")
        ulpgc_content = ulpgc_info.get(
            "content", "(Contenidos no disponibles)"
        )
        ulpgc_outcomes = ulpgc_info.get(
            "learningOutcomes", "(Resultados de aprendizaje no disponibles)"
        )

        md_lines.append(f"### EMPAREJAMIENTO {emparejamiento_num}:")
        md_lines.append("")
        md_lines.append(
            f"| Nombre asignatura local: {ulpgc_name} "
            f"| Nombre asignatura destino 1: {items[0]['lut_name']} |"
        )
        md_lines.append("|---|---|")

        basis = preferred_ulpgc_basis.get(ulpgc_code, "learningOutcomes")
        if basis == "content":
            local_basis_text = ulpgc_content
        else:
            local_basis_text = ulpgc_outcomes
        local_basis = local_basis_text.replace("\n", " ").replace("|", "/")
        if len(local_basis) > 700:
            local_basis = local_basis[:700] + "..."

        for index, item in enumerate(items):
            total_lut = item.get("lut_total_ects", item["assigned_ects"])
            if item["assigned_ects"] == total_lut:
                ects_info = f"{int(total_lut)} ECTS"
            else:
                ects_info = f"{item['assigned_ects']}/{int(total_lut)} ECTS"

            if index == 0:
                right_col = (
                    f"**Codigo destino y n credits 1:** "
                    f"{item['lut_code']} ({ects_info})"
                )
            else:
                right_col = (
                    f"**Codigo destino y n credits {index + 1}:** "
                    f"{item['lut_code']} ({ects_info})"
                )

            md_lines.append(f"| {local_basis} | {right_col} |")

            lut_content = (item.get("lut_content", "") or "").replace("\n", " ").replace("|", "/")
            if len(lut_content) > 500:
                lut_content = lut_content[:500] + "..."
            md_lines.append(
                f"| {local_basis} | **Contenidos {index + 1}:** {lut_content} |"
            )

        md_lines.append("")
        emparejamiento_num += 1

    matched_codes = {m["ulpgc_code"] for m in ram_matches}
    pending = [c for c in ulpgc_courses if c["code"] not in matched_codes]
    if pending:
        md_lines.append("---")
        md_lines.append("")
        md_lines.append("## Asignaturas no emparejadas")
        md_lines.append("")
        for course in pending:
            md_lines.append(f"- **{course['code']}** - {course['name']} ({course['ects']} ECTS)")
        md_lines.append("")

    return "\n".join(md_lines)


def export_ram_markdown(assignments: dict[str, list[dict]], courses_dict: dict[str, dict], ulpgc_courses: list[dict], output_file: str = "RAM_emparejamientos.md") -> str | None:
    """Exporta el RAM en Markdown y devuelve la ruta si tiene exito."""
    if not assignments:
        return None

    ram_matches = build_ram_matches(assignments, courses_dict)
    markdown = generate_ram_markdown(ram_matches, ulpgc_courses)
    with open(output_file, "w", encoding="utf-8") as file:
        file.write(markdown)
    return output_file


def save_assignments_to_json(assignments: dict[str, list[dict]], courses_dict: dict[str, dict], output_file: str = "emparejamientos.json") -> bool:
    """Exporta las asignaciones actuales a un archivo JSON."""
    try:
        output_data = {
            "total_ulpgc_assigned": len(assignments),
            "assignments": [],
        }

        for ulpgc_code, entries in assignments.items():
            course = courses_dict.get(ulpgc_code, {})
            assignment_entry = {
                "ulpgc_code": ulpgc_code,
                "ulpgc_name": course.get("name", "N/A"),
                "ulpgc_credits": get_ulpgc_credits(course),
                "ulpgc_type": course.get("type", "N/A"),
                "lut_courses": [
                    {
                        "lut_code": entry.get("lut_code", "N/A"),
                        "lut_name": entry.get("lut_name", "N/A"),
                        "ulpgc_credits_assigned": entry.get("ulpgc_credits", "N/A"),
                        "lut_credits_max": entry.get("lut_credits", "N/A"),
                    }
                    for entry in entries
                ],
            }
            output_data["assignments"].append(assignment_entry)

        with open(output_file, "w", encoding="utf-8") as file:
            json.dump(output_data, file, indent=2, ensure_ascii=False)
        return True
    except Exception:
        return False


def load_assignments_from_json(path: str | Path = "emparejamientos.json") -> dict[str, list[dict]]:
    """Carga asignaciones desde JSON si existe."""
    json_path = Path(path)
    if not json_path.exists():
        return {}
    with open(json_path, encoding="utf-8") as file:
        data = json.load(file)

    assignments: dict[str, list[dict]] = {}
    for assignment in data.get("assignments", []):
        ulpgc_code = assignment.get("ulpgc_code")
        if not ulpgc_code:
            continue
        entries = []
        for lut_course in assignment.get("lut_courses", []):
            entries.append({
                "lut_code": lut_course.get("lut_code", "N/A"),
                "lut_name": lut_course.get("lut_name", "N/A"),
                "ulpgc_credits": parse_float_credits(lut_course.get("ulpgc_credits_assigned", 0)),
                "lut_credits": parse_float_credits(lut_course.get("lut_credits_max", 0)),
            })
        assignments[ulpgc_code] = entries
    return assignments


def build_lut_assignments(assignments: dict[str, list[dict]]) -> dict[str, list[str]]:
    """Construye el índice inverso LUT -> ULPGC a partir de assignments."""
    lut_assignments: dict[str, list[str]] = {}
    for ulpgc_code, entries in assignments.items():
        for entry in entries:
            lut_code = entry.get("lut_code")
            if not lut_code:
                continue
            lut_assignments.setdefault(lut_code, []).append(ulpgc_code)
    return lut_assignments


def assign_candidate_non_interactive(
    course: dict,
    candidate: dict,
    assignments: dict[str, list[dict]],
    lut_assignments: dict[str, list[str]],
    append: bool = True,
) -> tuple[bool, str]:
    """Asigna un candidato sin interacción y devuelve estado legible."""
    ulpgc_credits = get_ulpgc_credits(course)
    candidate_credits = parse_float_credits(candidate.get("credits_max", 0))
    if candidate_credits == 0.0:
        candidate_credits = parse_float_credits(candidate.get("credits_min", 0))

    can_assign, remaining = can_use_same_lut(candidate, ulpgc_credits, lut_assignments, assignments)
    if not can_assign:
        return False, f"Capacidad insuficiente en {candidate.get('code')} ({remaining:.1f} ECTS libres)"

    ulpgc_code = course.get("code")
    if not append and ulpgc_code in assignments:
        for prev in assignments.get(ulpgc_code, []):
            prev_lut = prev.get("lut_code")
            if prev_lut in lut_assignments and ulpgc_code in lut_assignments[prev_lut]:
                lut_assignments[prev_lut].remove(ulpgc_code)
                if not lut_assignments[prev_lut]:
                    del lut_assignments[prev_lut]
        assignments[ulpgc_code] = []

    entry = {
        "lut_code": candidate.get("code", "N/A"),
        "lut_name": candidate.get("name", "N/A"),
        "ulpgc_credits": ulpgc_credits,
        "lut_credits": candidate_credits,
    }
    assignments.setdefault(ulpgc_code, []).append(entry)
    lut_assignments.setdefault(candidate.get("code", ""), []).append(ulpgc_code)
    return True, "ok"
