# MATCHER v2 - Búsqueda Inteligente de Cursos

## ¿Cómo Usar?

### Paso 1: Activar el entorno virtual

```powershell
.\.venv\Scripts\Activate.ps1
```

### Paso 2: Ejecutar el script

```powershell
python matcher_v2.py
```

### Paso 3: Seleccionar un curso

El script muestra un menú con los 27 cursos ULPGC disponibles:

```bash
CURSOS DISPONIBLES ULPGC:

 1. 49188 - Analisis Matematico III
 2. 49190 - Electromagnetismo y Optica Fisica II
 3. 49189 - Estadistica
 ... (27 cursos totales)
```

**Opciones:**

- Escribe un número (1-27) para buscar equivalencias de UN curso
- Escribe **0** para buscar todos los cursos a la vez (genera un reporte largo)

### Paso 4: Interpretar resultados

El script mostrará una tabla con los top 10 cursos de LUT ordenados por similitud:

```bash
RESULTADOS - Top 10:

┌─────────┬──────────┬──────────────────────────────────────┬──────┬──────────┐
│ Simil % │ Codigo   │ Nombre                               │ ECTS │ Nivel    │
├─────────┼──────────┼──────────────────────────────────────┼──────┼──────────┤
│ 38.6%   │ HDD4030  │ Engineering Mathematics III (HDD)    │ 0-6  │ Bachelor │
│ 38.4%   │ LES10A24 │ Engineering Mathematics III          │ 0-6  │ Bachelor │
│ 37.7%   │ BM20A84  │ Partial Differential Equations       │ 0-6  │ Intermed │
...
```

**Interpretar columnas:**

- **Simil %**: Similitud semántica (0-100%). Rojo < 50%, Amarillo 50-60%, Verde > 60%
- **Codigo**: Código del curso LUT
- **Nombre**: Nombre del curso LUT
- **ECTS**: Rango de créditos (mín-máx)
- **Nivel**: Bachelor, Intermediate, Master, o Doctoral

---

## Arquitectura Interna

### 1. **Pre-filtrado por Keywords (FTS)**

- Extrae 7-12 palabras clave en INGLÉS de cada curso ULPGC
- Busca en la base de datos SQLite con Full-Text Search
- Resultado: 30-40 candidatos PRE-SELECCIONADOS relevantes

**Ejemplo:**

```text
Métodos Matemáticos II (ULPGC) → 
Keywords: "differential equations", "partial differential", "fourier series", ...
→ FTS Search → 40 cursos con estos términos en LUT
```

### 2. **Ranking por Similitud Semántica**

- Usa embeddings (all-MiniLM-L6-v2 de Sentence-Transformers)
- Calcula similitud coseno entre texto ULPGC y cada candidato LUT
- Ordena resultados por puntuación (0-100%)

**Ventajas:**

- Semántica: No busca palabras exactas, sino significado similar
- Rápido: Embeddings solo de 30-40 cursos (no 2313)
- Relevante: Keywords garantizan candidatos relacionados

---

## Customización

### Cambiar Keywords de un Curso

Abre `matcher_v2.py` y edita `KEYWORD_MAP`:

```python
"49192": {
    "name": "Metodos Matematicos II",
    "keywords": [
        "differential equations",
        "partial differential",
        "fourier series",
        # Agrega más palabras clave aquí
    ]
},
```

**Tips para buenos keywords:**

- Usa términos en INGLÉS (base de datos LUT está en inglés)
- Incluye sinónimos y variaciones
- 8-10 términos es óptimo
- Sé específico (ej: "partial differential" mejor que "equations")

### Cambiar límite de resultados

En la función `search_keywords()`:

```python
def search_keywords(keywords: list, limit: int = 30) -> list:
    # limit=30 es el número de candidatos pre-filtrados
    # limit=40 para búsquedas más amplias (más lento)
```

En la tabla de resultados:

```python
for r in scored[:10]:  # Cambia 10 para mostrar más/menos resultados
    table.add_row(...)
```

---

## Archivos Relacionados

- **matcher_v2.py**: Script principal (este archivo)
- **lut_courses.db**: Base de datos SQLite regenerable con `python build_db.py`
- **ulpgc_courses.json**: Datos de los 27 cursos ULPGC (fuente)
- **tools/analysis/**: Scripts e informes exploratorios sobre cobertura de `content`

---

## Ejemplos de Uso

### Búsqueda Simple: Un Curso

```powershell
python matcher_v2.py
# Selecciona: 5 (Métodos Matemáticos II)
# Resultado: Top 10 cursos LUT equivalentes
```

### Búsqueda Avanzada: Todos los Cursos

```powershell
python matcher_v2.py
# Selecciona: 0 (procesa los 27)
# Resultado: Reporte de 270 equivalencias (27 cursos x 10 resultados)
# Útil para exportar a Excel/CSV
```

### Script Batch: Procesar Solo Matemáticas

Edita `matcher_v2.py` en la función `main()`:

```python
# Descomentar estas líneas para filtrar por área
if choice == 0:
    selected_codes = [code for code in codes if courses_dict[code]['area'] == 'Matemáticas']
```

---

## Troubleshooting

### Error: "No se encontró lut_courses.db"

- Primero ejecuta: `python build_db.py`

### Error: "UnicodeEncodeError" en Windows**

- Ya está solucionado (sin emojis)
- Si ocurre de nuevo, asegúrate de tener Python 3.12+

### Pocos resultados (< 5 cursos)

- Ajusta los keywords: edita `KEYWORD_MAP`
- Aumenta el `limit` en `search_keywords()`
- Verifica que la BD se haya regenerado correctamente con `python build_db.py`

### Resultados con baja similitud (< 40%)

- Normal: embeddings capturan similitud semántica, no equivalencia exacta
- Interpreta como "relevante" si > 35%
- Interpreta como "muy relevante" si > 50%

---

## Próximos Pasos Opcionales

1. **Combinaciones 2-curso**: Implementar búsqueda de pares
   - "¿Qué 2 cursos LUT pueden cubrir 1 ULPGC?"
2. **Re-scraper de 2025-2026**: Mejorar ~500 cursos sin descripción
3. **Exportación a CSV**: Generar reportes para Excel

4. **API REST**: Exponer como servicio web

---

**Creado:** 2026-06-16  
**Versión:** 2.0 (Completa con 27 cursos ULPGC + menú interactivo)  
**Autor:** Sistema de Movilidad Erasmus ULPGC → LUT
