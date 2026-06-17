"""Construye la base SQLite usada por el matcher.

Lee `lut_courses.json`, normaliza los campos que usa la busqueda y crea
`lut_courses.db` con una tabla virtual FTS5 llamada `courses`.

La base de datos es un artefacto regenerable y no se versiona en Git.
"""
import json
import sqlite3
import re
from pathlib import Path
from rich.console import Console

console = Console()
JSON_PATH = Path("lut_courses.json")
DB_PATH = Path("lut_courses.db")

def build_agent_db():
    """Regenera `lut_courses.db` desde el JSON principal de cursos LUT."""
    if not JSON_PATH.exists():
        console.print(f"[red]Error:[/red] No se encontró {JSON_PATH}. Ejecuta primero scraper.py")
        return

    console.print(f"[cyan]Leyendo {JSON_PATH}...[/cyan]")
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        courses = json.load(f)

    console.print(f"[cyan]Construyendo base de datos SQLite en {DB_PATH}...[/cyan]")
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DROP TABLE IF EXISTS courses")
    
    # Esquema optimizado para el Agente + Búsqueda Semántica
    conn.execute("""
        CREATE VIRTUAL TABLE courses USING fts5(
            id, code, name, 
            credits_min, credits_max, 
            course_level, language, periods, is_exchange,
            learning_outcomes, content, equivalent_courses,
            tokenize='unicode61 remove_diacritics 1'
        )
    """)
    
    insert_sql = """
        INSERT INTO courses (id, code, name, credits_min, credits_max, course_level, 
                             language, periods, is_exchange, learning_outcomes, content, equivalent_courses)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    
    rows = []
    for c in courses:
        # 1. Procesar créditos
        credits = c.get("credits", "0")
        if isinstance(credits, str) and "+" in credits:
            c_min, c_max = credits.split("+")
        elif isinstance(credits, (int, float)):
            c_min = c_max = int(credits)
        elif isinstance(credits, dict): # Por si el JSON aún tiene el formato {min: 5, max: 5}
            c_min = credits.get("min", 0)
            c_max = credits.get("max", 0)
        else:
            # Intentar convertir string directo a número
            try:
                c_min = c_max = int(float(str(credits)))
            except (ValueError, TypeError):
                c_min = c_max = 0
            
        # 2. Procesar periodos (de la lista teachingPeriods o rawDetail)
        periods = c.get("teachingPeriods")
        if isinstance(periods, list):
            periods_str = ", ".join(str(p) for p in periods)
        else:
            periods_str = ""
            
        # 3. Limpieza básica de HTML en equivalencias
        eq_info = c.get("equivalentCoursesInfo", "")
        eq_str = re.sub(r'<[^>]+>', ' ', str(eq_info)).strip() if eq_info else "Ninguna"

        rows.append((
            c.get("id", ""),
            c.get("code", ""),
            c.get("name", ""),
            int(c_min),
            int(c_max),
            c.get("courseLevel", "Desconocido"),
            c.get("languageOfLearning", ""),
            periods_str,
            1 if c.get("isExchangeCourse") else 0,
            c.get("learningOutcomes", ""),
            c.get("content", ""),
            eq_str
        ))
        
        # Inserción por lotes para eficiencia
        if len(rows) >= 500:
            conn.executemany(insert_sql, rows)
            rows = []
            
    if rows:
        conn.executemany(insert_sql, rows)
        
    conn.commit()
    conn.close()
    console.print(f"[green]✓ Base de datos lista con {len(courses)} cursos indexados.[/green]")

if __name__ == "__main__":
    build_agent_db()
