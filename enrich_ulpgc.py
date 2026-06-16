"""Enriquece ulpgc_courses.json con campos imprescindibles: university, type, area."""

import json

# Mapeo manual de asignaturas a áreas temáticas
AREA_MAP = {
    "49188": "Matemáticas",    # Análisis Matemático III
    "49190": "Física",          # Electromagnetismo y Óptica Física II
    "49189": "Estadística",     # Estadística
    "49191": "Física",          # Fundamentos de Mecánica Cuántica
    "49192": "Matemáticas",     # Métodos Matemáticos y sus Aplicaciones II
    "49201": "Computación",     # Aprendizaje Profundo
    "49193": "Física",          # Estado Sólido y Materiales
    "49195": "Física",          # Física de Fluidos y Fenómenos de Transporte
    "49202": "Física",          # Física de Plasmas y Aplicaciones Tecnológicas
    "49203": "Física",          # Física del Océano
    "49204": "Estadística",     # Inferencia Estadística
    "49194": "Ingeniería",      # Instrumentación y Medida
    "49196": "Matemáticas",     # Métodos Matemáticos y sus Aplicaciones III
    "49197": "Matemáticas",     # Análisis Matemático IV
    "49205": "Ingeniería",      # Diseño de Gemelos Digitales Medioambientales
    "49206": "Ingeniería",      # Dispositivos Fotónicos
    "49207": "Física",          # Física de las Radiaciones Ionizantes
    "49200": "Física",          # Física Estadística y Sistemas Complejos
    "49198": "Física",          # Mecánica Cuántica Avanzada y sus Tecnologías
    "49208": "Estadística",     # Métodos Estadísticos Multivariantes
    "49199": "Ingeniería",      # Proyectos de Ingeniería
    "49209": "Computación",     # Computación Cuántica
    "49210": "Estadística",     # Estadística Bayesiana
    "49211": "Ingeniería",      # Modelado de Sistemas Físicos de Alta Densidad de Energía
    "49212": "Ingeniería",      # Redes Complejas
    "49213": "Ingeniería",      # Prácticas Externas
    "49214": "Ingeniería",      # Trabajo Fin de Grado
}

with open("ulpgc_courses.json", "r", encoding="utf-8") as f:
    courses = json.load(f)

for course in courses:
    # Añadir universidad
    course["university"] = "ULPGC"
    
    # Convertir isOptional a type
    course["type"] = "optativa" if course.get("isOptional", False) else "obligatoria"
    
    # Asignar área temática
    course_code = course.get("code")
    course["area"] = AREA_MAP.get(course_code, "Otros")
    
    # Eliminar el campo original isOptional (opcional)
    if "isOptional" in course:
        del course["isOptional"]

# Guardar el JSON enriquecido
with open("ulpgc_courses.json", "w", encoding="utf-8") as f:
    json.dump(courses, f, indent=2, ensure_ascii=False)

print(f"✓ Enriquecido: {len(courses)} asignaturas")
print("Campos añadidos: university, type, area")
print("Campo eliminado: isOptional")
