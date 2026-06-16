# LUT SISU Scraper

Este proyecto contiene un scraper para extraer el catálogo de cursos de la universidad LUT desde el API SISU.

## Archivos principales

- `scraper.py`: scraper principal con búsqueda y descarga de detalles de curso.
- `test_helpers.py`: pruebas unitarias para rutinas de limpieza y parseo.
- `test_search.py`: prueba de consulta al endpoint de búsqueda.
- `test_detail.py`: prueba de transformación del detalle de un curso.

## Requisitos

Instala dependencias con:

```bash
pip install -r requirements.txt
```

## Uso

Ejecuta el scraper con una consulta limitada para probar:

```bash
python scraper.py --queries physics --page-limit 5 --max-pages 1 --output test_output.json
```

Para pasar una cookie HTTP si el endpoint la requiere:

```bash
python scraper.py --cookie "TU_COOKIE_AQUI" --output lut_courses.json
```

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

No se ha ejecutado `pytest` durante este cambio. Las pruebas están disponibles en los archivos mencionados, y puedes ejecutarlas manualmente cuando lo necesites.
