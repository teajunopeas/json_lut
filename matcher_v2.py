#!/usr/bin/env python3
"""
matcher_v2.py - Busqueda inteligente: Keywords + Embeddings Semanticos
Versi n completa con los 27 cursos ULPGC
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

# KEYWORD_MAP para los 27 cursos ULPGC (traducidos al ingles)
KEYWORD_MAP = {
    "49188": {
        "name": "Analisis Matematico III",
        "keywords": ["complex analysis", "complex numbers", "cauchy theorem", "residues", 
                    "fourier series", "functions", "integration", "complex variables"]
    },
    "49190": {
        "name": "Electromagnetismo y Optica Fisica II",
        "keywords": ["electromagnetic waves", "propagation", "radiation", "diffraction", 
                    "interference", "laser", "optics", "coherence"]
    },
    "49189": {
        "name": "Estadistica",
        "keywords": ["statistics", "regression", "analysis", "variance", "linear model", 
                    "hypothesis testing", "bayesian", "inference"]
    },
    "49191": {
        "name": "Fundamentos de Mecanica Cuantica",
        "keywords": ["quantum mechanics", "schrodinger", "operators", "wave function", 
                    "perturbation theory", "variational method", "eigenvalues"]
    },
    "49192": {
        "name": "Metodos Matematicos II",
        "keywords": ["differential equations", "partial differential", "fourier series", 
                    "laplace transform", "wave equation", "heat equation", "separation variables"]
    },
    "49201": {
        "name": "Aprendizaje Profundo",
        "keywords": ["deep learning", "neural networks", "convolutional", "machine learning", 
                    "automatic", "architectures", "training", "optimization"]
    },
    "49193": {
        "name": "Estado Solido y Materiales",
        "keywords": ["solid state", "materials", "crystal structure", "crystalline", 
                    "defects", "properties", "lattice", "semiconductors"]
    },
    "49195": {
        "name": "Fisica de Fluidos y Transporte",
        "keywords": ["fluid mechanics", "fluid dynamics", "transport phenomena", "flow", 
                    "navier stokes", "dimensional analysis", "similitude", "turbulence"]
    },
    "49202": {
        "name": "Fisica de Plasmas y Aplicaciones",
        "keywords": ["plasma physics", "plasma", "equilibrium", "electromagnetic", 
                    "thermodynamic", "ionization", "magnetic confinement"]
    },
    "49203": {
        "name": "Fisica del Oceano",
        "keywords": ["oceanography", "ocean physics", "geostrophic", "hydrodynamics", 
                    "waves", "circulation", "dynamics", "water"]
    },
    "49204": {
        "name": "Inferencia Estadistica",
        "keywords": ["statistical inference", "estimation", "hypothesis testing", 
                    "confidence intervals", "likelihood", "neyman pearson", "tests"]
    },
    "49194": {
        "name": "Instrumentacion y Medida",
        "keywords": ["instrumentation", "measurement", "sensors", "transducers", 
                    "signal processing", "acquisition", "virtual instruments"]
    },
    "49196": {
        "name": "Metodos Matematicos III",
        "keywords": ["finite element", "numerical methods", "finite difference", 
                    "discretization", "weak solution", "galerkin", "fem", "variational"]
    },
    "49197": {
        "name": "Analisis Matematico IV",
        "keywords": ["measure theory", "integration", "lebesgue", "convergence", 
                    "measurable sets", "real analysis", "functions", "trigonometric"]
    },
    "49205": {
        "name": "Diseno Gemelos Digitales Medioambientales",
        "keywords": ["digital twins", "models", "environmental", "remote sensing", 
                    "geographic information", "simulation", "data assimilation"]
    },
    "49206": {
        "name": "Dispositivos Fotonico",
        "keywords": ["photonic devices", "photodetectors", "solar cells", "lasers", 
                    "semiconductors", "light emission", "optical", "photonics"]
    },
    "49207": {
        "name": "Fisica Radiaciones Ionizantes",
        "keywords": ["ionizing radiation", "radioactivity", "nuclear", "dosimetry", 
                    "particle", "interactions", "shielding", "detection"]
    },
    "49200": {
        "name": "Fisica Estadistica y Sistemas Complejos",
        "keywords": ["statistical physics", "complex systems", "phase transitions", 
                    "critical phenomena", "fluctuations", "ensembles", "thermodynamics"]
    },
    "49198": {
        "name": "Mecanica Cuantica Avanzada",
        "keywords": ["quantum field theory", "quantum information", "entanglement", 
                    "quantum computing", "quantum technology", "quantum communication"]
    },
    "49208": {
        "name": "Metodos Estadisticos Multivariantes",
        "keywords": ["multivariate analysis", "principal components", "regression", 
                    "classification", "clustering", "factor analysis", "linear models"]
    },
    "49199": {
        "name": "Proyectos Ingenieria",
        "keywords": ["engineering projects", "project management", "design", "planning", 
                    "resource management", "control", "scheduling"]
    },
    "49209": {
        "name": "Computacion Cuantica",
        "keywords": ["quantum computing", "quantum algorithms", "quantum computers", 
                    "quantum gates", "machine learning", "quantum applications"]
    },
    "49210": {
        "name": "Estadistica Bayesiana",
        "keywords": ["bayesian inference", "bayesian statistics", "priors", "posterior", 
                    "mcmc", "sampling", "linear models", "data analysis"]
    },
    "49211": {
        "name": "Modelado Sistemas Fisicos Alta Densidad",
        "keywords": ["plasma simulation", "numerical methods", "equations", "radiation", 
                    "high density", "interactions", "modeling"]
    },
    "49212": {
        "name": "Redes Complejas",
        "keywords": ["complex networks", "network analysis", "metrics", "models", 
                    "processes", "structure", "nodes", "resilience"]
    },
    "49213": {
        "name": "Practicas Externas",
        "keywords": ["internship", "practical experience", "applied", "professional", 
                    "external", "real world", "practical training"]
    },
    "49214": {
        "name": "Trabajo Fin Grado",
        "keywords": ["final project", "thesis", "engineering project", "planning", 
                    "development", "research", "documentation"]
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
    
    # Mostrar menu de cursos
    console.print("\n[bold cyan]CURSOS DISPONIBLES ULPGC:[/bold cyan]\n")
    
    courses_dict = {c["code"]: c for c in ulpgc_data}
    codes = list(KEYWORD_MAP.keys())
    
    # Mostrar en 2 columnas
    for i in range(0, len(codes), 2):
        line = ""
        for j in range(2):
            if i + j < len(codes):
                code = codes[i + j]
                name = KEYWORD_MAP[code]["name"]
                line += f"{i+j+1:2d}. {code} - {name:<45s}  "
        console.print(line)
    
    # Pedir seleccion
    console.print("\n")
    try:
        choice = int(input("Selecciona numero de curso (1-27, o 0 para todos): "))
        if choice < 0 or choice > len(codes):
            console.print("[red]Opcion invalida[/red]")
            return
    except ValueError:
        console.print("[red]Entrada invalida[/red]")
        return
    
    # Determinar cursos a procesar
    if choice == 0:
        selected_codes = codes
    else:
        selected_codes = [codes[choice - 1]]
    
    # Procesar cada curso seleccionado
    for selected_code in selected_codes:
        # Obtener datos del curso seleccionado
        course = courses_dict[selected_code]
        config = KEYWORD_MAP[selected_code]
        keywords = config["keywords"]
        
        console.print(f"\n[bold cyan]{'='*80}[/bold cyan]")
        console.print(f"[bold]{config['name']} ({course['credits']} ECTS)[/bold]")
        console.print(f"[dim]Codigo: {selected_code} | Area: {course.get('area', 'N/A')}[/dim]")
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
        console.print("\n[bold green]RESULTADOS - Top 10:[/bold green]\n")
        
        table = Table(show_lines=True)
        table.add_column("Similitud", justify="center", style="bold cyan", width=10)
        table.add_column("Codigo", style="green", width=12)
        table.add_column("Nombre", style="white", width=45)
        table.add_column("ECTS", justify="center", width=6)
        table.add_column("Nivel", style="magenta", width=12)
        
        for r in scored[:10]:
            score = r["similarity_score"]
            style = "bold green" if score >= 60 else "bold yellow" if score >= 50 else "dim"
            
            table.add_row(
                f"[{style}]{score}%[/{style}]",
                r["code"],
                r["name"][:44],
                f"{r['credits_min']}-{r['credits_max']}",
                r["course_level"] or "N/A"
            )
        
        console.print(table)
        console.print()

if __name__ == "__main__":
    main()
