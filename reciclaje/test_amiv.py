"""Test rápido del matcher con AM IV."""
from matcher import load_ulpgc_courses, search_keywords, score_similarity, deduplicate_candidates
from rich.console import Console
from rich.table import Table

console = Console()
ulpgc = load_ulpgc_courses()
courses = {c['code']: c for c in ulpgc}

# AM IV = Análisis Matemático IV (49197)
code = '49197'
course = courses.get(code)

if not course:
    print(f'Curso {code} no encontrado')
else:
    console.print(f'\n[bold cyan]{course["name"]}[/bold cyan] ({code}) - {course.get("credits")} ECTS')
    console.print(f'[yellow]Keywords:[/yellow] {course.get("keywords", [])}\n')
    
    results = search_keywords(course.get('keywords', []))
    console.print(f'[green]Candidatos encontrados: {len(results)}[/green]\n')
    
    scored = score_similarity(course, results)
    deduped = deduplicate_candidates(scored)
    
    table = Table(show_header=True)
    table.add_column('Top', justify='right', width=4)
    table.add_column('Código', width=12, style='green')
    table.add_column('Nombre', width=50)
    table.add_column('ECTS', width=6)
    table.add_column('Similitud', width=8)
    
    for i, c in enumerate(deduped[:10], 1):
        table.add_row(
            str(i),
            c['code'],
            c['name'][:49],
            str(c.get('credits_max', 0)),
            f"{c['best_score']:.1f}%"
        )
    
    console.print(table)
