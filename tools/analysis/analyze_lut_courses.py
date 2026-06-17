import json
from collections import defaultdict, Counter
from pathlib import Path

# Load the JSON file
json_path = Path('lut_courses.json')
with open(json_path, 'r', encoding='utf-8') as f:
    courses = json.load(f)

print("=" * 80)
print("ANÁLISIS ESTADÍSTICO DEL ARCHIVO lut_courses.json")
print("=" * 80)

# 1. Total de cursos
total_courses = len(courses)
print(f"\n1. TOTAL DE CURSOS: {total_courses}")

# 2. Análisis de 'content'
content_empty = 0
content_null = 0
content_missing = 0
content_valid = 0

for course in courses:
    if 'content' not in course:
        content_missing += 1
    elif course['content'] is None:
        content_null += 1
    elif isinstance(course['content'], str) and course['content'].strip() == '':
        content_empty += 1
    else:
        content_valid += 1

print(f"\n2. ANÁLISIS DEL CAMPO 'content':")
print(f"   - Con contenido válido: {content_valid} ({content_valid/total_courses*100:.1f}%)")
print(f"   - Vacío (string vacío): {content_empty} ({content_empty/total_courses*100:.1f}%)")
print(f"   - Nulo (null): {content_null} ({content_null/total_courses*100:.1f}%)")
print(f"   - Faltante (campo no existe): {content_missing} ({content_missing/total_courses*100:.1f}%)")
print(f"   - TOTAL SIN CONTENIDO: {content_empty + content_null + content_missing} ({(content_empty + content_null + content_missing)/total_courses*100:.1f}%)")

# 3. Análisis de 'learningOutcomes'
outcomes_empty = 0
outcomes_null = 0
outcomes_missing = 0
outcomes_valid = 0

for course in courses:
    if 'learningOutcomes' not in course:
        outcomes_missing += 1
    elif course['learningOutcomes'] is None:
        outcomes_null += 1
    elif isinstance(course['learningOutcomes'], str) and course['learningOutcomes'].strip() == '':
        outcomes_empty += 1
    else:
        outcomes_valid += 1

print(f"\n3. ANÁLISIS DEL CAMPO 'learningOutcomes':")
print(f"   - Con contenido válido: {outcomes_valid} ({outcomes_valid/total_courses*100:.1f}%)")
print(f"   - Vacío (string vacío): {outcomes_empty} ({outcomes_empty/total_courses*100:.1f}%)")
print(f"   - Nulo (null): {outcomes_null} ({outcomes_null/total_courses*100:.1f}%)")
print(f"   - Faltante (campo no existe): {outcomes_missing} ({outcomes_missing/total_courses*100:.1f}%)")
print(f"   - TOTAL SIN OUTCOMES: {outcomes_empty + outcomes_null + outcomes_missing} ({(outcomes_empty + outcomes_null + outcomes_missing)/total_courses*100:.1f}%)")

# 4. Cursos sin NINGUNO de los dos campos
without_both = 0
without_both_list = []

for course in courses:
    has_content = ('content' in course and 
                   course['content'] is not None and 
                   isinstance(course['content'], str) and 
                   course['content'].strip() != '')
    
    has_outcomes = ('learningOutcomes' in course and 
                    course['learningOutcomes'] is not None and 
                    isinstance(course['learningOutcomes'], str) and 
                    course['learningOutcomes'].strip() != '')
    
    if not has_content and not has_outcomes:
        without_both += 1
        without_both_list.append(course)

print(f"\n4. CURSOS SIN NINGUNO DE LOS DOS CAMPOS (content Y learningOutcomes):")
print(f"   - Total: {without_both} ({without_both/total_courses*100:.1f}%)")

# 5. Detectar duplicados
print(f"\n5. ANÁLISIS DE DUPLICADOS:")

# Duplicados por 'code'
code_counter = Counter([c.get('code', 'MISSING') for c in courses])
duplicate_codes = {code: count for code, count in code_counter.items() if count > 1}

if duplicate_codes:
    print(f"   - Cursos con código DUPLICADO: {len(duplicate_codes)}")
    for code, count in list(duplicate_codes.items())[:5]:
        print(f"     • {code}: {count} cursos")
