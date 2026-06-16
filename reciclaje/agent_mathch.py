"""
Agente de Emparejamiento de Cursos v2 (Optimizado para Normativa ULPGC/LUT)
Maneja créditos fraccionados, regla de los 158 ECTS y comparación de contenidos al 75%.
"""
import argparse
import json
import sqlite3
import requests
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

console = Console()
DB_PATH = Path("lut_courses_agent.db")
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3" # o "qwen2.5:7b"

def get_candidates(query: str, limit: int = 6) -> list:
    """Busca candidatos en la DB usando FTS5."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    sql = """
        SELECT code, name, credits_min, credits_max, course_level, language, periods, 
               is_exchange, learning_outcomes, content, equivalent_courses
        FROM courses 
        WHERE courses MATCH ? 
        ORDER BY rank 
        LIMIT ?
    """
    cursor = conn.execute(sql, (query, limit))
    results = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return results

def evaluate_match(home_course: dict, lut_candidates: list, current_ects: int, target_semester: str) -> str:
    """Envía los datos a Ollama para una evaluación burocrática estricta."""
    
    candidates_text = ""
    for i, c in enumerate(lut_candidates, 1):
        candidates_text += f"""
CANDIDATO LUT #{i}: {c['code']} - {c['name']}
- Créditos totales: {c['credits_min']} a {c['credits_max']} ECTS
- Nivel: {c['course_level']} | Idioma: {c['language']} | Periodos LUT: {c['periods'] or 'No especificado'}
- Equivalencias declaradas por LUT: {c['equivalent_courses'] or 'Ninguna'}
- Contenidos LUT: {c['content'][:600]}...
- Resultados de Aprendizaje LUT: {c['learning_outcomes'][:400]}...
---"""

    # Determinamos si aplica la restricción de los 158 ECTS
    ects_warning = ""
    if current_ects < 158 and target_semester.lower() in ["autumn", "1", "2"]:
        ects_warning = "⚠️ RESTRICCIÓN ACTIVA: El estudiante tiene menos de 158 ECTS. En Periodos 1 y 2, las asignaturas de nivel 'Master' están RESTRINGIDAS y deben ser justificadas excepcionalmente o descartadas."

    prompt = f"""
Eres un experto coordinador de movilidad académica (Erasmus) de la ULPGC evaluando un RAM (Reconocimiento de Asignaturas).

**ASIGNATURA DE ORIGEN (ULPGC):**
- Nombre: {home_course['name']}
- Créditos: {home_course['credits']} ECTS
- Semestre ULPGC: {home_course['semester']}
- Contenidos y Resultados de Aprendizaje: {home_course['description']}

**CANDIDATOS EN DESTINO (LUT):**
{candidates_text}

**REGLAS BUROCRÁTICAS ESTRICTAS:**
1. {ects_warning}
2. COINCIDENCIA DEL 75%: Evalúa si los Contenidos o Resultados de Aprendizaje se solapan al menos en un 75%. Los contenidos detallados suelen ser más fiables que los resultados de aprendizaje breves.
3. CRÉDITOS FRACCIONADOS: Una asignatura de LUT puede cubrir solo una PARTE de la asignatura de la ULPGC (ej: un curso de 6 ECTS en LUT puede cubrir 4.5 ECTS de uno de 6 ECTS en la ULPGC). Si es así, debes especificar cuántos ECTS de la ULPGC cubre.
4. PERIODOS: El periodo de impartición en LUT no tiene por qué coincidir exactamente con el semestre de la ULPGC, pero debe ser lógicamente compatible (ej: un curso de 1er semestre en LUT puede convalidar un curso de 1er o 2do semestre en ULPGC).

