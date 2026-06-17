"""Emparejamiento realista: múltiples LUT por ULPGC con distribución de créditos."""
from matcher import load_ulpgc_courses, search_keywords, score_similarity, deduplicate_candidates
from rich.console import Console
from rich.table import Table

console = Console()

def find_realistic_combinations(course, scored_candidates, target_credits, max_courses=3):
    """
    Busca combinaciones de cursos LUT que cubran realísticamente los créditos ULPGC.
    Retorna lista de combinaciones: [{'lut_code': X, 'lut_name': Y, 'credits': Z, 'similarity': S}, ...]
    """
    # Filtrar candidatos con similitud >= 40% y créditos razonables (3-15 ECTS)
    suitable = [
        c for c in scored_candidates 
        if c['best_score'] >= 40 and 3 <= c.get('credits_max', 0) <= 15
    ]
    
    if not suitable:
        return None
    
    # Agrupar por rango de créditos
    small = [c for c in suitable if c.get('credits_max', 0) <= 5]
    medium = [c for c in suitable if 5 < c.get('credits_max', 0) <= 10]
    large = [c for c in suitable if c.get('credits_max', 0) > 10]
    
    combinations = []
    
    # 1. Intentar con un solo curso medio/grande
    for candidate in medium + large:
        if abs(candidate.get('credits_max', 0) - target_credits) <= 3:
            combinations.append({
                'courses': [candidate],
                'total_credits': candidate.get('credits_max', 0),
                'total_similarity': candidate['best_score'],
                'efficiency': candidate.get('credits_max', 0) / target_credits if target_credits > 0 else 0
            })
    
    # 2. Intentar con dos cursos pequeños/medianos
    for i, c1 in enumerate(small + medium):
        for c2 in (small + medium)[i+1:]:
            total_cred = c1.get('credits_max', 0) + c2.get('credits_max', 0)
            if target_credits * 0.8 <= total_cred <= target_credits * 1.3:
                avg_sim = (c1['best_score'] + c2['best_score']) / 2
                combinations.append({
                    'courses': [c1, c2],
                    'total_credits': total_cred,
                    'total_similarity': avg_sim,
                    'efficiency': total_cred / target_credits if target_credits > 0 else 0
                })
    
    # Ordenar por: (1) eficiencia (cercana a 1.0), (2) similitud descendente
    combinations.sort(
        key=lambda x: (abs(x['efficiency'] - 1.0), -x['total_similarity'])
    )
    
    return combinations[:max_courses]

def main():
    ulpgc = load_ulpgc_courses()
    courses = {c['code']: c for c in ulpgc}
    test_codes = ['49192', '49196', '49201']
    
    console.print("\n[bold cyan]=== EMPAREJAMIENTO REALISTA CON DISTRIBUCIÓN DE CRÉDITOS ===[/bold cyan]\n")
    
    for code in test_codes:
        course = courses.get(code)
        if not course:
            continue
        
        ulpgc_credits = float(course.get('credits', 0))
        console.print(f"[bold]{course['name']}[/bold] ({code}) - {ulpgc_credits} ECTS")
        console.print(f"Keywords: {', '.join(course.get('keywords', [])[:3])}...\n")
        
        results = search_keywords(course.get('keywords', []))
        if not results:
            console.print("[red]Sin resultados[/red]\n")
            continue
        
        scored = score_similarity(course, results)
        deduped = deduplicate_candidates(scored)
        
        combinations = find_realistic_combinations(course, deduped, ulpgc_credits)
        
        if not combinations:
            console.print("[yellow]No se encontraron combinaciones realistas[/yellow]\n")
            continue
        
        # Mostrar top 3 combinaciones
        for i, combo in enumerate(combinations[:3], 1):
            table = Table(show_header=False, box=None)
            table.add_row(f"[green]Opción {i}:[/green]")
            for j, lut in enumerate(combo['courses'], 1):
                table.add_row(
                    f"  {j}. [{lut['code']}] {lut['name'][:50]} - {lut.get('credits_max', 0)} ECTS ({lut['best_score']}%)"
                )
            table.add_row(f"[cyan]Total: {combo['total_credits']} ECTS (eficiencia: {combo['efficiency']:.2f}x)[/cyan]")
            console.print(table)
        
        console.print()

if __name__ == '__main__':
    main()
