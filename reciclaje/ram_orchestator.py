"""
Paso 2: Orquestador del RAM con Agente Local (Ollama).
Aplica reglas burocráticas estrictas (150 ECTS, fraccionamiento) y usa Qwen 2.5 para el razonamiento de contenidos.
"""
import json
import sqlite3
import requests
from pathlib import Path
from typing import List, Dict, Any
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()
DB_PATH = Path("lut_courses.db")
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "qwen2.5:7b" # o "qwen2.5:14b"

# ==========================================
# 1. GESTIÓN DEL ESTADO (Memoria del Agente)
# ==========================================
class ULPGCCourse:
    def __init__(self, code: str, name: str, total_ects: float, semester: str, description: str):
        self.code = code
        self.name = name
        self.total_ects = float(total_ects)
        self.remaining_ects = float(total_ects)
        self.semester = semester
        self.description = description
        self.matches: List[Dict[str, Any]] = []

    def consume_ects(self, amount: float, lut_code: str, lut_name: str, reasoning: str, overlap: int):
        if amount > self.remaining_ects:
            raise ValueError(f"Error: Intentando consumir {amount} ECTS, pero solo quedan {self.remaining_ects} en {self.code}")
        self.remaining_ects -= amount
        self.matches.append({
            "lut_code": lut_code,
            "lut_name": lut_name,
            "contributed_ects": amount,
            "reasoning": reasoning,
            "overlap": overlap
        })

class RAMState:
    def __init__(self, current_ects: int):
        self.current_ects = current_ects
        self.ulpgc_courses: Dict[str, ULPGCCourse] = {}
        self.lut_registry: Dict[str, Dict[str, Any]] = {} # code -> {remaining_ects, level, periods}
        self.table_direct = []
        self.table_fractional = []

    def add_ulpgc(self, code, name, ects, semester, desc):
        self.ulpgc_courses[code] = ULPGCCourse(code, name, ects, semester, desc)

    def get_available_lut_candidates(self, query: str, target_lut_semester: str, limit: int = 6) -> List[Dict]:
        """Busca candidatos y FILTRA por la regla de los 150 ECTS si es necesario."""
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        sql = """
            SELECT code, name, credits_min, credits_max, course_level, periods, content, learning_outcomes
            FROM courses WHERE courses MATCH ? ORDER BY rank LIMIT ?
        """
        cursor = conn.execute(sql, (query, limit * 3))
        candidates = []
        
        for row in cursor.fetchall():
            code = row["code"]
            level = (row["course_level"] or "").lower()
            
            # --- REGLA DE ORO DE LOS 150 ECTS ---
            is_master = "master" in level or "advanced" in level
            
            # Semestres de otoño en ULPGC suelen ser 5 y 7. LUT periodos 1 y 2.
            if target_lut_semester == "autumn" and self.current_ects < 150 and is_master:
                continue  # ¡FILTRO DURO! La IA nunca verá este curso.
            
            # Gestión de ECTS restantes en LUT
            if code in self.lut_registry:
                rem_ects = self.lut_registry[code]["remaining_ects"]
                if rem_ects <= 0.5:
                    continue
                row_dict = dict(row)
                row_dict["available_ects"] = rem_ects
                candidates.append(row_dict)
            else:
                row_dict = dict(row)
                row_dict["available_ects"] = float(row["credits_max"])
                candidates.append(row_dict)
        
        conn.close()
        return candidates[:limit]

    def lock_lut_ects(self, lut_code: str, consumed: float, level: str, periods: str):
        if lut_code not in self.lut_registry:
            self.lut_registry[lut_code] = {"remaining_ects": consumed, "level": level, "periods": periods}
        else:
            self.lut_registry[lut_code]["remaining_ects"] -= consumed

