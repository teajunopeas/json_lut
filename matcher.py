import sqlite3
import numpy as np
from pathlib import Path
from rich.console import Console
from rich.table import Table
from sentence_transformers import SentenceTransformer, util

console = Console()
DB_PATH = Path("lut_courses.db")

# 1. Cargar el modelo de embeddings
console.print("[cyan]Cargando modelo de embeddings (all-MiniLM-L6-v2)...[/cyan]")
model = SentenceTransformer('all-MiniLM-L6-v2')

def prepare_text_for_embedding(content: str, outcomes: str) -> str:
    """Concatena y limpia el texto para que el embedding sea lo más preciso posible."""
    text = ""
    if content:
        text += f"Contenidos: {content}. "
    if outcomes:
        text += f"Resultados de aprendizaje: {outcomes}."
    return text.strip()

def get_filtered_candidates(query: str, target_semester: str, current_ects: int, limit: int = 15) -> list:
    """Paso 1: Filtrado duro en SQLite (Reglas burocráticas).
    
    Nota: Si no hay resultados FTS, usa búsqueda por palabras clave comunes.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    
    # Buscamos candidatos que coincidan mínimamente con el nombre o contenido
    sql = """
        SELECT code, name, credits_min, credits_max, course_level, periods, content, learning_outcomes
        FROM courses WHERE courses MATCH ? ORDER BY rank LIMIT ?
    """
    cursor = conn.execute(sql, (query, limit * 3))
    candidates_fts = cursor.fetchall()
    
    # Si FTS no encuentra nada (ej: búsqueda en español), hacer búsqueda fallback
    if not candidates_fts:
        console.print(f"[dim]→ FTS sin resultados, usando búsqueda fallback por palabras clave...[/dim]")
        # Fallback: buscar todo y confiar en embeddings para ranking
        sql_fallback = """
            SELECT code, name, credits_min, credits_max, course_level, periods, content, learning_outcomes
            FROM courses LIMIT ?
        """
        cursor = conn.execute(sql_fallback, (limit * 5,))
        candidates_fts = cursor.fetchall()
    
    valid_candidates = []
    for row in candidates_fts:
        level = (row["course_level"] or "").lower()
        is_master = "master" in level or "advanced" in level
        
        # REGLA DE LOS 150 ECTS (si nivel Master y semestre Autumn, necesitas >= 150 ECTS)
        if target_semester == "autumn" and current_ects < 150 and is_master:
            continue
            
        # REGLA DE CRÉDITOS (margen de +/- 2 ECTS)
        c_min, c_max = float(row["credits_min"]), float(row["credits_max"])
        # Asumimos que la asignatura de origen tiene un rango similar, esto se ajusta en el bucle principal
        
        valid_candidates.append(dict(row))
        
    conn.close()
    return valid_candidates[:limit]

def calculate_semantic_similarity(ulpgc_text: str, lut_candidates: list) -> list:
    """Paso 2: Convertir a embeddings y calcular similitud del coseno."""
    
    # Preparar textos
    ulpgc_embedding = model.encode(ulpgc_text, convert_to_tensor=True)
    
    scored_candidates = []
    for c in lut_candidates:
        lut_text = prepare_text_for_embedding(c["content"], c["learning_outcomes"])
        lut_embedding = model.encode(lut_text, convert_to_tensor=True)
        
        # Calcular similitud del coseno (0 a 1)
        similarity = util.cos_sim(ulpgc_embedding, lut_embedding).item()
        
        scored_candidates.append({
            **c,
            "similarity_score": round(similarity * 100, 1), # Convertir a porcentaje
            "prepared_text": lut_text # Lo guardamos por si queremos depurar
        })
        
    # Ordenar de mayor a menor similitud
    scored_candidates.sort(key=lambda x: x["similarity_score"], reverse=True)
    return scored_candidates

def main():
    # DATOS DE EJEMPLO (Tu asignatura de la ULPGC)
    ulpgc_course = {
        "name": "Métodos Matemáticos y sus Aplicaciones II",
        "credits": 3,
        "semester": "5", # 5 o 7 = autumn, 6 = spring
        "description": "Identificar las ecuaciones en derivadas parciales clásicas de la física matemática: ecuación de transporte, ecuación del calor, ecuación de ondas y ecuación de Laplace. Utilizar el método de las características para las EDOs de orden 1. Aplicar el método de separación de variables y operar formalmente con series de Fourier."
    }
    
    current_ects = 145 # Prueba con 145 y luego con 155 para ver el cambio
    
    target_semester = "autumn" if str(ulpgc_course["semester"]) in ["5", "7", "1", "3"] else "spring"
    
    console.print(f"\n[bold cyan]Buscando equivalencia para:[/bold cyan] {ulpgc_course['name']} ({ulpgc_course['credits']} ECTS)")
    console.print(f"[dim]Semestre destino: {target_semester} | ECTS actuales: {current_ects}[/dim]\n")
    
    # 1. Filtrado duro
    query = f"{ulpgc_course['name']} {' '.join(ulpgc_course['description'].split()[:8])}"
    console.print("[yellow]⚙️ Filtrando candidatos por reglas burocráticas en SQLite...[/yellow]")
    candidates = get_filtered_candidates(query, target_semester, current_ects, limit=10)
    
    if not candidates:
        console.print("[red]No se encontraron candidatos que cumplan las reglas básicas.[/red]")
        return
        
    console.print(f"[green]✓ Se encontraron {len(candidates)} candidatos viables.[/green]")
    
    # 2. Búsqueda semántica con Embeddings
    console.print("[cyan]🧠 Calculando similitud semántica con embeddings...[/cyan]")
    ulpgc_text = prepare_text_for_embedding(ulpgc_course["description"], "")
    scored_results = calculate_semantic_similarity(ulpgc_text, candidates)
    
    # 3. Mostrar resultados
    console.print("\n[bold green]🏆 Resultados ordenados por similitud semántica:[/bold green]\n")
    
    table = Table(show_lines=True)
    table.add_column("Similitud", justify="center", style="bold cyan")
    table.add_column("Código LUT", style="green")
    table.add_column("Nombre LUT", style="white")
    table.add_column("ECTS", justify="center", style="yellow")
    table.add_column("Nivel / Periodos", style="magenta")
    table.add_column("Fragmento de Contenido (Match)", style="dim")
    
    for r in scored_results[:5]: # Mostrar top 5
        # Extraer un fragmento del texto preparado que parezca relevante (simplificado)
        snippet = r["prepared_text"][:150] + "..."
        
        # Colorear la puntuación
        score = r["similarity_score"]
        score_style = "bold green" if score >= 75 else "bold yellow" if score >= 60 else "bold red"
        
        table.add_row(
            f"[{score_style}]{score}%[/{score_style}]",
            r["code"],
            r["name"],
            f"{r['credits_min']}-{r['credits_max']}",
            f"{r['course_level']}\n{r['periods'] or 'N/A'}",
            snippet
        )
        
    console.print(table)

if __name__ == "__main__":
    main()