**FORMATO DE RESPUESTA:**
Devuelve SOLO un array JSON válido. Sin texto antes ni después. Estructura:
[
  {{
    "code": "CÓDIGO_LUT",
    "match_percentage": 85,
    "suggested_ects_contribution": "4.5/6", 
    "verdict": "RECOMENDADO" | "PARCIAL (NECESITA COMPLEMENTO)" | "NO RECOMENDADO",
    "reasoning": "Explicación clara de por qué se alcanza el 75% de similitud, mencionando temas específicos compartidos (ej: 'ambos cubren ecuaciones de Maxwell y propagación de ondas').",
    "warnings": ["Lista de advertencias, ej: 'Nivel Master con <158 ECTS en periodo 1'", 'El curso es de 3 ECTS, faltan 3 ECTS para convalidar los 6 de origen']
  }}
]
"""
    try:
        payload = {
            "model": MODEL_NAME,
            "prompt": prompt,
            "stream": False,
            "format": "json"
        }
        response = requests.post(OLLAMA_URL, json=payload, timeout=90)
        response.raise_for_status()
        result = response.json()["response"]
        return result.strip().removeprefix("```json").removesuffix("```").strip()
    except Exception as e:
        return f"ERROR: {e}"

def main():
    parser = argparse.ArgumentParser(description="Agente de emparejamiento RAM ULPGC-LUT v2")
    parser.add_argument("--name", required=True, help="Nombre de la asignatura de la ULPGC")
    parser.add_argument("--credits", type=int, required=True, help="Créditos ECTS de la asignatura ULPGC")
    parser.add_argument("--desc", required=True, help="Contenidos y resultados de aprendizaje de la asignatura ULPGC")
    parser.add_argument("--semester", required=True, help="Semestre en la ULPGC (ej: '5', '6', '7')")
    parser.add_argument("--current-ects", type=int, default=150, help="ECTS totales aprobados actualmente por el estudiante")
    parser.add_argument("--limit", type=int, default=5, help="Número de candidatos a evaluar")
    
    args = parser.parse_args()

    if not DB_PATH.exists():
        console.print("[red]Error:[/red] Ejecuta primero `python agent_db.py` para crear la base de datos.")
        return

    console.print(f"[bold cyan]Analizando convalidación para:[/bold cyan] {args.name} ({args.credits} ECTS, Semestre {args.semester})")
    console.print(f"[dim]ECTS acumulados: {args.current_ects} | Restricción <158 ECTS: {'[red]ACTIVA[/red]' if args.current_ects < 158 else '[green]NO APLICA[/green]'}[/dim]\n")
    
    # 1. Recuperación
    query = f"{args.name}"
    candidates = get_candidates(query, limit=args.limit + 2) # Pedimos un poco más para que el LLM tenga donde elegir
    
    if not candidates:
        console.print("[yellow]No se encontraron candidatos en la base de datos. Prueba con palabras clave en inglés.[/yellow]")
        return

    # 2. Evaluación del Agente
    home_course = {
        "name": args.name,
        "credits": args.credits,
        "semester": args.semester,
        "description": args.desc
    }
    
    console.print("[cyan]🧠 El agente está comparando contenidos y calculando créditos fraccionados...[/cyan]\n")
    result_json = evaluate_match(home_course, candidates, args.current_ects, args.semester)
    
    try:
        results = json.loads(result_json)
        for r in results:
            score = r.get("match_percentage", 0)
            color = "green" if score >= 75 else "yellow" if score >= 50 else "red"
            verdict = r.get("verdict", "DESCONOCIDO")
            
            warnings = "\n".join([f"  ⚠️ {w}" for w in r.get("warnings", [])]) if r.get("warnings") else "  ✅ Sin advertencias críticas"
            
            panel_content = f"""
**Coincidencia:** [{color}]{score}%[/{color}] | **Veredicto:** {verdict}
**Contribución sugerida:** `{r.get('suggested_ects_contribution', 'No especificada')}` ECTS

**Razonamiento del Agente:**
{r.get('reasoning', 'Sin razonamiento')}

**Advertencias:**
{warnings}
"""
            console.print(Panel(panel_content, title=f"{r.get('code')} - {r.get('name', 'Candidato')}", border_style=color, expand=False))
            console.print()
            
    except json.JSONDecodeError:
        console.print(f"[red]Error al procesar la respuesta del LLM. Respuesta cruda:[/red]\n{result_json}")

if __name__ == "__main__":
    main()