else:
    print(f"   - Cursos con código DUPLICADO: 0")

# Duplicados por 'name'
name_counter = Counter([c.get('name', 'MISSING') for c in courses])
duplicate_names = {name: count for name, count in name_counter.items() if count > 1}

if duplicate_names:
    print(f"   - Cursos con nombre DUPLICADO: {len(duplicate_names)}")
    for name, count in list(duplicate_names.items())[:5]:
        print(f"     • '{name[:60]}...': {count} cursos")
else:
    print(f"   - Cursos con nombre DUPLICADO: 0")

# 6. Ejemplos de cursos sin contenido
print(f"\n6. EJEMPLOS DE CURSOS SIN CONTENIDO (mostrando campos presentes):")
print(f"   (Limitado a los primeros 3 ejemplos)\n")

for i, course in enumerate(without_both_list[:3]):
    print(f"   Ejemplo {i+1}:")
    print(f"   - code: {course.get('code', 'N/A')}")
    print(f"   - name: {course.get('name', 'N/A')}")
    print(f"   - courseLevel: {course.get('courseLevel', 'N/A')}")
    print(f"   - credits: {course.get('credits', 'N/A')}")
    print(f"   - year: {course.get('year', 'N/A')}")
    print(f"   - content: {repr(course.get('content', 'MISSING'))}")
    print(f"   - learningOutcomes: {repr(course.get('learningOutcomes', 'MISSING'))}")
    
    # Mostrar qué campos SÍ tienen contenido
    fields_with_content = []
    for key, value in course.items():
        if key not in ['content', 'learningOutcomes', 'id']:
            if value is not None and (not isinstance(value, str) or value.strip() != ''):
                fields_with_content.append(key)
    
    print(f"   - Campos con contenido: {', '.join(fields_with_content[:8])}")
    print()

# 7. Conclusiones y estadísticas finales
print("=" * 80)
print("7. CONCLUSIONES Y ESTADÍSTICAS FINALES:")
print("=" * 80)

# Calcular el grado de completitud
content_completeness = (content_valid / total_courses) * 100
outcomes_completeness = (outcomes_valid / total_courses) * 100

print(f"\nGRADO DE COMPLETITUD:")
print(f"   - Content: {content_completeness:.1f}% completos")
print(f"   - Learning Outcomes: {outcomes_completeness:.1f}% completos")
print(f"   - Promedio: {(content_completeness + outcomes_completeness)/2:.1f}% completos")

print(f"\nDIAGNÓSTICO:")

if without_both == 0:
    print(f"   ✓ Todos los cursos tienen al menos un campo (content O learningOutcomes)")
else:
    print(f"   ✗ {without_both} cursos ({without_both/total_courses*100:.1f}%) carecen de AMBOS campos")

if content_completeness > 95:
    print(f"   ✓ Content está muy completo")
elif content_completeness > 80:
    print(f"   ~ Content tiene cobertura moderada")
else:
    print(f"   ✗ Content tiene baja cobertura - posible problema de scraping")

if outcomes_completeness > 95:
    print(f"   ✓ Learning Outcomes está muy completo")
elif outcomes_completeness > 80:
    print(f"   ~ Learning Outcomes tiene cobertura moderada")
else:
    print(f"   ✗ Learning Outcomes tiene baja cobertura - posible problema de scraping")

if not duplicate_codes and not duplicate_names:
    print(f"   ✓ Sin duplicados detectados")
else:
    print(f"   ✗ Se detectaron duplicados")

print(f"\nINTERPRETACIÓN:")
if content_completeness < 80 or outcomes_completeness < 80:
    print(f"   → CONCLUSIÓN: Es probable un PROBLEMA DE SCRAPING INCOMPLETO")
    print(f"     El scraper puede estar con timeouts, errores de parsing parcial,")
    print(f"     o limitaciones en la extracción de algunos campos.")
else:
    print(f"   → CONCLUSIÓN: Parece ser que EL JSON ORIGINAL VIENE INCOMPLETO")
    print(f"     (O el sitio origen tiene campos vacíos inherentemente)")

print("\n" + "=" * 80)
