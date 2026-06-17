from matcher import (
    load_ulpgc_courses,
    search_keywords,
    score_similarity,
    deduplicate_candidates,
    can_use_same_lut,
    render_results,
    show_assignment_summary,
)


def format_candidate_line(c):
    return f"{c.get('code')} - {c.get('name')} | best={c.get('best_score')}% (cont={c.get('content_score')}%, out={c.get('outcomes_score')}%)"


def main():
    ulpgc = load_ulpgc_courses()
    courses = {c['code']: c for c in ulpgc}
    # Selección de prueba: Métodos Matemáticos II, III y un optativa/optable (Deep Learning)
    test_codes = ['49204', '49196', '49201']

    assignments = {}
    lut_assignments = {}

    for code in test_codes:
        course = courses.get(code)
        if not course:
            print(f"Curso {code} no encontrado en ULPGC.")
            continue
        print('\n' + '='*80)
        print(f"Probando emparejamiento automático para: {course['name']} ({code}) - {course.get('credits')} ECTS")
        keywords = course.get('keywords', [])
        print(f"Keywords: {keywords}")
        results = search_keywords(keywords)
        if not results:
            print("No hay candidatos LUT encontrados.")
            continue
        scored = score_similarity(course, results)
        deduped = deduplicate_candidates(scored)
        print(f"Top candidatos (max 5):")
        for c in deduped[:5]:
            print(' -', format_candidate_line(c))

        top = deduped[0]
        can_assign, remaining = can_use_same_lut(top, float(course.get('credits', 0)), lut_assignments, assignments)
        print(f"Intentando asignar top candidato {top['code']}: puede_asignar={can_assign}, restante_ects={remaining}")
        if can_assign:
            entry = {
                'lut_code': top.get('code'),
                'lut_name': top.get('name'),
                'ulpgc_credits': float(course.get('credits', 0)),
                'lut_credits': float(top.get('credits_max') or top.get('credits_min') or 0),
            }
            assignments.setdefault(code, []).append(entry)
            lut_assignments.setdefault(top.get('code',''), []).append(code)
            print(f"Asignado {top.get('code')} -> {code}")
        else:
            print("No se pudo asignar por falta de creditos.")

    print('\nResumen de asignaciones:')
    show_assignment_summary(assignments, courses)


if __name__ == '__main__':
    main()
