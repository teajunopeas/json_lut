#!/usr/bin/env python3
"""Matcher interactivo para buscar equivalencias ULPGC -> LUT.

El flujo combina tres pasos:
1. Carga asignaturas ULPGC y keywords desde `ulpgc_courses.json`.
2. Preselecciona cursos LUT con SQLite FTS5 usando esas keywords en ingles.
3. Reordena candidatos con embeddings semanticos de SentenceTransformers.

La tabla muestra similitud por contenido, resultados de aprendizaje y texto
combinado. El criterio del 75% se usa como umbral orientativo, no como
aprobacion automatica.
"""

import json
import os
import sqlite3
from itertools import combinations
from pathlib import Path

from rich.console import Console
from rich.table import Table
from sentence_transformers import SentenceTransformer, util

console = Console()
DB_PATH = Path("lut_courses.db")
ULPGC_PATH = Path("ulpgc_courses.json")
MODEL_NAME = "all-MiniLM-L6-v2"
MODEL_CACHE_DIR = Path(".cache")
MATCH_THRESHOLD = 75.0
SEARCH_LIMIT = 40
RESULT_LIMIT = 10

os.environ.setdefault("TRANSFORMERS_CACHE", str(MODEL_CACHE_DIR))
console.print(
    f"[cyan]Cargando modelo de embeddings ({MODEL_NAME}) desde caché local {MODEL_CACHE_DIR}...[/cyan]"
)
model = SentenceTransformer(MODEL_NAME, cache_folder=str(MODEL_CACHE_DIR))


def load_ulpgc_courses(path: Path = ULPGC_PATH) -> list[dict]:
    """Carga asignaturas ULPGC y comprueba que todas tengan keywords."""
    with open(path, encoding="utf-8") as file:
        courses = json.load(file)

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
        SELECT code, name, credits_min, credits_max, course_level, periods, content, learning_outcomes
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
    ulpgc_content = prepare_text(course.get("content", ""), "", course.get("name", ""))
    ulpgc_outcomes = prepare_text("", course.get("learningOutcomes", ""), course.get("name", ""))
    ulpgc_combined = prepare_text(
        course.get("content", ""),
        course.get("learningOutcomes", ""),
        course.get("name", ""),
    )

    scored = []
    for candidate in candidates:
        lut_content = prepare_text(candidate["content"], "", candidate.get("name", ""))
        lut_outcomes = prepare_text("", candidate["learning_outcomes"], candidate.get("name", ""))
        lut_combined = prepare_text(
            candidate["content"],
            candidate["learning_outcomes"],
            candidate.get("name", ""),
        )

        content_score = similarity_percent(ulpgc_content, lut_content)
        outcomes_score = similarity_percent(ulpgc_outcomes, lut_outcomes)
        combined_score = similarity_percent(ulpgc_combined, lut_combined)
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


def render_results(scored: list[dict]) -> None:
    """Muestra los candidatos con desglose de similitud por criterio."""
    table = Table(show_lines=True)
    table.add_column("Mejor", justify="center", style="bold cyan", width=8)
    table.add_column("Cont.", justify="center", width=8)
    table.add_column("Res.", justify="center", width=8)
    table.add_column("Comb.", justify="center", width=8)
    table.add_column("Codigo", style="green", width=12)
    table.add_column("Nombre", style="white", width=38)
    table.add_column("ECTS", justify="center", width=6)
    table.add_column("Nivel", style="magenta", width=12)

    for result in scored[:RESULT_LIMIT]:
        score = result["best_score"]
        style = "bold green" if result["meets_threshold"] else "bold yellow" if score >= 60 else "dim"

        table.add_row(
            f"[{style}]{score}%[/{style}]",
            f"{result['content_score']}%",
            f"{result['outcomes_score']}%",
            f"{result['combined_score']}%",
            result["code"],
            result["name"][:37],
            f"{result['credits_min']}-{result['credits_max']}",
            result["course_level"] or "N/A",
        )

    console.print(table)

