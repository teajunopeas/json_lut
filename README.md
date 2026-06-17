# LUT SISU Scraper y Matcher ULPGC -> LUT

Este proyecto extrae el catálogo de cursos de LUT desde el API SISU y lo prepara para buscar posibles equivalencias con asignaturas ULPGC.

## Archivos principales

- `scraper.py`: scraper principal con búsqueda y descarga de detalles de curso.
- `build_db.py`: genera `lut_courses.db` desde `lut_courses.json` con índice FTS5.
- `matcher_v2.py`: matcher interactivo que combina keywords y embeddings semánticos.
- `lut_courses.json`: catálogo LUT versionado.
- `ulpgc_courses.json`: asignaturas ULPGC enriquecidas para el matcher.
- `tools/analysis/`: scripts e informes exploratorios sobre calidad del dataset.
- `tests/`: pruebas del scraper y del mapeo de campos.

## Requisitos

Instala dependencias con:

```bash
pip install -r requirements.txt
```

## Uso

### 1. Scraping LUT

Ejecuta el scraper con una consulta limitada para probar:

```bash
python scraper.py --queries physics --page-limit 5 --max-pages 1 --output test_output.json
```

Para pasar una cookie HTTP si el endpoint la requiere:

```bash
python scraper.py --cookie "TU_COOKIE_AQUI" --output lut_courses.json
```

### 2. Construir la base de búsqueda

`lut_courses.db` no se versiona porque es regenerable:

```bash
python build_db.py
```

### 3. Buscar equivalencias

```bash
python matcher_v2.py
```

Consulta más detalles en `MATCHER_README.md`.

## Extracción de la cookie

Para usar la cookie correcta, abre el navegador con la sesión de LUT SISU activa y sigue estos pasos:

1. Abre las herramientas de desarrollador (F12).
2. Ve a la pestaña `Application` (Chrome) o `Storage` (Firefox).
3. En `Cookies`, selecciona `https://sisu.lut.fi`.
4. Busca la cookie asociada a la sesión, normalmente llamada `JSESSIONID`, `SESSION`, `sisu` o similar.
5. Copia el valor completo de la cookie.
6. Pega ese valor en el script usando `--cookie "NOMBRE=valor; otro=valor"`.

> Si el endpoint requiere además una organización específica, asegúrate de haber seleccionado "Lappeenranta-Lahti University of Technology LUT (+ all suborganizations)" en el buscador antes de copiar la cookie.

## Salida

El resultado se guarda en un archivo JSON con registros que incluyen:

- `id`
- `code`
- `name`
- `credits`
- `learningOutcomes`
- `content`
- `courseLevel`
- `languageOfLearning`
- `year`
- `coursePeriod`
- `prerequisites`
- `equivalentCoursesInfo`

## Nota

`tests/test_search.py` consulta el endpoint real de LUT; trátalo como prueba de integración si no tienes red disponible.
