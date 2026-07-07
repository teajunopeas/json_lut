#!/usr/bin/env python3
"""Interfaz interactiva para el matcher ULPGC -> LUT.

La logica pura vive en `matcher_core.py`. Este archivo se centra en:
- presentacion con Rich,
- preguntas interactivas,
- flujo de menu para revision humana,
- un pequeno modo CLI no interactivo para automatizaciones simples.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from rich.columns import Columns
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from matcher_core import (
    MODEL_NAME,
    MORE_RESULTS_STEP,
    RESULT_LIMIT,
    assign_candidate_non_interactive,
    build_lut_assignments,
    can_use_same_lut,
    course_matches_filters,
    deduplicate_candidates,
    export_ram_markdown,
    filter_lut_candidates,
    find_combo_candidates,
    get_model,
    get_ulpgc_credits,
    load_lut_course_by_code,
    load_assignments_from_json,
    load_ulpgc_courses,
    lut_level_filter_label,
    lut_period_filter_label,
    parse_float_credits,
    parse_period_filter,
    parse_semester_filter,
    save_assignments_to_json,
    score_similarity,
    search_keywords,
    search_lut_courses,
    semester_filter_label,
    unassign_course,
    validate_assignments,
)

console = Console()


def ensure_model_loaded() -> None:
    """Carga el modelo de embeddings y muestra mensajes utiles al usuario."""
    console.print(f"[cyan]Cargando modelo de embeddings ({MODEL_NAME})...[/cyan]")
    if not Path("models/all-MiniLM-L6-v2").exists():
        console.print("[yellow]Modelo local no encontrado. Descargando...[/yellow]")
    get_model()
    if Path("models/all-MiniLM-L6-v2").exists():
        console.print("[green]Modelo listo.[/green]")


def render_results(scored: list[dict], limit: int = RESULT_LIMIT) -> None:
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

    for result in scored[:limit]:
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
    if limit < len(scored):
        console.print(
            f"[dim]Mostrando {min(limit, len(scored))} de {len(scored)} candidatos. "
            "Pulsa 'm' para ver más.[/dim]"
        )


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


def build_ulpgc_panel(ulpgc_course: dict) -> Panel:
    """Construye el panel de referencia ULPGC para reutilizarlo sin duplicarlo."""
    ulpgc_credits = get_ulpgc_credits(ulpgc_course)
    ulpgc_body_lines = [
        f"[bold]Nombre:[/bold] {ulpgc_course.get('name', 'N/A')}",
        f"[bold]ECTS:[/bold] {ulpgc_credits}",
        "",
        "[bold]Contenido:[/bold]",
        str(ulpgc_course.get("content", "(sin contenido)") or "(sin contenido)"),
        "",
        "[bold]Resultados de aprendizaje:[/bold]",
        str(ulpgc_course.get("learningOutcomes", "(sin información)") or "(sin información)"),
    ]
    return Panel(
        "\n".join(ulpgc_body_lines),
        title=f"[bold green]ULPGC {ulpgc_course.get('code', 'N/A')}[/bold green]",
        border_style="green",
    )


def build_lut_panel(lut_course: dict) -> Panel:
    """Construye el panel detallado del candidato LUT."""
    lut_credits_min = lut_course.get("credits_min", "N/A")
    lut_credits_max = lut_course.get("credits_max", "N/A")
    lut_periods = lut_course.get("periods", "N/A") or "N/A"
    lut_body_lines = [
        f"[bold]Nombre:[/bold] {lut_course.get('name', 'N/A')}",
        f"[bold]ECTS:[/bold] {lut_credits_min}-{lut_credits_max}",
        f"[bold]Periodo:[/bold] {lut_periods}",
        "",
        "[bold]Contenido:[/bold]",
        str(lut_course.get("content", "(sin contenido)") or "(sin contenido)"),
        "",
        "[bold]Resultados de aprendizaje:[/bold]",
        str(lut_course.get("learning_outcomes", "(sin información)") or "(sin información)"),
    ]
    return Panel(
        "\n".join(lut_body_lines),
        title=f"[bold cyan]LUT {lut_course.get('code', 'N/A')}[/bold cyan]",
        border_style="cyan",
    )


def show_comparison(ulpgc_course: dict, lut_course: dict, include_ulpgc: bool = True) -> None:
    """Muestra la referencia ULPGC una vez y el detalle LUT cuando corresponda."""
    if include_ulpgc:
        console.print(Columns([build_ulpgc_panel(ulpgc_course), build_lut_panel(lut_course)], equal=True, expand=True))
    else:
        console.print(build_lut_panel(lut_course))


def show_multi_coverage(course: dict, candidates: list[dict]) -> float:
    """Muestra la cobertura ECTS acumulada de varios candidatos LUT frente al objetivo ULPGC."""
    target = get_ulpgc_credits(course)
    console.print(f"\n[bold]ULPGC:[/bold] {course.get('name', 'N/A')} ([bold]{target}[/bold] ECTS objetivo)")
    console.print("[bold]LUT seleccionados:[/bold]")

    total = 0.0
    for candidate in candidates:
        ects = parse_float_credits(candidate.get("credits_max", 0)) or parse_float_credits(candidate.get("credits_min", 0))
        total += ects
        console.print(f"  - {candidate.get('code', 'N/A')} | {candidate.get('name', 'N/A')} ({ects} ECTS)")

    coverage_icon = "[bold green]✓[/bold green]" if total >= target else "[bold yellow]⚠[/bold yellow]"
    console.print(f"\n{coverage_icon} [bold]ECTS LUT acumulados:[/bold] {total} / {target}\n")
    return total


def search_manual_lut_course(course: dict, config: dict) -> dict | None:
    """Busca un curso LUT por nombre o código para añadirlo manualmente al RAM."""
    query = input("Buscar curso LUT por nombre o código (vacío para cancelar): ").strip()
    if not query:
        return None

    results = filter_lut_candidates(search_lut_courses(query), config)
    if not results:
        console.print("[yellow]No se encontraron cursos LUT que coincidan con esa búsqueda.[/yellow]\n")
        return None

    table = Table(show_lines=True)
    table.add_column("#", justify="right", width=4)
    table.add_column("Codigo", style="green", width=12)
    table.add_column("Nombre", style="white", width=42)
    table.add_column("ECTS", justify="center", width=8)
    table.add_column("Nivel", style="magenta", width=12)
    for index, result in enumerate(results, start=1):
        table.add_row(
            str(index),
            result["code"],
            result["name"][:41],
            f"{result['credits_min']}-{result['credits_max']}",
            result["course_level"] or "N/A",
        )
    console.print(table)

    choice = input(f"Selecciona curso (1-{len(results)}) o vacío para cancelar: ").strip()
    if not choice:
        return None
    try:
        index = int(choice) - 1
        if index < 0 or index >= len(results):
            console.print("[red]Numero fuera de rango.[/red]")
            return None
    except ValueError:
        console.print("[red]Entrada invalida.[/red]")
        return None

    selected = results[index]
    scored = score_similarity(course, [selected])
    return scored[0] if scored else selected


def review_candidates(course: dict, scored: list[dict], config: dict) -> list[dict] | str | None:
    """Permite seleccionar uno o varios candidatos, comparándolos con el ULPGC."""
    if not scored:
        return None

    limit_state = {"current": min(RESULT_LIMIT, len(scored))}
    show_comparison(course, scored[0], include_ulpgc=True)

    while True:
        prompt = (
            f"Selecciona candidato(s) (1-{limit_state['current']}, varios con coma o espacio), "
            "'v'+num para vista detallada, 'j'+num para JSON, 'm' para más resultados, "
            "'a' para añadir manualmente, 'c' para combinaciones, o 's' para saltar: "
        )
        choice = input(prompt).strip().lower()
        if choice == "s":
            return None
        if choice == "c":
            return "combo"
        if choice == "m":
            limit_state["current"] = min(limit_state["current"] + MORE_RESULTS_STEP, len(scored))
            render_results(scored, limit=limit_state["current"])
            continue
        if choice == "a":
            manual = search_manual_lut_course(course, config)
            if manual is None:
                continue
            show_comparison(course, manual, include_ulpgc=False)
            if prompt_yes_no("¿Incluir este curso encontrado manualmente en tu selección?", default=True):
                return [manual]
            console.print("[yellow]Curso descartado.[/yellow]\n")
            continue
        if choice.startswith("j"):
            selection = choice[1:].strip()
            try:
                index = int(selection) - 1
                if index < 0 or index >= limit_state["current"]:
                    console.print("[red]Numero fuera de rango para JSON.[/red]")
                    continue
            except ValueError:
                console.print("[red]Entrada invalida para JSON.[/red]")
                continue
            console.print_json(data=scored[index])
            continue
        if choice.startswith("v"):
            selection = choice[1:].strip()
            try:
                index = int(selection) - 1
                if index < 0 or index >= limit_state["current"]:
                    console.print("[red]Numero fuera de rango.[/red]")
                    continue
            except ValueError:
                console.print("[red]Entrada invalida. Usa 'v 1' para ver el candidato 1.[/red]")
                continue
            preview_candidate(scored[index], rank=index + 1)
            show_comparison(course, scored[index], include_ulpgc=False)
            continue

        tokens = choice.replace(",", " ").split()
        if not tokens:
            console.print("[red]Entrada invalida.[/red]")
            continue
        try:
            indices = [int(token) - 1 for token in tokens]
        except ValueError:
            console.print("[red]Entrada invalida.[/red]")
            continue
        if any(index < 0 or index >= limit_state["current"] for index in indices):
            console.print("[red]Numero fuera de rango.[/red]")
            continue

        selected_candidates = [scored[index] for index in indices]
        if len(selected_candidates) == 1:
            candidate = selected_candidates[0]
            show_comparison(course, candidate, include_ulpgc=False)
            if prompt_yes_no("¿Incluir este candidato en tu seleccion?", default=False):
                return [candidate]
            console.print("[yellow]Candidato descartado. Sigue revisando otros candidatos o usa 's' para saltar.[/yellow]\n")
            continue

        console.print("\n[bold cyan]Selección múltiple:[/bold cyan]")
        for candidate in selected_candidates:
            show_comparison(course, candidate, include_ulpgc=False)
        show_multi_coverage(course, selected_candidates)
        if prompt_yes_no("¿Confirmar esta selección múltiple?", default=True):
            return selected_candidates
        console.print("[yellow]Selección descartada. Sigue revisando otros candidatos o usa 's' para saltar.[/yellow]\n")


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
        console.print("\n[bold cyan]Detalles de la combinacion seleccionada[/bold cyan]")
        for item in combo["candidates"]:
            console.print(
                f"- {item['code']} | {item['name']} | "
                f"{item['remaining_capacity']:.1f} ECTS restantes | {item['best_score']:.1f}%"
            )
        console.print(f"\n[bold]Total capacidad:[/bold] {combo['total_capacity']:.1f} ECTS")
        console.print(f"[bold]Ajuste al objetivo:[/bold] {combo['closeness']:.2f}")

        if prompt_yes_no("¿Asignar esta combinacion al curso ULPGC?", default=False):
            return combo
        console.print("[yellow]Combinacion descartada. Puedes elegir otra o saltar.[/yellow]\n")


def assign_candidate(course: dict, candidate: dict, assignments: dict[str, list[dict]], lut_assignments: dict[str, list[str]]) -> bool:
    """Asigna el candidato seleccionado y actualiza los registros de LUT."""
    ulpgc_credits = get_ulpgc_credits(course)
    candidate_credits = parse_float_credits(candidate.get("credits_max", 0))
    if candidate_credits == 0.0:
        candidate_credits = parse_float_credits(candidate.get("credits_min", 0))

    can_assign, remaining = can_use_same_lut(candidate, ulpgc_credits, lut_assignments, assignments)
    if not can_assign:
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
        return False

    ulpgc_code = course.get("code")
    append = prompt_yes_no("¿Añadir esta asignación además de las existentes?", default=True)
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
    console.print(f"[green]Asignado {candidate.get('code', 'N/A')} a {ulpgc_code}.[/green]\n")
    return True


def assign_candidate_with_credits(
    course: dict,
    candidate: dict,
    assigned_credits: float,
    assignments: dict[str, list[dict]],
    lut_assignments: dict[str, list[str]],
) -> bool:
    """Asigna un curso LUT con una cantidad explícita de créditos ULPGC."""
    candidate_credits = parse_float_credits(candidate.get("credits_max", 0))
    if candidate_credits == 0.0:
        candidate_credits = parse_float_credits(candidate.get("credits_min", 0))

    can_assign, remaining = can_use_same_lut(candidate, assigned_credits, lut_assignments, assignments)
    if not can_assign:
        console.print(
            f"[yellow]Aviso:[/yellow] {candidate.get('code', 'N/A')} no tiene capacidad suficiente "
            f"({remaining:.1f} ECTS libres)."
        )
        return False

    entry = {
        "lut_code": candidate.get("code", "N/A"),
        "lut_name": candidate.get("name", "N/A"),
        "ulpgc_credits": assigned_credits,
        "lut_credits": candidate_credits,
    }
    ulpgc_code = course.get("code")
    assignments.setdefault(ulpgc_code, []).append(entry)
    lut_assignments.setdefault(candidate.get("code", ""), []).append(ulpgc_code)
    console.print(
        f"[green]Asignado {candidate.get('code', 'N/A')} a {ulpgc_code} "
        f"con {assigned_credits:.1f} ECTS.[/green]\n"
    )
    return True


def assign_group(course: dict, candidates: list[dict], assignments: dict[str, list[dict]], lut_assignments: dict[str, list[str]]) -> bool:
    """Asigna uno o varios cursos LUT a un curso ULPGC tras una selección múltiple."""
    if not candidates:
        return False
    success = True
    for candidate in candidates:
        if not assign_candidate(course, candidate, assignments, lut_assignments):
            success = False
    return success


def assign_combo(course: dict, combo: dict, assignments: dict[str, list[dict]], lut_assignments: dict[str, list[str]]) -> bool:
    """Asigna varios cursos LUT a un curso ULPGC de una sola vez."""
    if not combo or not combo.get("candidates"):
        return False
    remaining_target = get_ulpgc_credits(course)
    success = True
    for candidate in combo["candidates"]:
        available = parse_float_credits(candidate.get("remaining_capacity", 0))
        if available <= 0:
            available = parse_float_credits(candidate.get("credits_max", 0)) or parse_float_credits(candidate.get("credits_min", 0))
        assigned_credits = min(remaining_target, available)
        if assigned_credits <= 0:
            continue
        if not assign_candidate_with_credits(course, candidate, assigned_credits, assignments, lut_assignments):
            success = False
        else:
            remaining_target -= assigned_credits
        if remaining_target <= 0:
            break
    return success and remaining_target <= 0.0001


def render_course_list(courses: list[dict], assignments: dict[str, list[dict]], config: dict) -> None:
    """Muestra una tabla con los cursos ULPGC disponibles y su estado de asignacion."""
    table = Table(show_lines=False)
    table.add_column("#", justify="right", width=4)
    table.add_column("Codigo", style="green", width=12)
    table.add_column("Nombre", style="white", width=40)
    table.add_column("Tipo", style="yellow", width=12)
    table.add_column("Sem.", justify="center", width=6)
    table.add_column("ECTS", justify="center", width=6)
    table.add_column("Asignado a", style="cyan", width=18)

    visible = [course for course in courses if course_matches_filters(course, config)]
    console.print(
        f"[dim]Filtros activos -> optativas: {'sí' if config['show_optatives'] else 'no'} | "
        f"semestre: {semester_filter_label(config)} | "
        f"mostrar master+: {lut_level_filter_label(config)} | "
        f"periodo LUT: {lut_period_filter_label(config)}[/dim]"
    )
    for index, course in enumerate(visible, start=1):
        code = course.get("code", "N/A")
        status = assignments.get(code)
        assigned = ", ".join([entry.get("lut_code", "") for entry in status]) if status else "-"
        table.add_row(
            str(index),
            code,
            course.get("name", "N/A")[:38],
            course.get("type", "N/A"),
            str(course.get("semester", "N/A")),
            str(get_ulpgc_credits(course)),
            assigned,
        )

    console.print(table)


def search_and_review_course(course: dict, assignments: dict[str, list[dict]], lut_assignments: dict[str, list[str]], config: dict, courses_dict: dict[str, dict] | None = None) -> None:
    """Busca y revisa candidatos para una asignatura ULPGC."""
    console.print(f"\n[bold cyan]Buscando equivalencias para {course.get('name', 'N/A')} ({course.get('code', 'N/A')})[/bold cyan]")
    console.print(f"[yellow]Keywords usadas: {', '.join(course.get('keywords', []))}[/yellow]\n")

    results = search_keywords(course.get("keywords", []))
    results = filter_lut_candidates(results, config)
    if not results:
        console.print("[red]No se encontraron candidatos para esta asignatura con los filtros activos.[/red]\n")
        return

    scored = score_similarity(course, results)
    deduped = deduplicate_candidates(scored)
    if len(deduped) < len(scored):
        console.print(f"[dim]Se han eliminado {len(scored) - len(deduped)} coincidencias duplicadas.[/dim]\n")

    render_results(deduped)
    console.print(
        "[dim]Pulsa 'c' para combinaciones, 'a' para añadir un curso manualmente, "
        "'m' para ver más candidatos, o varios números (ej. 1,3,5) para seleccionar varios a la vez.[/dim]\n"
    )
    selection = review_candidates(course, deduped, config)
    if selection == "combo":
        combos = find_combo_candidates(course, deduped, assignments, lut_assignments, config, max_combo=2)
        combo = review_combo_candidates(combos, course)
        if combo is None:
            console.print("[yellow]No se seleccionó ninguna combinación.[/yellow]\n")
            return
        if not assign_combo(course, combo, assignments, lut_assignments):
            console.print("[yellow]No se guardó la combinación seleccionada.[/yellow]\n")
        elif courses_dict is not None:
            render_current_agreement(assignments, courses_dict)
        return

    if selection is None:
        console.print("[yellow]No se realizó ninguna asignación.[/yellow]\n")
        return

    if not assign_group(course, selection, assignments, lut_assignments):
        console.print("[yellow]No se guardó la asignación. Puedes revisar otro candidato más tarde.[/yellow]\n")
    elif courses_dict is not None:
        render_current_agreement(assignments, courses_dict)


def select_course_by_input(courses: list[dict], assignments: dict[str, list[dict]], config: dict) -> dict | None:
    """Selecciona una asignatura ULPGC desde la lista filtrada."""
    visible = [course for course in courses if course_matches_filters(course, config)]
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
    """Imprime un resumen de las asignaciones ULPGC -> LUT actuales."""
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
        for index, entry in enumerate(entries):
            table.add_row(
                ulpgc_code if index == 0 else "",
                course.get("name", "N/A")[:38] if index == 0 else "",
                entry.get("lut_code", "N/A"),
                entry.get("lut_name", "N/A")[:38],
                f"{entry.get('ulpgc_credits', '')}",
                f"{entry.get('lut_credits', '')}",
            )
    console.print(table)


def render_current_agreement(assignments: dict[str, list[dict]], courses_dict: dict[str, dict]) -> None:
    """Muestra de forma compacta el RAM en construcción tras cada asignación."""
    if not assignments:
        return
    console.print("\n[bold cyan]" + "=" * 36 + "[/bold cyan]")
    console.print("[bold cyan]RECONOCIMIENTO ACADÉMICO (en construcción)[/bold cyan]")
    console.print("[bold cyan]" + "=" * 36 + "[/bold cyan]")
    for ulpgc_code, entries in assignments.items():
        course = courses_dict.get(ulpgc_code, {})
        console.print(f"\n[bold]{course.get('name', ulpgc_code)}[/bold] [dim]({ulpgc_code})[/dim]")
        for entry in entries:
            console.print(f"    -> {entry.get('lut_name', 'N/A')} [dim]({entry.get('lut_code', 'N/A')})[/dim]")
    console.print()


def preview_candidate(candidate: dict, rank: int) -> None:
    """Muestra un candidato LUT con formato estructurado y legible."""
    header_parts = []
    if candidate.get("course_level"):
        header_parts.append(f"[bold blue]Nivel:[/bold blue] {candidate['course_level']}")
    if candidate.get("credits_min") == candidate.get("credits_max"):
        header_parts.append(f"[bold yellow]ECTS:[/bold yellow] {candidate['credits_min']}")
    else:
        header_parts.append(f"[bold yellow]ECTS:[/bold yellow] {candidate['credits_min']}-{candidate['credits_max']}")
    if candidate.get("language"):
        header_parts.append(f"[cyan]Idioma:[/cyan] {candidate['language']}")
    if candidate.get("periods"):
        header_parts.append(f"[magenta]Periodos LUT:[/magenta] {candidate['periods']}")
    if candidate.get("is_exchange"):
        header_parts.append("[bold green]Exchange[/bold green]")
    header = " | ".join(header_parts) if header_parts else "Sin metadatos disponibles"

    body_lines = []
    outcomes = candidate.get("learning_outcomes") or "No disponibles"
    body_lines.append("[bold magenta]RESULTADOS DE APRENDIZAJE[/bold magenta]")
    body_lines.append(f"    {outcomes.replace(chr(10), chr(10) + '    ')}")
    body_lines.append("")

    content = candidate.get("content") or "No disponibles"
    if len(content) > 1200:
        content = content[:1200] + " ... [dim](truncado)[/dim]"
    body_lines.append("[bold cyan]CONTENIDOS[/bold cyan]")
    body_lines.append(f"    {content.replace(chr(10), chr(10) + '    ')}")
    body_lines.append("")

    eq = candidate.get("equivalent_courses")
    if eq and eq != "Ninguna":
        body_lines.append("[bold green]EQUIVALENCIAS DECLARADAS POR LUT[/bold green]")
        body_lines.append(f"    {eq}")
        body_lines.append("")

    prereq = candidate.get("prerequisites")
    if prereq:
        prereq_short = prereq[:300] + ("..." if len(prereq) > 300 else "")
        body_lines.append("[dim]Prerrequisitos:[/dim]")
        body_lines.append(f"    {prereq_short}")

    panel = Panel(
        "\n".join(body_lines),
        title=f"[bold]#{rank}  {candidate['code']} - {candidate['name']}[/bold]",
        subtitle=header,
        border_style="blue",
        expand=False,
    )
    console.print(panel)


def compare_courses_detailed(ulpgc_course: dict, lut_course: dict) -> None:
    """Compara el contenido detallado de un curso ULPGC vs uno o varios LUT."""
    console.print("\n[bold cyan]COMPARACIÓN DE CONTENIDO[/bold cyan]")
    console.print(f"[bold green]ULPGC:[/bold green] {ulpgc_course.get('code')} | {ulpgc_course.get('name')}")
    console.print(f"[bold cyan]LUT:[/bold cyan]   {lut_course.get('code')} | {lut_course.get('name')}\n")
    console.print("[bold]Contenido ULPGC:[/bold]")
    console.print(ulpgc_course.get("description", "(sin descripción)") or "(sin descripción)", overflow="fold")
    console.print("\n[bold]Contenido LUT:[/bold]")
    console.print(lut_course.get("content", "(sin contenido)") or "(sin contenido)", overflow="fold")
    console.print("\n[bold]Resultados de Aprendizaje ULPGC:[/bold]")
    console.print(ulpgc_course.get("learning_outcomes", "(sin información)") or "(sin información)", overflow="fold")
    console.print("\n[bold]Resultados de Aprendizaje LUT:[/bold]")
    console.print(lut_course.get("learning_outcomes", "(sin información)") or "(sin información)", overflow="fold")
    console.print("\n[yellow]Nota: Revisa manualmente si la cobertura es suficiente para tu plan de movilidad.[/yellow]\n")


def show_lut_capacity_status(assignments: dict[str, list[dict]]) -> None:
    """Muestra un resumen de la capacidad disponible en cada curso LUT asignado."""
    if not assignments:
        console.print("[yellow]No hay asignaciones registradas.[/yellow]")
        return

    console.print("\n[bold cyan]ESTADO DE CAPACIDAD EN CURSOS LUT[/bold cyan]\n")
    lut_usage: dict[str, dict] = {}
    for _, entries in assignments.items():
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


def cli_mode() -> None:
    """Modo no interactivo para automatizaciones y uso directo por consola."""
    parser = argparse.ArgumentParser(description="Matcher ULPGC-LUT")
    parser.add_argument("--status", action="store_true", help="Mostrar estado actual")
    parser.add_argument("--pending", action="store_true", help="Listar asignaturas pendientes")
    parser.add_argument("--find", type=str, help="Buscar candidatos para un código ULPGC")
    parser.add_argument("--search-lut", type=str, help="Buscar cursos LUT por código, nombre, contenido o learning outcomes")
    parser.add_argument("--top", type=int, default=10, help="Número de candidatos a mostrar")
    parser.add_argument("--assign", nargs=2, metavar=("ULPGC", "LUT"), help="Asignar curso LUT a curso ULPGC")
    parser.add_argument("--replace", action="store_true", help="Reemplazar asignaciones previas del ULPGC")
    parser.add_argument("--save", action="store_true", help="Guardar asignaciones en JSON")
    parser.add_argument("--export", action="store_true", help="Exportar RAM a Markdown")
    parser.add_argument("--validate", action="store_true", help="Validar creditos y uso compartido de LUT")
    parser.add_argument("--output", default="RAM_emparejamientos.md", help="Ruta de salida para exportación")
    parser.add_argument("--show-optatives", action="store_true", help="Incluir optativas al filtrar ULPGC")
    parser.add_argument("--semester", type=str, help="Filtro de semestre ULPGC")
    parser.add_argument("--allow-master", action="store_true", help="Mantener compatibilidad: permite cursos LUT de master o superior")
    parser.add_argument("--bachelor-only", action="store_true", help="Ocultar cursos LUT de master o superior")
    parser.add_argument("--lut-period", type=str, help="Filtro de periodo LUT: 1,2 o 1-2")
    args = parser.parse_args()

    courses = load_ulpgc_courses()
    courses_dict = {course["code"]: course for course in courses}
    assignments = load_assignments_from_json()
    lut_assignments = build_lut_assignments(assignments)
    config = {
        "show_optatives": args.show_optatives,
        "semester_filter": None if not args.semester or args.semester == "todos" else args.semester,
        "show_master_or_higher": not args.bachelor_only,
        "lut_period_filter": None if not args.lut_period or args.lut_period == "todos" else args.lut_period,
    }

    if args.lut_period and args.lut_period != "todos":
        parse_period_filter(args.lut_period)
    if args.semester and args.semester != "todos":
        parse_semester_filter(args.semester)

    if args.status:
        pending = [
            {"code": course["code"], "name": course["name"], "credits": get_ulpgc_credits(course)}
            for course in courses
            if course["code"] not in assignments and course_matches_filters(course, config)
        ]
        print(json.dumps({
            "assigned_count": len(assignments),
            "pending_count": len(pending),
            "filters": config,
        }, ensure_ascii=False, indent=2))
        return

    if args.pending:
        pending = [
            {"code": course["code"], "name": course["name"], "credits": get_ulpgc_credits(course)}
            for course in courses
            if course["code"] not in assignments and course_matches_filters(course, config)
        ]
        print(json.dumps(pending, ensure_ascii=False, indent=2))
        return

    if args.find:
        ensure_model_loaded()
        course = next((item for item in courses if item["code"] == args.find), None)
        if not course:
            raise SystemExit(f"Curso ULPGC no encontrado: {args.find}")
        results = search_keywords(course.get("keywords", []))
        results = filter_lut_candidates(results, config)
        scored = score_similarity(course, results)
        print(json.dumps(deduplicate_candidates(scored)[:args.top], ensure_ascii=False, indent=2))
        return

    if args.search_lut:
        results = search_lut_courses(args.search_lut, limit=max(args.top, 1))
        results = filter_lut_candidates(results, config)
        print(json.dumps(results[:args.top], ensure_ascii=False, indent=2))
        return

    if args.assign:
        ulpgc_code, lut_code = args.assign
        course = courses_dict.get(ulpgc_code)
        if not course:
            raise SystemExit(f"Curso ULPGC no encontrado: {ulpgc_code}")
        candidate = load_lut_course_by_code(lut_code)
        if not candidate:
            raise SystemExit(f"Curso LUT no encontrado: {lut_code}")
        if not filter_lut_candidates([candidate], config):
            raise SystemExit(f"Curso LUT filtrado por la configuración actual: {lut_code}")

        ok, message = assign_candidate_non_interactive(
            course,
            candidate,
            assignments,
            lut_assignments,
            append=not args.replace,
        )
        saved = False
        if ok and args.save:
            saved = save_assignments_to_json(assignments, courses_dict)
        print(json.dumps({
            "ok": ok,
            "message": message,
            "saved": saved,
            "ulpgc_code": ulpgc_code,
            "lut_code": lut_code,
        }, ensure_ascii=False, indent=2))
        return

    if args.export:
        output = export_ram_markdown(assignments, courses_dict, courses, output_file=args.output)
        print(json.dumps({"ok": bool(output), "output": output}, ensure_ascii=False, indent=2))
        return

    if args.validate:
        print(json.dumps(validate_assignments(assignments, courses_dict), ensure_ascii=False, indent=2))
        return

    if args.save:
        print(json.dumps({"ok": save_assignments_to_json(assignments, courses_dict)}, ensure_ascii=False, indent=2))
        return

    parser.print_help()


def main() -> None:
    """Bucle principal del matcher interactivo."""
    ensure_model_loaded()
    ulpgc_data = load_ulpgc_courses()
    courses_dict = {course["code"]: course for course in ulpgc_data}
    assignments: dict[str, list[dict]] = load_assignments_from_json()
    lut_assignments: dict[str, list[str]] = build_lut_assignments(assignments)
    config = {
        "show_optatives": False,
        "semester_filter": None,
        "show_master_or_higher": True,
        "lut_period_filter": None,
    }

    console.print("\n[bold cyan]BIENVENIDO AL MATCHER ULPGC ↔ LUT[/bold cyan]\n")
    console.print("[dim]Este programa te ayuda a encontrar equivalencias entre cursos ULPGC y cursos LUT.\n[/dim]")
    console.print("[bold]Opciones principales del menú:[/bold]")
    console.print("  1. [bold]Seleccionar asignatura[/bold] -> Busca equivalencias para un curso ULPGC")
    console.print("  2. [bold]Ver emparejamientos[/bold] -> Muestra todas las asignaciones actuales")
    console.print("  3. [bold]Estado de capacidad[/bold] -> Ver cuántos créditos quedan disponibles en cada LUT")
    console.print("  4. [bold]Procesar obligatorias[/bold] -> Busca automáticamente equivalencias para todas las obligatorias sin asignar")
    console.print("  5. [bold]Revisar todo[/bold] -> Revisa todas las asignaturas no asignadas")
    console.print("  6. [bold]Guardar resultados[/bold] -> Exporta tus emparejamientos a un archivo JSON")
    console.print("  7. [bold]Configuración[/bold] -> Ajusta filtros de revisión")
    console.print("  8. [bold]Exportar RAM en Markdown[/bold] -> Genera el documento oficial listo para revisar")
    console.print("  q. [bold]Salir[/bold] -> Termina el programa\n")
    console.print(
        "[yellow]💡 Dentro de cada búsqueda: 'c' combinaciones · 'a' añadir curso LUT manualmente · "
        "'m' ver más candidatos · 'v'+num vista detallada · varios números (ej. 1,3,5) para selección múltiple.\n[/yellow]"
    )

    while True:
        console.print("\n[bold cyan]═══════════ MENÚ PRINCIPAL ═══════════[/bold cyan]")
        console.print("  1. Seleccionar asignatura")
        console.print("  2. Ver emparejamientos actuales")
        console.print("  3. Estado de capacidad en cursos LUT")
        console.print("  4. Procesar obligatorias sin asignar")
        console.print("  5. Revisar todas las sin asignar")
        console.print("  6. Guardar resultados (JSON)")
        console.print("  7. Configuración")
        console.print("  8. Exportar RAM en Markdown")
        console.print("  q. Salir\n")

        choice = input("Selecciona opción (1-8, q): ").strip().lower()
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
            search_and_review_course(course, assignments, lut_assignments, config, courses_dict)
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
                if not course_matches_filters(course, config):
                    continue
                processed += 1
                console.print(f"[dim][{processed}][/dim] ", end="")
                search_and_review_course(course, assignments, lut_assignments, config, courses_dict)
            console.print(f"[green]Procesadas {processed} asignaturas.[/green]")
        elif choice == "5":
            console.print("[cyan]Revisando todas las asignaturas sin asignar...[/cyan]\n")
            processed = 0
            for course in ulpgc_data:
                if course["code"] in assignments:
                    continue
                if not course_matches_filters(course, config):
                    continue
                processed += 1
                console.print(f"[dim][{processed}][/dim] ", end="")
                search_and_review_course(course, assignments, lut_assignments, config, courses_dict)
            console.print(f"[green]Revisadas {processed} asignaturas.[/green]")
        elif choice == "6":
            if assignments:
                if save_assignments_to_json(assignments, courses_dict):
                    console.print("[green]✓ Asignaciones guardadas correctamente.[/green]")
                else:
                    console.print("[red]✗ Error al guardar las asignaciones.[/red]")
            else:
                console.print("[yellow]No hay asignaciones para guardar.[/yellow]")
        elif choice == "7":
            console.print("\n[bold cyan]CONFIGURACIÓN[/bold cyan]\n")
            config["show_optatives"] = prompt_yes_no(
                f"Mostrar asignaturas optativas [{'sí' if config['show_optatives'] else 'no'}]?",
                default=config["show_optatives"],
            )
            config["show_master_or_higher"] = prompt_yes_no(
                f"Mostrar cursos LUT de nivel master o superior [{'sí' if config['show_master_or_higher'] else 'no'}]?",
                default=config["show_master_or_higher"],
            )
            lut_period_answer = input(
                f"Filtro de periodo LUT actual [{lut_period_filter_label(config)}]. "
                "Escribe 1-5, varios separados por coma (ej. 1,2), un rango (ej. 1-2), "
                "'todos' para quitar el filtro, o Enter para mantener: "
            ).strip().lower()
            if lut_period_answer:
                if lut_period_answer == "todos":
                    config["lut_period_filter"] = None
                else:
                    try:
                        parse_period_filter(lut_period_answer)
                        config["lut_period_filter"] = lut_period_answer
                    except ValueError:
                        console.print("[yellow]Periodo LUT no válido. Se mantiene la configuración anterior.[/yellow]")
            semester_answer = input(
                f"Filtro de semestre actual [{semester_filter_label(config)}]. "
                "Escribe 1-10, varios separados por coma (ej. 5,6), un rango (ej. 5-6), "
                "'todos' para quitar el filtro, o Enter para mantener: "
            ).strip().lower()
            if semester_answer:
                if semester_answer == "todos":
                    config["semester_filter"] = None
                else:
                    try:
                        parse_semester_filter(semester_answer)
                        config["semester_filter"] = semester_answer
                    except ValueError:
                        console.print("[yellow]Semestre no válido. Se mantiene la configuración anterior.[/yellow]")
        elif choice == "8":
            output = export_ram_markdown(assignments, courses_dict, ulpgc_data)
            if output:
                console.print(f"[green]✓ RAM exportado en Markdown en {output}[/green]")
            else:
                console.print("[yellow]No hay asignaciones para exportar.[/yellow]")
        else:
            console.print("[red]❌ Opción no reconocida. Intenta de nuevo.[/red]")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        cli_mode()
    else:
        main()