def prompt_yes_no(message: str, default: bool = True) -> bool:
    """Solicita una respuesta si/no al usuario."""
    yes = {"s", "si", "y", "yes", "1"}
    no = {"n", "no", "0"}

    while True:
        answer = input(f"{message} [{'S/n' if default else 's/N'}]: ").strip().lower()
        if answer == "":
            return default
        if answer in yes:
            return True
        if answer in no:
            return False
        console.print("[red]Respuesta no valida. Usa 's' o 'n'.[/red]")


def show_candidate_details(candidate: dict) -> None:
    """Muestra contenido, resultados y JSON del candidato elegido."""
    console.print(f"\n[bold cyan]Detalles del candidato {candidate['code']}[/bold cyan]")
    console.print(f"[bold]Nombre LUT:[/bold] {candidate.get('name', 'N/A')}")
    console.print(f"[bold]ECTS LUT:[/bold] {candidate.get('credits_min', 'N/A')} - {candidate.get('credits_max', 'N/A')}")
    console.print(f"[bold]Nivel LUT:[/bold] {candidate.get('course_level', 'N/A')}\n")

    console.print("[bold]Contenido LUT:[/bold]")
    console.print(candidate.get('content', '(sin contenido)'), overflow='fold')
    console.print("\n[bold]Resultados de aprendizaje LUT:[/bold]")
    console.print(candidate.get('learning_outcomes', '(sin learning_outcomes)'), overflow='fold')
    console.print("\n[bold]JSON completo del candidato:[/bold]")
    console.print_json(data=candidate)
    console.print()


def review_candidates(scored: list[dict]) -> dict | None:
    """Permite seleccionar un candidato y explorar su JSON antes de decidir."""
    if not scored:
        return None

    while True:
        prompt = (
            f"Selecciona candidato (1-{min(RESULT_LIMIT, len(scored))}) para ver detalles, "
            "'j' + numero para JSON bruto, o 's' para saltar: "
        )
        choice = input(prompt).strip().lower()
        if choice == "s":
            return None
        if choice.startswith("j"):
            selection = choice[1:].strip()
            try:
                index = int(selection) - 1
                if index < 0 or index >= min(RESULT_LIMIT, len(scored)):
                    console.print("[red]Numero fuera de rango para JSON.[/red]")
                    continue
            except ValueError:
                console.print("[red]Entrada invalida para JSON.[/red]")
                continue
            console.print_json(data=scored[index])
            continue

        if choice == "c":
            return "combo"

        try:
            index = int(choice) - 1
            if index < 0 or index >= min(RESULT_LIMIT, len(scored)):
                console.print("[red]Numero fuera de rango.[/red]")
                continue
        except ValueError:
            console.print("[red]Entrada invalida.[/red]")
            continue

        candidate = scored[index]
        show_candidate_details(candidate)
        if prompt_yes_no("¿Incluir este candidato en tu seleccion?", default=False):
            return candidate
        console.print("[yellow]Candidato descartado. Sigue revisando otros candidatos o usa 's' para saltar.[/yellow]\n")


