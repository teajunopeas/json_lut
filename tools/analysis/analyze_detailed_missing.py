import json
import re

# Cargar el archivo
with open('lut_courses.json', 'r', encoding='utf-8') as f:
    courses = json.load(f)

# Separar cursos
cursos_sin_content = [c for c in courses if 'content' not in c or c.get('content') is None or c.get('content') == '']
cursos_con_content = [c for c in courses if 'content' in c and c.get('content')]

print("="*100)
print("ANÁLISIS PROFUNDO: ¿POR QUÉ FALTAN 'content' Y 'periods'?")
print("="*100)

# 1. Comparar estrutura entre cursos con y sin content
print("\n1. COMPARACIÓN DE ESTRUCTURA")
print("-" * 100)

campos_todos = set()
for curso in courses:
    campos_todos.update(curso.keys())

print(f"Total de campos únicos en el dataset: {len(campos_todos)}")

# Campos con presencia diferenciada
print("\nCampos que SIEMPRE están (100%) en cursos SIN content:")
campos_siempre = [campo for campo in campos_todos 
                   if all(campo in c for c in cursos_sin_content)]
print(f"  {', '.join(campos_siempre)}")

print("\nCampos que NUNCA están en cursos SIN content (0%):")
campos_nunca = [campo for campo in campos_todos 
                 if not any(campo in c for c in cursos_sin_content)]
print(f"  {', '.join(campos_nunca)}")

# 2. Analizar el patrón de campos "placeholder"
print("\n\n2. CAMPOS CON TEXTOS PLACEHOLDER")
print("-" * 100)

placeholder_patterns = {
    'Details available in Completion methods': 0,
    'More details under': 0,
    'Katso tarkemmat tiedot': 0,
    'null': 0,
    'N/A': 0
}

campos_placeholder = {}

for curso in cursos_sin_content:
    for campo in ['prerequisites', 'learningMaterial', 'evaluationCriteria', 'workload']:
        valor = curso.get(campo, '')
        if valor:
            if campo not in campos_placeholder:
                campos_placeholder[campo] = {'placeholder': 0, 'contenido_real': 0, 'ejemplos': []}
            
            if isinstance(valor, str) and ('Details available' in valor or 'More details' in valor or 'Katso' in valor):
                campos_placeholder[campo]['placeholder'] += 1
            elif valor and str(valor).strip():
                campos_placeholder[campo]['contenido_real'] += 1
                if len(campos_placeholder[campo]['ejemplos']) < 2:
                    campos_placeholder[campo]['ejemplos'].append(valor[:60] + "...")

print("Campos con PLACEHOLDERS vs contenido real en cursos SIN content:")
for campo, stats in campos_placeholder.items():
    total = stats['placeholder'] + stats['contenido_real']
    if total > 0:
        print(f"  {campo:20s}: {stats['placeholder']:3d} placeholders ({stats['placeholder']*100/total:5.1f}%) | {stats['contenido_real']:3d} reales")

# 3. Analizar yearInDegree y teachingPeriods
print("\n\n3. ANÁLISIS DE yearInDegree Y teachingPeriods")
print("-" * 100)

sin_content_yearInDegree = sum(1 for c in cursos_sin_content if c.get('yearInDegree'))
sin_content_teachingPeriods = sum(1 for c in cursos_sin_content if c.get('teachingPeriods'))

con_content_yearInDegree = sum(1 for c in cursos_con_content if c.get('yearInDegree'))
con_content_teachingPeriods = sum(1 for c in cursos_con_content if c.get('teachingPeriods'))

print(f"\nCursos CON content:")
print(f"  - yearInDegree rellenado: {con_content_yearInDegree} ({con_content_yearInDegree*100/len(cursos_con_content):.1f}%)")
print(f"  - teachingPeriods rellenado: {con_content_teachingPeriods} ({con_content_teachingPeriods*100/len(cursos_con_content):.1f}%)")

