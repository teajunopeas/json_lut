#!/usr/bin/env python3
"""
matcher_v2.py - Búsqueda inteligente: Keywords + Embeddings Semánticos
SIN caracteres Unicode para compatibilidad Windows
"""
import sqlite3
import json
from pathlib import Path
from rich.console import Console
from rich.table import Table
from sentence_transformers import SentenceTransformer, util

console = Console()
DB_PATH = Path("lut_courses.db")

# Cargar modelo embeddings
console.print("[cyan]Cargando modelo de embeddings (all-MiniLM-L6-v2)...[/cyan]")
model = SentenceTransformer('all-MiniLM-L6-v2')

# Mapeo de temas ULPGC a keywords en inglés
KEYWORD_MAP = {
    "49192": {  # Métodos Matemáticos II
        "keywords": [
            "differential equations", "partial differential", 
            "fourier series", "laplace", "wave equation", "heat equation",
            "separation variables", "edp", "pde"
        ],
        "name": "Métodos Matemáticos y sus Aplicaciones II"
    },
    "49196": {  # Métodos Matemáticos III
        "keywords": [
            "finite element", "numerical methods", "finite difference",
            "weak solution", "discretization", "galerkin", "fem",
            "variational", "approximation"
        ],
        "name": "Métodos Matemáticos y sus Aplicaciones III"
    },
    "49188": {  # Análisis Matemático III
        "keywords": [
            "complex analysis", "residue theorem", "cauchy", "analytic",
            "fourier", "integration", "series", "complex variable"
        ],
        "name": "Análisis Matemático III"
    },
}

def prepare_text(content: str, outcomes: str, name: str = "") -> str:
    """Preparar texto para embedding."""
    parts = []
    if content and len(str(content).strip()) > 20:
        parts.append(str(content))
    if outcomes and len(str(outcomes).strip()) > 20:
        parts.append(str(outcomes))
    if not parts and name:
        parts.append(str(name))
    return " ".join(parts).strip()

def search_keywords(keywords: list, limit: int = 30) -> list:
    """Buscar por keywords en FTS."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    
    query = " OR ".join(keywords)
    sql = """
        SELECT code, name, credits_min, credits_max, course_level, periods, content, learning_outcomes
        FROM courses 
        WHERE (courses MATCH ?) AND content IS NOT NULL AND content != ''
        ORDER BY rank LIMIT ?
    """
    cursor = conn.execute(sql, (query, limit))
    results = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return results

def score_similarity(ulpgc_text: str, candidates: list) -> list:
    """Calcular similitud semántica."""
    ulpgc_emb = model.encode(ulpgc_text, convert_to_tensor=True)
    
    scored = []
    for c in candidates:
        lut_text = prepare_text(c["content"], c["learning_outcomes"], c.get("name", ""))
        lut_emb = model.encode(lut_text, convert_to_tensor=True)
        sim = util.cos_sim(ulpgc_emb, lut_emb).item()
        
        scored.append({
            **c,
            "similarity_score": round(sim * 100, 1),
        })
    
    scored.sort(key=lambda x: x["similarity_score"], reverse=True)
    return scored

def main():
    # Cargar datos ULPGC
    with open("ulpgc_courses.json", encoding="utf-8") as f:
        ulpgc_data = json.load(f)
    
    # Buscar cursos target
    target = [c for c in ulpgc_data if c.get("code") in KEYWORD_MAP]
    
    if not target:
        console.print("[red]ERROR: No se encontraron cursos objetivo[/red]")
        return
    
    for course in target:
        code = course.get("code")
        config = KEYWORD_MAP[code]
        keywords = config["keywords"]
        
        console.print(f"\n[bold cyan]{'='*80}[/bold cyan]")
        console.print(f"[bold]{config['name']} ({course['credits']} ECTS)[/bold]")
        console.print(f"[cyan]{'='*80}[/cyan]\n")
        
        # Paso 1: Buscar por keywords
        console.print(f"[yellow]Buscando {len(keywords)} keywords en ingles...[/yellow]")
        results = search_keywords(keywords, limit=40)
        
        if not results:
            console.print(f"[red]Sin resultados para {config['name']}[/red]\n")
            continue
        
        console.print(f"[green][OK] {len(results)} cursos encontrados[/green]\n")
        
        # Paso 2: Ranking por similitud
        console.print("[cyan]Calculando similitud semantica...[/cyan]")
        ulpgc_text = prepare_text(
            course.get("content", ""),
            course.get("learningOutcomes", ""),
            course.get("name", "")
        )
        scored = score_similarity(ulpgc_text, results)
        
        # Mostrar resultados
        console.print("\n[bold green]RESULTADOS - Top 8:[/bold green]\n")
        
        table = Table(show_lines=True)
        table.add_column("Similitud", justify="center", style="bold cyan", width=10)
        table.add_column("Codigo", style="green", width=12)
        table.add_column("Nombre", style="white", width=40)
        table.add_column("ECTS", justify="center", width=6)
        table.add_column("Nivel", style="magenta", width=12)
        
        for r in scored[:8]:
            score = r["similarity_score"]
            style = "bold green" if score >= 60 else "bold yellow" if score >= 50 else "dim"
            
            table.add_row(
                f"[{style}]{score}%[/{style}]",
                r["code"],
                r["name"][:39],
                f"{r['credits_min']}-{r['credits_max']}",
                r["course_level"] or "N/A"
            )
        
        console.print(table)
        console.print()

if __name__ == "__main__":
    main()