# ==========================================
# 2. EL CEREBRO (LLM con Ollama)
# ==========================================
def evaluate_match(ulpgc: ULPGCCourse, lut_candidates: List[Dict], state: RAMState, target_lut_semester: str) -> List[Dict]:
    candidates_text = ""
    for i, c in enumerate(lut_candidates, 1):
        candidates_text += f"""
Candidato #{i}: {c['code']} - {c['name']}
- ECTS DISPONIBLES PARA ASIGNAR: {c['available_ects']}
- Nivel: {c['course_level'] or 'N/A'} | Periodos LUT: {c['periods'] or 'N/A'}
- Contenidos: {c['content'][:600]}...
- Resultados de Aprendizaje: {c['learning_outcomes'][:400]}...
---"""

    level_warning = ""
    if target_lut_semester == "autumn":
        if state.current_ects < 150:
            level_warning = "⚠️ REGLA ACTIVA: El estudiante tiene < 150 ECTS. En el 1er semestre (Otoño) NO se permiten asignaturas de nivel Master. Solo se han proporcionado candidatos Bachelor/Intermediate."
        else:
            level_warning = "✅ El estudiante tiene >= 150 ECTS, por lo que las asignaturas de nivel Master en el 1er semestre están permitidas."
    else:
        level_warning = "✅ Es el 2do semestre (Primavera), las asignaturas de nivel Master están permitidas."

    prompt = f"""
Eres un coordinador académico experto de la ULPGC evaluando un RAM para LUT.
La asignatura de origen necesita cubrir {ulpgc.remaining_ects} ECTS.

**ASIGNATURA DE ORIGEN (ULPGC):** {ulpgc.name} ({ulpgc.code})
- ECTS a cubrir: {ulpgc.remaining_ects}
- Semestre ULPGC: {ulpgc.semester}
- Contenidos/Objetivos: {ulpgc.description[:800]}

**CANDIDATOS EN LUT (Semestre destino: {target_lut_semester}):**
{candidates_text}

**REGLAS Burocráticas ESTRICTAS:**
1. {level_warning}
2. FRACCIONAMIENTO: Una asignatura de LUT puede repartir sus ECTS entre varias de la ULPGC. Ej: Un curso de 6 ECTS en LUT puede aportar 4.5 ECTS a la asignatura A y 1.5 ECTS a la B.
3. La suma de 'contributed_ects' que asignes a esta asignatura ULPGC NO puede superar los {ulpgc.remaining_ects} ECTS que le faltan.
4. No puedes asignar más ECTS de los 'ECTS DISPONIBLES' de cada candidato de LUT.
5. Exige al menos 75% de solapamiento temático (contenidos o resultados de aprendizaje) para asignaturas obligatorias.

**FORMATO JSON (Array):**
[
  {{
    "lut_code": "CÓDIGO",
    "contributed_ects": 4.5,
    "overlap_percentage": 80,
    "reasoning": "Cubre ecuaciones de Maxwell y propagación de ondas. Se asignan 4.5 ECTS de este curso de 6 ECTS, quedando 1.5 ECTS disponibles para otra asignatura."
  }}
]
Devuelve SOLO el array JSON. Sin markdown, sin texto extra.
"""
    try:
        payload = {"model": MODEL_NAME, "prompt": prompt, "stream": False, "format": "json"}
        response = requests.post(OLLAMA_URL, json=payload, timeout=90)
        response.raise_for_status()
        result = response.json()["response"].strip().removeprefix("```json").removesuffix("```").strip()
        return json.loads(result)
    except Exception as e:
        console.print(f"[red]Error LLM:[/red] {e}")
        return []

# ==========================================
# 3. ORQUESTACIÓN DEL BUCLE
# ==========================================
def build_ram(ulpgc_data: List[Dict], current_ects: int):
    state = RAMState(current_ects)
    for c in ulpgc_data:
        state.add_ulpgc(c["code"], c["name"], c["ects"], c["semester"], c["desc"])

    console.print("[bold cyan]🚀 Iniciando orquestación del RAM...[/bold cyan]")
    
    for ulpgc_code, ulpgc_course in state.ulpgc_courses.items():
        if ulpgc_course.remaining_ects <= 0.1:
            continue
            
        # Mapeo simple de semestres ULPGC a temporadas LUT
        target_lut_semester = "autumn" if str(ulpgc_course.semester) in ["5", "7", "1", "3"] else "spring"
        
        console.print(f"\n[yellow]➡️  Analizando:[/yellow] {ulpgc_course.name} (Faltan {ulpgc_course.remaining_ects} ECTS, LUT: {target_lut_semester})")
        
        query = f"{ulpgc_course.name} {' '.join(ulpgc_course.description.split()[:10])}"
        candidates = state.get_available_lut_candidates(query, target_lut_semester, limit=6)
        
        if not candidates:
            console.print("  [dim]No se encontraron candidatos válidos en la DB.[/dim]")
            continue

        suggestions = evaluate_match(ulpgc_course, candidates, state, target_lut_semester)
        
        for sug in suggestions:
            lut_code = sug["lut_code"]
            proposed_ects = float(sug["contributed_ects"])
            
            lut_info = next((c for c in candidates if c["code"] == lut_code), None)
            if not lut_info:
                continue
                
            available = lut_info["available_ects"]
            needed = ulpgc_course.remaining_ects
            
            # GUARDARRAÍL DE PYTHON: La IA sugiere, pero Python limita matemáticamente
            final_ects = min(proposed_ects, available, needed)
            
            if final_ects > 0.5:
                ulpgc_course.consume_ects(
                    amount=final_ects,
                    lut_code=lut_code,
                    lut_name=lut_info["name"],
                    reasoning=sug["reasoning"],
                    overlap=sug["overlap_percentage"]
                )
                state.lock_lut_ects(lut_code, final_ects, lut_info["course_level"], lut_info["periods"])
                console.print(f"  [green]✓ Asignado:[/green] {final_ects} ECTS de {lut_code} ({lut_info['name']})")

        # Clasificar en tabla
        for match in ulpgc_course.matches:
            row_data = {
                "ulpgc_code": ulpgc_course.code,
                "ulpgc_name": ulpgc_course.name,
                "ulpgc_ects_total": ulpgc_course.total_ects,
                "lut_code": match["lut_code"],
                "lut_name": match["lut_name"],
                "contributed_ects": match["contributed_ects"],
                "overlap": match["overlap"],
                "reasoning": match["reasoning"]
            }
            if match["contributed_ects"] == ulpgc_course.total_ects and match["overlap"] >= 85:
                state.table_direct.append(row_data)
            else:
                state.table_fractional.append(row_data)

    return state

