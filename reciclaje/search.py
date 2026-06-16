"""
Motor de búsqueda CLI para el catálogo de cursos de LUT.
Utiliza SQLite con FTS5 (Full-Text Search) para búsquedas instantáneas y ranking por relevancia (BM25).

Uso:
  python search.py --build                   # Construye el índice desde lut_courses.json
  python search.py "bayesian statistics"     # Búsqueda de texto completo
  python search.py "python" --level Master --lang en --limit 10
  python search.py "physics" --exchange      # Solo cursos de intercambio
"""
import argparse
import json
import sqlite3
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.text import Text
    from rich import print as rprint
except ImportError:
    print("Error: Se requiere la librería 'rich'. Instálala con: pip install rich")
    sys.exit(1)

console = Console()

DB_PATH = Path("lut_courses.db")
JSON_PATH = Path("lut_courses.json")

def build_index(json_path: Path, db_path: Path) -> None:
    """Lee el JSON y construye la base de datos SQLite con FTS5."""
    if not json_path.exists():
        console.print(f"[red]Error:[/red] No se encontró {json_path}. Ejecuta el scraper primero.")
        sys.exit(1)

    console.print(f"[cyan]Leyendo {json_path}...[/cyan]")
    with open(json_path, "r", encoding="utf-8") as f:
        courses = json.load(f)

    console.print(f"[cyan]Construyendo índice SQLite en {db_path}...[/cyan]")
    conn = sqlite3.connect(db_path)
    
    # Eliminamos la tabla anterior para reconstruir desde cero
    conn.execute("DROP TABLE IF EXISTS courses")
    
    # Creamos una tabla virtual FTS5. 
    # 'tokenize=unicode61 remove_diacritics 1' ayuda a ignorar acentos (útil para fi/sv/en).
    conn.execute("""
        CREATE VIRTUAL TABLE courses USING fts5(
            id, code, name, credits, courseLevel, year, languageOfLearning,
            isExchangeCourse, content, learningOutcomes, prerequisites, searchTags,
            tokenize='unicode61 remove_diacritics 1'
        )
    """)
    
    # Preparamos la inserción masiva
    insert_sql = """
        INSERT INTO courses (id, code, name, credits, courseLevel, year, languageOfLearning,
                             isExchangeCourse, content, learningOutcomes, prerequisites, searchTags)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    
    rows_to_insert = []
    for course in courses:
        # Convertimos la lista de tags a string para que FTS5 pueda indexarla
        tags = " ".join(course.get("searchTags", []))
        is_exchange = 1 if course.get("isExchangeCourse") else 0
        
        rows_to_insert.append((
            course.get("id", ""),
            course.get("code", ""),
            course.get("name", ""),
            str(course.get("credits", "")),
            course.get("courseLevel", ""),
            course.get("year", ""),
            course.get("languageOfLearning", ""),
            is_exchange,
            course.get("content", ""),
            course.get("learningOutcomes", ""),
            course.get("prerequisites", ""),
            tags
        ))
        
        # Insertamos en lotes de 500 para eficiencia de memoria
        if len(rows_to_insert) >= 500:
            conn.executemany(insert_sql, rows_to_insert)
            rows_to_insert = []
            
    if rows_to_insert:
        conn.executemany(insert_sql, rows_to_insert)
        
    conn.commit()
    conn.close()
    console.print(f"[green]✓ Índice construido exitosamente con {len(courses)} cursos.[/green]")


def parse_credits_filter(credits_str: str) -> str:
    """Convierte un filtro de créditos en una condición SQL válida."""
    if credits_str.isdigit():
        return f"credits = '{credits_str}'"
    if credits_str.startswith(">="):
        val = credits_str[2:]
        return f"CAST(credits AS INTEGER) >= {val}"
    if credits_str.startswith("<="):
        val = credits_str[2:]
        return f"CAST(credits AS INTEGER) <= {val}"
    if "-" in credits_str:
        min_val, max_val = credits_str.split("-")
        return f"CAST(credits AS INTEGER) BETWEEN {min_val} AND {max_val}"
    return f"credits LIKE '%{credits_str}%'"


def search_courses(
    query: str,
    db_path: Path,
    level: Optional[str] = None,
    lang: Optional[str] = None,
    credits: Optional[str] = None,
    exchange_only: bool = False,
    limit: int = 20
) -> List[Dict[str, Any]]:
    """Ejecuta la búsqueda FTS5 con filtros adicionales."""
    if not db_path.exists():
        console.print(f"[red]Error:[/red] No se encontró la base de datos {db_path}. Ejecuta `python search.py --build` primero.")
        sys.exit(1)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    
    # Construimos la consulta SQL
    # Usamos MATCH para la búsqueda de texto completo (BM25 ranking)
    sql = "SELECT * FROM courses WHERE courses MATCH ?"
    params = [query]
    
    # Añadimos filtros exactos (AND)
    if level:
        sql += " AND courseLevel = ?"
        params.append(level)
    if lang:
        sql += " AND languageOfLearning LIKE ?"
        params.append(f"%{lang}%")
    if credits:
        sql += f" AND {parse_credits_filter(credits)}"
    if exchange_only:
        sql += " AND isExchangeCourse = 1"
        
    # Ordenamos por relevancia (rank es nativo de FTS5, menor es mejor)
    sql += " ORDER BY rank LIMIT ?"
    params.append(limit)
    
    cursor = conn.execute(sql, params)
    results = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return results


def display_results(results: List[Dict[str, Any]], query: str) -> None:
    """Muestra los resultados de forma bonita en la terminal."""
    if not results:
        console.print("[yellow]No se encontraron cursos que coincidan con tu búsqueda.[/yellow]")
        return

    console.print(f"\n[bold cyan]Se encontraron {len(results)} resultados para '[bold white]{query}[/bold white]':[/bold cyan]\n")
    
    for i, course in enumerate(results, 1):
        # Panel principal del curso
        title = f"[bold green]{course['code']}[/bold green] - {course['name']}"
        
        # Metadatos en una línea
        meta_parts = []
        if course['credits']: meta_parts.append(f"[yellow]📚 {course['credits']} ECTS[/yellow]")
        if course['courseLevel']: meta_parts.append(f"[blue]🎓 {course['courseLevel']}[/blue]")
        if course['year']: meta_parts.append(f"[magenta]📅 {course['year']}[/magenta]")
        if course['languageOfLearning']: meta_parts.append(f"[cyan]🌐 {course['languageOfLearning']}[/cyan]")
        if course['isExchangeCourse'] == 1: meta_parts.append("[red]✈️ Exchange[/red]")
        
        meta_str = " | ".join(meta_parts)
        
        # Contenido resumido
        content = course.get('content') or course.get('learningOutcomes') or "Sin descripción disponible."
        # Truncamos el contenido a ~300 caracteres para no saturar la pantalla
        if len(content) > 350:
            content = content[:350] + "..."
            
        panel_content = f"{meta_str}\n\n[dim]{content}[/dim]"
        
        console.print(Panel(panel_content, title=f"#{i} {title}", expand=False, border_style="blue"))
        console.print()


def main():
    parser = argparse.ArgumentParser(description="Motor de búsqueda de cursos LUT")
    
    # Modos de operación
    parser.add_argument("query", nargs="?", default=None, help="Término de búsqueda (ej: 'machine learning')")
    parser.add_argument("--build", action="store_true", help="Construye el índice SQLite desde el JSON")
    parser.add_argument("--json", type=str, default=str(JSON_PATH), help="Ruta al archivo JSON (default: lut_courses.json)")
    parser.add_argument("--db", type=str, default=str(DB_PATH), help="Ruta a la base de datos SQLite (default: lut_courses.db)")
    
    # Filtros
    parser.add_argument("--level", type=str, help="Filtrar por nivel (ej: 'Master', 'Bachelor')")
    parser.add_argument("--lang", type=str, help="Filtrar por idioma (ej: 'en', 'fi')")
    parser.add_argument("--credits", type=str, help="Filtrar por créditos (ej: '5', '>=5', '3-6')")
    parser.add_argument("--exchange", action="store_true", help="Mostrar solo cursos de intercambio")
    parser.add_argument("--limit", type=int, default=15, help="Número máximo de resultados (default: 15)")

    args = parser.parse_args()

    if args.build:
        build_index(Path(args.json), Path(args.db))
        return

    if not args.query:
        console.print("[red]Error:[/red] Debes proporcionar un término de búsqueda o usar --build.")
        console.print("Ejemplo: [bold]python search.py 'data science' --level Master --limit 5[/bold]")
        sys.exit(1)

    results = search_courses(
        query=args.query,
        db_path=Path(args.db),
        level=args.level,
        lang=args.lang,
        credits=args.credits,
        exchange_only=args.exchange,
        limit=args.limit
    )
    
    display_results(results, args.query)


if __name__ == "__main__":
    main()