print(f"\nCursos SIN content:")
print(f"  - yearInDegree rellenado: {sin_content_yearInDegree} ({sin_content_yearInDegree*100/len(cursos_sin_content):.1f}%)")
print(f"  - teachingPeriods rellenado: {sin_content_teachingPeriods} ({sin_content_teachingPeriods*100/len(cursos_sin_content):.1f}%)")

# 4. Analizar equivalentCoursesInfo (indicador de si es curso especial/alternativo)
print("\n\n4. CURSOS CON INFORMACIÓN DE EQUIVALENCIA")
print("-" * 100)

sin_content_equiv = sum(1 for c in cursos_sin_content if c.get('equivalentCoursesInfo'))
con_content_equiv = sum(1 for c in cursos_con_content if c.get('equivalentCoursesInfo'))

print(f"Cursos CON content con equivalentCoursesInfo: {con_content_equiv} ({con_content_equiv*100/len(cursos_con_content):.1f}%)")
print(f"Cursos SIN content con equivalentCoursesInfo: {sin_content_equiv} ({sin_content_equiv*100/len(cursos_sin_content):.1f}%)")

# 5. Patrones por año de curso
print("\n\n5. DISTRIBUCIÓN POR AÑO DE CURSO")
print("-" * 100)

años = {}
for curso in cursos_sin_content:
    año = curso.get('year', 'desconocido')
    if año not in años:
        años[año] = 0
    años[año] += 1

print("Top 10 años con más cursos SIN content:")
for año, cantidad in sorted(años.items(), key=lambda x: x[1], reverse=True)[:10]:
    print(f"  {año}: {cantidad} cursos")

# 6. Análisis de lenguaje
print("\n\n6. DISTRIBUCIÓN POR IDIOMA")
print("-" * 100)

idiomas_sin = {}
idiomas_con = {}

for curso in cursos_sin_content:
    idioma = curso.get('languageOfLearning', 'unknown')
    idiomas_sin[idioma] = idiomas_sin.get(idioma, 0) + 1

for curso in cursos_con_content:
    idioma = curso.get('languageOfLearning', 'unknown')
    idiomas_con[idioma] = idiomas_con.get(idioma, 0) + 1

print("Idiomas en cursos SIN content:")
for idioma in sorted(idiomas_sin.keys()):
    porc_sin = idiomas_sin[idioma] * 100 / len(cursos_sin_content)
    porc_con = idiomas_con.get(idioma, 0) * 100 / len(cursos_con_content) if len(cursos_con_content) > 0 else 0
    print(f"  {idioma:2s}: {idiomas_sin[idioma]:4d} ({porc_sin:5.1f}%) | vs CON content: ({porc_con:5.1f}%)")

# 7. Conclusión - Guardar muestra de 25 ejemplos variados
print("\n\n7. GUARDANDO MUESTRAS...")
print("-" * 100)

# Muestra aleatoria de 25 cursos sin content con todos sus campos
import random
muestra_indices = random.sample(range(len(cursos_sin_content)), min(25, len(cursos_sin_content)))
muestra = [cursos_sin_content[i] for i in sorted(muestra_indices)]

with open('cursos_sin_content_25_muestra.json', 'w', encoding='utf-8') as f:
    json.dump(muestra, f, indent=2, ensure_ascii=False)

print(f"✓ Guardado: cursos_sin_content_25_muestra.json (25 ejemplos aleatorios)")

# Guardar estadísticas en JSON
estadisticas = {
    "resumen": {
        "total_cursos": len(courses),
        "cursos_con_content": len(cursos_con_content),
        "cursos_sin_content": len(cursos_sin_content),
        "porcentaje_sin_content": f"{len(cursos_sin_content)*100/len(courses):.1f}%"
    },
    "campos_analizados": {
        "siempre_presentes": campos_siempre,
        "nunca_presentes": campos_nunca
    },
    "campos_con_placeholders": campos_placeholder,
    "distribucion_por_año": años,
    "idiomas": {
        "sin_content": idiomas_sin,
        "con_content": idiomas_con
    }
}

with open('estadisticas_missing_content.json', 'w', encoding='utf-8') as f:
    json.dump(estadisticas, f, indent=2, ensure_ascii=False)

print("✓ Guardado: estadisticas_missing_content.json")
