import json
from collections import Counter

# Cargar el archivo
with open('lut_courses.json', 'r', encoding='utf-8') as f:
    courses = json.load(f)

print(f"Total de cursos: {len(courses)}")

# Separar cursos con y sin content
cursos_sin_content = [c for c in courses if 'content' not in c or c.get('content') is None or c.get('content') == '']
cursos_con_content = [c for c in courses if 'content' in c and c.get('content')]

print(f"Cursos con content: {len(cursos_con_content)} ({len(cursos_con_content)*100/len(courses):.1f}%)")
print(f"Cursos SIN content: {len(cursos_sin_content)} ({len(cursos_sin_content)*100/len(courses):.1f}%)")

# Analizar campos en cursos sin content
print("\n" + "="*80)
print("ANÁLISIS DE CAMPOS EN CURSOS SIN CONTENT")
print("="*80)

campos_comunes = ['name', 'code', 'courseLevel', 'year', 'periods', 'languageOfLearning', 'learningOutcomes', 'credits']
estadisticas_campos = {}

for campo in campos_comunes:
    tiene_campo = sum(1 for c in cursos_sin_content if campo in c and c.get(campo))
    estadisticas_campos[campo] = {
        'presentes': tiene_campo,
        'porcentaje': tiene_campo * 100 / len(cursos_sin_content)
    }

for campo, stats in estadisticas_campos.items():
    print(f"{campo:20s}: {stats['presentes']:4d} cursos ({stats['porcentaje']:5.1f}%)")

# Analizar nombres para detectar patrones
print("\n" + "="*80)
print("ANÁLISIS DE NOMBRES - PRIMEROS 15 CURSOS SIN CONTENT")
print("="*80)

for i, curso in enumerate(cursos_sin_content[:15]):
    nombre = curso.get('name', 'SIN NOMBRE')
    code = curso.get('code', 'SIN CODE')
    nivel = curso.get('courseLevel', 'SIN NIVEL')
    
    # Detectar tipo de curso por nombre
    tipo = 'REGULAR'
    if any(x in nombre.lower() for x in ['tesis', 'thesis', 'project', 'trabajo', 'seminar', 'seminario', 'workshop']):
        tipo = 'ESPECIAL'
    
    print(f"\n{i+1}. [{code}] {nombre}")
    print(f"   Nivel: {nivel} | Tipo: {tipo}")
    
    # Mostrar qué campos tiene
    campos_presentes = []
    for campo in ['learningOutcomes', 'credits', 'year', 'periods', 'languageOfLearning']:
        if campo in curso and curso.get(campo):
            campos_presentes.append(campo)
    
    if campos_presentes:
        print(f"   Otros campos: {', '.join(campos_presentes)}")
    else:
        print(f"   Otros campos: VACÍO")

print("\n" + "="*80)
print("PRIMEROS 5 CURSOS SIN CONTENT (JSON COMPLETO)")
print("="*80)

# Mostrar los primeros 5 como JSON
ejemplo_json = json.dumps(cursos_sin_content[:5], indent=2, ensure_ascii=False)
print(ejemplo_json)

# Análisis adicional: Tipos de cursos por nombre
print("\n" + "="*80)
print("ANÁLISIS POR TIPO DE CURSO")
print("="*80)

tipos = {
    'TESIS/PROYECTO': 0,
    'SEMINARIO/WORKSHOP': 0,
    'PRÁCTICA/LAB': 0,
    'REGULAR': 0
}

for curso in cursos_sin_content:
    nombre = curso.get('name', '').lower()
    if any(x in nombre for x in ['thesis', 'tesis', 'project', 'proyecto', 'trabajo fin']):
        tipos['TESIS/PROYECTO'] += 1
    elif any(x in nombre for x in ['seminar', 'seminario', 'workshop', 'colloquium']):
        tipos['SEMINARIO/WORKSHOP'] += 1
    elif any(x in nombre for x in ['lab', 'laboratory', 'práctica', 'practice']):
        tipos['PRÁCTICA/LAB'] += 1
    else:
        tipos['REGULAR'] += 1

for tipo, cantidad in tipos.items():
    print(f"{tipo:20s}: {cantidad:4d} ({cantidad*100/len(cursos_sin_content):5.1f}%)")

# Guardar todos los cursos sin content a un archivo para análisis manual
with open('cursos_sin_content_muestra.json', 'w', encoding='utf-8') as f:
    json.dump(cursos_sin_content[:20], f, indent=2, ensure_ascii=False)

print(f"\n✓ Guardado: cursos_sin_content_muestra.json (20 ejemplos)")