def parse_float_credits(value: str | int | float) -> float:
    """Normaliza un valor de creditos a float."""
    if value is None:
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    try:
        text = str(value).replace(',', '.').strip()
        return float(text)
    except ValueError:
        return 0.0


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
        SELECT code, name, credits_min, credits_max, course_level, periods, content, learning_outcomes
        FROM courses
        WHERE code = ?
        """,
        (code,),
    )
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


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


def find_combo_candidates(course: dict, candidates: list[dict], assignments: dict[str, list[dict]], lut_assignments: dict[str, list[str]], max_combo: int = 2, limit: int = 10) -> list[dict]:
    """Busca combinaciones de cursos LUT que cubran un ULPGC por créditos."""
    target_credits = parse_float_credits(course.get("credits", "0"))
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

    scored_candidates = score_similarity(course, deduped)
    combo_candidates = []
    for candidate in scored_candidates:
        remaining_capacity = get_candidate_capacity(candidate, lut_assignments, assignments)
        if remaining_capacity <= 0:
            continue
        candidate["remaining_capacity"] = remaining_capacity
        combo_candidates.append(candidate)

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


def render_combo_results(combos: list[dict]) -> None:
    """Muestra combinaciones de cursos LUT en una tabla."""
    if not combos:
        console.print("[yellow]No se encontraron combinaciones adecuadas.[/yellow]")
        return

    table = Table(show_lines=True)
    table.add_column("#", justify="right", width=4)
    table.add_column("ECTS tot.", justify="center", width=8)
    table.add_column("Score", justify="center", width=8)
    table.add_column("Ajuste", justify="center", width=8)
    table.add_column("Códigos LUT", style="green", width=24)
    table.add_column("Nombres", style="white", width=42)

    for index, combo in enumerate(combos, start=1):
        codes = ", ".join(item["code"] for item in combo["candidates"])
        names = " + ".join(item["name"][:18] for item in combo["candidates"])
        table.add_row(
            str(index),
            f"{combo['total_capacity']:.1f}",
            f"{combo['avg_score']:.1f}%",
            f"{combo['closeness']:.2f}",
            codes,
            names,
        )

    console.print(table)


def review_combo_candidates(combos: list[dict], course: dict) -> dict | None:
    """Permite elegir una combinacion de cursos LUT para asignar."""
    if not combos:
        return None

    while True:
        render_combo_results(combos)
        choice = input(
            f"Selecciona combinacion (1-{len(combos)}) para ver detalles, 's' para saltar: "
        ).strip().lower()
        if choice == "s":
            return None

        try:
            index = int(choice) - 1
            if index < 0 or index >= len(combos):
                console.print("[red]Numero fuera de rango.[/red]")
                continue
        except ValueError:
            console.print("[red]Entrada invalida.[/red]")
            continue

        combo = combos[index]
        console.print(f"\n[bold cyan]Detalles de la combinacion seleccionada[/bold cyan]")
        for item in combo["candidates"]:
            console.print(f"- {item['code']} | {item['name']} | {item['remaining_capacity']:.1f} ECTS restantes | {item['best_score']:.1f}%")
        console.print(f"\n[bold]Total capacidad:[/bold] {combo['total_capacity']:.1f} ECTS")
        console.print(f"[bold]Ajuste al objetivo:[/bold] {combo['closeness']:.2f}")

        if prompt_yes_no("¿Asignar esta combinacion al curso ULPGC?", default=False):
            return combo
        console.print("[yellow]Combinacion descartada. Puedes elegir otra o saltar.[/yellow]\n")


def assign_combo(course: dict, combo: dict, assignments: dict[str, list[dict]], lut_assignments: dict[str, list[str]]) -> bool:
    """Asigna varios cursos LUT a un curso ULPGC de una sola vez."""
    if not combo or not combo.get("candidates"):
        return False

    success = True
    for candidate in combo["candidates"]:
        if not assign_candidate(course, candidate, assignments, lut_assignments):
            success = False
    return success


def can_use_same_lut(candidate: dict, ulpgc_credits: float, lut_assignments: dict[str, list[str]], assignments: dict[str, list[dict]]) -> tuple[bool, float]:
    """Comprueba si un curso LUT tiene creditos suficientes libres para otra asignacion."""
    candidate_code = candidate.get("code")
    candidate_credits = parse_float_credits(candidate.get("credits_max", 0))
    if candidate_credits == 0.0:
        candidate_credits = parse_float_credits(candidate.get("credits_min", 0))

    assigned_courses = lut_assignments.get(candidate_code, [])
    used_credits = 0.0
    for ulpgc_code in assigned_courses:
        for a in assignments.get(ulpgc_code, []):
            used_credits += parse_float_credits(a.get("ulpgc_credits", 0))
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


def render_course_list(courses: list[dict], assignments: dict[str, list[dict]], config: dict) -> None:
    """Muestra una tabla con los cursos ULPGC disponibles y su estado de asignacion."""
    table = Table(show_lines=False)
    table.add_column("#", justify="right", width=4)
    table.add_column("Codigo", style="green", width=12)
    table.add_column("Nombre", style="white", width=40)
    table.add_column("Tipo", style="yellow", width=12)
    table.add_column("ECTS", justify="center", width=6)
    table.add_column("Asignado a", style="cyan", width=18)

    visible = [course for course in courses if course.get("type") != "optativa" or config["show_optatives"]]
    for index, course in enumerate(visible, start=1):
        code = course.get("code", "N/A")
        status = assignments.get(code)
        assigned = ", ".join([s.get("lut_code", "") for s in status]) if status else "-"
        table.add_row(
            str(index),
            code,
            course.get("name", "N/A")[:38],
            course.get("type", "N/A"),
            str(course.get("credits", "N/A")),
            assigned,
        )

    console.print(table)


def assign_candidate(course: dict, candidate: dict, assignments: dict[str, list[dict]], lut_assignments: dict[str, list[str]]) -> bool:
    """Asigna el candidato seleccionado y actualiza los registros de LUT.

    Permite añadir la asignación además de otras existentes o reemplazarlas.
    """
    ulpgc_credits = parse_float_credits(course.get("credits", "0"))
    candidate_credits = parse_float_credits(candidate.get("credits_max", 0))
    if candidate_credits == 0.0:
        candidate_credits = parse_float_credits(candidate.get("credits_min", 0))

    can_assign, remaining = can_use_same_lut(candidate, ulpgc_credits, lut_assignments, assignments)
    if not can_assign and candidate.get("code") in lut_assignments:
        assigned = lut_assignments.get(candidate.get("code"), [])
        console.print(
            f"[yellow]Aviso:[/yellow] El curso LUT ya está asignado a {len(assigned)} ULPGC(s), "
            f"con {remaining:.1f} ECTS sobrantes.\n"
        )
        if remaining <= 0 and prompt_yes_no("¿Deseas liberar una asignación previa para revisarla?", default=False):
            previous_course = assigned[0]
            unassign_course(previous_course, assignments, lut_assignments)
            console.print(f"[green]Se ha liberado el curso {previous_course} para su revisión.[/green]\n")
            return False

    ulpgc_code = course.get("code")
    append = prompt_yes_no("¿Añadir esta asignación además de las existentes?", default=True)
    if not append and ulpgc_code in assignments:
        # eliminar asignaciones previas para este ULPGC
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
    console.print(f"[green]Asignado {candidate.get('code', 'N/A')} a {ulpgc_code}.[/green]\n")
    return True


def search_and_review_course(course: dict, assignments: dict[str, list[dict]], lut_assignments: dict[str, list[str]], config: dict) -> None:
    """Busca y revisa candidatos para una asignatura ULPGC."""
    console.print(f"\n[bold cyan]Buscando equivalencias para {course.get('name', 'N/A')} ({course.get('code', 'N/A')})[/bold cyan]")
    console.print(f"[yellow]Keywords usadas: {', '.join(course.get('keywords', []))}[/yellow]\n")

    results = search_keywords(course.get("keywords", []))
    if not results:
        console.print("[red]No se encontraron candidatos para esta asignatura.[/red]\n")
        return

    scored = score_similarity(course, results)
    deduped = deduplicate_candidates(scored)
    if len(deduped) < len(scored):
        console.print(f"[dim]Se han eliminado {len(scored) - len(deduped)} coincidencias duplicadas.[/dim]\n")

    render_results(deduped)
    console.print("[dim]Pulsa 'c' para buscar combinaciones de cursos LUT si necesitas cubrir esta asignatura con varios cursos.[/dim]\n")
    selection = review_candidates(deduped)
    if selection == "combo":
        combos = find_combo_candidates(course, deduped, assignments, lut_assignments, max_combo=2)
        combo = review_combo_candidates(combos, course)
        if combo is None:
            console.print("[yellow]No se seleccionó ninguna combinación.[/yellow]\n")
            return
        if not assign_combo(course, combo, assignments, lut_assignments):
            console.print("[yellow]No se guardó la combinación seleccionada.[/yellow]\n")
        return

    if selection is None:
        console.print("[yellow]No se realizó ninguna asignación.[/yellow]\n")
        return

    if not assign_candidate(course, selection, assignments, lut_assignments):
        console.print("[yellow]No se guardó la asignación. Puedes revisar otro candidato más tarde.[/yellow]\n")


def select_course_by_input(courses: list[dict], assignments: dict[str, list[dict]], config: dict) -> dict | None:
    """Selecciona una asignatura ULPGC desde la lista filtrada."""
    visible = [course for course in courses if course.get("type") != "optativa" or config["show_optatives"]]
    if not visible:
        console.print("[red]No hay cursos disponibles con la configuración actual.[/red]")
        return None

    render_course_list(courses, assignments, config)
    choice = input("Selecciona número de curso o código ULPGC: ").strip()
    if not choice:
        return None

    if choice.isdigit():
        idx = int(choice) - 1
        if 0 <= idx < len(visible):
            return visible[idx]
        console.print("[red]Número fuera de rango.[/red]")
        return None

    course = next((course for course in visible if course.get("code") == choice), None)
    if not course:
        console.print("[red]Curso no encontrado.[/red]")
    return course


def show_assignment_summary(assignments: dict[str, list[dict]], courses: dict[str, dict]) -> None:
    """Imprime un resumen de las asignaciones ULPGC -> LUT actuales (soporta multiples)."""
    if not assignments:
        console.print("[yellow]No hay asignaciones registradas.[/yellow]")
        return

    table = Table(show_lines=True)
    table.add_column("ULPGC", style="green", width=12)
    table.add_column("Asignatura ULPGC", style="white", width=40)
    table.add_column("LUT", style="cyan", width=12)
    table.add_column("Asignatura LUT", style="white", width=40)
    table.add_column("ECTS ULPGC", justify="center", width=10)
    table.add_column("ECTS LUT", justify="center", width=10)

    for ulpgc_code, entries in assignments.items():
        course = courses.get(ulpgc_code, {})
        for i, entry in enumerate(entries):
            table.add_row(
                ulpgc_code if i == 0 else "",
                course.get("name", "N/A")[:38] if i == 0 else "",
                entry.get("lut_code", "N/A"),
                entry.get("lut_name", "N/A")[:38],
                f"{entry.get('ulpgc_credits', '')}",
                f"{entry.get('lut_credits', '')}",
            )

    console.print(table)


def compare_courses_detailed(ulpgc_course: dict, lut_course: dict) -> None:
    """Compara el contenido detallado de un curso ULPGC vs uno o varios LUT.
    
    Muestra:
    - Descripción de contenido
    - Resultados de aprendizaje
    - Temas cubiertos vs no cubiertos (análisis cualitativo)
    """
    console.print(f"\n[bold cyan]COMPARACIÓN DE CONTENIDO[/bold cyan]")
    console.print(f"[bold green]ULPGC:[/bold green] {ulpgc_course.get('code')} | {ulpgc_course.get('name')}")
    console.print(f"[bold cyan]LUT:[/bold cyan]   {lut_course.get('code')} | {lut_course.get('name')}\n")

    console.print("[bold]Contenido ULPGC:[/bold]")
    console.print(ulpgc_course.get('description', '(sin descripción)') or '(sin descripción)', overflow='fold')

    console.print("\n[bold]Contenido LUT:[/bold]")
    console.print(lut_course.get('content', '(sin contenido)') or '(sin contenido)', overflow='fold')

    console.print("\n[bold]Resultados de Aprendizaje ULPGC:[/bold]")
    console.print(ulpgc_course.get('learning_outcomes', '(sin información)') or '(sin información)', overflow='fold')

    console.print("\n[bold]Resultados de Aprendizaje LUT:[/bold]")
    console.print(lut_course.get('learning_outcomes', '(sin información)') or '(sin información)', overflow='fold')

    console.print("\n[yellow]Nota: Revisa manualmente si la cobertura es suficiente para tu plan de movilidad.[/yellow]\n")


def save_assignments_to_json(assignments: dict[str, list[dict]], courses_dict: dict[str, dict], output_file: str = "emparejamientos.json") -> bool:
    """Exporta las asignaciones actuales a un archivo JSON."""
    try:
        output_data = {
            "total_ulpgc_assigned": len(assignments),
            "assignments": []
        }
        
        for ulpgc_code, entries in assignments.items():
            course = courses_dict.get(ulpgc_code, {})
            assignment_entry = {
                "ulpgc_code": ulpgc_code,
                "ulpgc_name": course.get("name", "N/A"),
                "ulpgc_credits": course.get("credits", "N/A"),
                "ulpgc_type": course.get("type", "N/A"),
                "lut_courses": [
                    {
                        "lut_code": entry.get("lut_code", "N/A"),
                        "lut_name": entry.get("lut_name", "N/A"),
                        "ulpgc_credits_assigned": entry.get("ulpgc_credits", "N/A"),
                        "lut_credits_max": entry.get("lut_credits", "N/A"),
                    }
                    for entry in entries
                ]
            }
            output_data["assignments"].append(assignment_entry)
        
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        console.print(f"[green]✓ Asignaciones guardadas en {output_file}[/green]")
        return True
    except Exception as e:
        console.print(f"[red]✗ Error al guardar: {e}[/red]")
        return False


def show_lut_capacity_status(assignments: dict[str, list[dict]]) -> None:
    """Muestra un resumen de la capacidad disponible en cada curso LUT asignado."""
    if not assignments:
        console.print("[yellow]No hay asignaciones registradas.[/yellow]")
        return

    console.print("\n[bold cyan]ESTADO DE CAPACIDAD EN CURSOS LUT[/bold cyan]\n")
    
    lut_usage: dict[str, dict] = {}
    for ulpgc_code, entries in assignments.items():
        for entry in entries:
            lut_code = entry.get("lut_code", "")
            ulpgc_credits = parse_float_credits(entry.get("ulpgc_credits", 0))
            lut_credits = parse_float_credits(entry.get("lut_credits", 0))
            
            if lut_code not in lut_usage:
                lut_usage[lut_code] = {
                    "name": entry.get("lut_name", "N/A"),
                    "max_credits": lut_credits,
                    "used_credits": 0.0,
                    "ulpgc_count": 0,
                }
            lut_usage[lut_code]["used_credits"] += ulpgc_credits
            lut_usage[lut_code]["ulpgc_count"] += 1

    table = Table(show_lines=True)
    table.add_column("Código LUT", style="cyan", width=12)
    table.add_column("Nombre LUT", style="white", width=40)
    table.add_column("ECTS Máx", justify="center", width=10)
    table.add_column("ECTS Usados", justify="center", width=10)
    table.add_column("ECTS Libres", justify="center", width=10)
    table.add_column("% Uso", justify="center", width=8)
    table.add_column("ULPGC asig.", justify="center", width=10)

    for lut_code, info in sorted(lut_usage.items()):
        used = info["used_credits"]
        max_c = info["max_credits"]
        free = max(0.0, max_c - used)
        pct = round((used / max_c * 100) if max_c > 0 else 0, 1)
        
        style = "red" if pct >= 100 else "yellow" if pct >= 80 else "green"
        table.add_row(
            lut_code,
            info["name"][:38],
            f"{max_c:.1f}",
            f"{used:.1f}",
            f"[{style}]{free:.1f}[/{style}]",
            f"[{style}]{pct}%[/{style}]",
            str(info["ulpgc_count"]),
        )

    console.print(table)


def main() -> None:
    """Bucle principal del matcher interactivo."""
    ulpgc_data = load_ulpgc_courses()
    courses_dict = {course["code"]: course for course in ulpgc_data}
    assignments: dict[str, list[dict]] = {}
    lut_assignments: dict[str, list[str]] = {}
    config = {"show_optatives": False}

    # Mostrar explicación de funcionalidades al arrancar
    console.print("\n[bold cyan]BIENVENIDO AL MATCHER ULPGC ↔ LUT[/bold cyan]\n")
    console.print("[dim]Este programa te ayuda a encontrar equivalencias entre cursos ULPGC y cursos LUT.\n[/dim]")
    console.print("[bold]Opciones principales del menú:[/bold]")
    console.print("  1. [bold]Seleccionar asignatura[/bold] → Busca equivalencias para un curso ULPGC")
    console.print("  2. [bold]Ver emparejamientos[/bold] → Muestra todas las asignaciones actuales")
    console.print("  3. [bold]Estado de capacidad[/bold] → Ver cuántos créditos quedan disponibles en cada LUT")
    console.print("  4. [bold]Procesar obligatorias[/bold] → Busca automáticamente equivalencias para todas las obligatorias sin asignar")
    console.print("  5. [bold]Revisar todo[/bold] → Revisa todas las asignaturas no asignadas")
    console.print("  6. [bold]Guardar resultados[/bold] → Exporta tus emparejamientos a un archivo JSON")
    console.print("  7. [bold]Configuración[/bold] → Activa/desactiva mostrar asignaturas optativas")
    console.print("  q. [bold]Salir[/bold] → Termina el programa\n")
    console.print("[yellow]💡 Dentro de cada búsqueda, presiona 'c' para ver combinaciones de múltiples cursos LUT.\n[/yellow]")

    while True:
        console.print("\n[bold cyan]═══════════ MENÚ PRINCIPAL ═══════════[/bold cyan]")
        console.print("  1. Seleccionar asignatura")
        console.print("  2. Ver emparejamientos actuales")
        console.print("  3. Estado de capacidad en cursos LUT")
        console.print("  4. Procesar obligatorias sin asignar")
        console.print("  5. Revisar todas las sin asignar")
        console.print("  6. Guardar resultados (JSON)")
        console.print("  7. Configuración")
        console.print("  q. Salir\n")

        choice = input("Selecciona opción (1-7, q): ").strip().lower()
        if choice == "q":
            console.print("[cyan]¡Hasta luego![/cyan]\n")
            break

        if choice == "1":
            course = select_course_by_input(ulpgc_data, assignments, config)
            if not course:
                continue
            if course.get("type") == "optativa" and not config["show_optatives"]:
                if not prompt_yes_no("Esta asignatura es optativa. ¿Deseas continuar?", default=False):
                    continue
            search_and_review_course(course, assignments, lut_assignments, config)
        elif choice == "2":
            show_assignment_summary(assignments, courses_dict)
        elif choice == "3":
            show_lut_capacity_status(assignments)
        elif choice == "4":
            console.print("[cyan]Procesando asignaturas obligatorias sin asignar...[/cyan]\n")
            processed = 0
            for course in ulpgc_data:
                if course.get("type") != "obligatoria":
                    continue
                if course["code"] in assignments:
                    continue
                processed += 1
                console.print(f"[dim][{processed}][/dim] ", end="")
                search_and_review_course(course, assignments, lut_assignments, config)
            console.print(f"[green]Procesadas {processed} asignaturas.[/green]")
        elif choice == "5":
            console.print("[cyan]Revisando todas las asignaturas sin asignar...[/cyan]\n")
            processed = 0
            for course in ulpgc_data:
                if course["code"] in assignments:
                    continue
                if course.get("type") == "optativa" and not config["show_optatives"]:
                    continue
                processed += 1
                console.print(f"[dim][{processed}][/dim] ", end="")
                search_and_review_course(course, assignments, lut_assignments, config)
            console.print(f"[green]Revisadas {processed} asignaturas.[/green]")
        elif choice == "6":
            if assignments:
                save_assignments_to_json(assignments, courses_dict)
            else:
                console.print("[yellow]No hay asignaciones para guardar.[/yellow]")
        elif choice == "7":
            console.print("\n[bold cyan]CONFIGURACIÓN[/bold cyan]\n")
            config["show_optatives"] = prompt_yes_no(
                f"Mostrar asignaturas optativas [{'sí' if config['show_optatives'] else 'no'}]?", default=config["show_optatives"]
            )
        else:
            console.print("[red]❌ Opción no reconocida. Intenta de nuevo.[/red]")


if __name__ == "__main__":
    main()