# ==========================================
# 4. GENERACIÓN DE SALIDA (Tablas para Word)
# ==========================================
def print_tables(state: RAMState):
    console.print("\n" + "="*70)
    console.print("[bold green]✅ PROCESO COMPLETADO. TABLAS GENERADAS PARA EL RAM:[/bold green]")
    console.print("="*70)

    console.print("\n[bold cyan]📋 TABLA 1: Convalidaciones Directas (1 a 1, >85% solapamiento)[/bold cyan]")
    t1 = Table(show_lines=True)
    t1.add_column("ULPGC (Código / Nombre / ECTS)", style="yellow")
    t1.add_column("LUT (Código / Nombre / ECTS)", style="green")
    t1.add_column("Justificación (75%+ Contenido)", style="white")
    for r in state.table_direct:
        t1.add_row(
            f"{r['ulpgc_code']}\n{r['ulpgc_name']}\n[r]{r['ulpgc_ects_total']} ECTS[/r]",
            f"{r['lut_code']}\n{r['lut_name']}\n[g]{r['contributed_ects']} ECTS[/g]",
            f"Solapamiento: {r['overlap']}%\n{r['reasoning'][:200]}..."
        )
    console.print(t1)

    console.print("\n[bold yellow]📋 TABLA 2: Convalidaciones Fraccionadas / Parciales[/bold yellow]")
    t2 = Table(show_lines=True)
    t2.add_column("ULPGC (Total ECTS)", style="yellow")
    t2.add_column("LUT (Contribución ECTS)", style="green")
    t2.add_column("Desglose y Justificación", style="white")
    
    from itertools import groupby
    sorted_t2 = sorted(state.table_fractional, key=lambda x: x['ulpgc_code'])
    for ulpgc_code, group in groupby(sorted_t2, key=lambda x: x['ulpgc_code']):
        items = list(group)
        ulpgc_name = items[0]['ulpgc_name']
        total_ects = items[0]['ulpgc_ects_total']
        
        lut_details = "\n".join([f"• {i['lut_code']} ({i['lut_name']}): [bold]{i['contributed_ects']} ECTS[/bold]" for i in items])
        reasoning = items[0]['reasoning'][:250] + "..."
        
        t2.add_row(
            f"[bold]{ulpgc_code}[/bold]\n{ulpgc_name}\nTotal: {total_ects} ECTS",
            lut_details,
            f"Solapamiento parcial. {reasoning}"
        )
    console.print(t2)

    console.print("\n[bold magenta]📋 ESTADO FINAL:[/bold magenta]")
    pending = [c for c in state.ulpgc_courses.values() if c.remaining_ects > 0.5]
    if pending:
        for c in pending:
            console.print(f"  ⚠️  [red]{c.code} - {c.name}[/red]: Aún faltan [bold]{c.remaining_ects} ECTS[/bold] por cubrir.")
    else:
        console.print("  [green]✓ Todas las asignaturas han sido cubiertas al 100%.[/green]")

# ==========================================
# 5. DATOS DE EJEMPLO (Extraídos de tu RAM)
# ==========================================
if __name__ == "__main__":
    # Aquí puedes pegar tus 14 asignaturas reales. He puesto 3 de ejemplo.
    MIS_ASIGNATURAS_ULPGC = [
        {
            "code": "49189", "name": "Estadística", "ects": 6, "semester": "5", 
            "desc": "Reconocer, plantear y resolver problemas estadísticos. Manejar e interpretar correctamente el grado de relación entre variables. Dominar las principales propiedades de los estimadores y los métodos básicos de construcción de los mismos. Construir, interpretar y utilizar intervalos de confianza y contrastes de hipótesis."
        },
        {
            "code": "49192", "name": "Métodos Matemáticos y sus Aplicaciones II", "ects": 3, "semester": "5", 
            "desc": "Identificar las ecuaciones en derivadas parciales clásicas de la física matemática: ecuación de transporte, ecuación del calor, ecuación de ondas y ecuación de Laplace. Utilizar el método de las características para las EDOs de orden 1. Aplicar el método de separación de variables y operar formalmente con series de Fourier."
        },
        {
            "code": "49186", "name": "Electromagnetismo y Óptica Física II", "ects": 6, "semester": "6", 
            "desc": "Comprender los principios de la propagación de las ondas electromagnéticas por medios y de la radiación. Dominar los principios de interacción materia-campo electromagnético. Comprender los procesos de interferencia y difracción, redes de difracción, interferómetros. Radiación láser y sus aplicaciones."
        }
    ]

    # PRUEBA: Cambia current_ects a 145 o 155 para ver cómo cambia el comportamiento
    estado_final = build_ram(MIS_ASIGNATURAS_ULPGC, current_ects=155)
    print_tables(estado_final)