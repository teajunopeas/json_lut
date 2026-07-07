# Scripts relevantes

Estos scripts no viven dentro de `.agents`, pero son la base técnica que las skills deben consultar cuando corresponda.

- `scraper.py` -> extrae y actualiza el catálogo LUT.
- `build_db.py` -> reconstruye la base FTS5 `lut_courses.db`.
- `matcher.py` -> busca candidatos y permite revisar asignaciones.
- `matcher_core.py` -> lógica de coincidencia y soporte al matcher.
- `check_db.py` -> verificación rápida de la base de datos.
- `tests/test_search.py` -> pruebas de búsqueda.
- `tests/test_helpers.py` -> pruebas auxiliares.
- `tests/test_detail.py` -> pruebas de detalle y presentación.
- `tools/analysis/analyze_lut_courses.py` -> análisis de calidad del catálogo.
- `tools/analysis/analyze_missing_content.py` -> análisis de contenidos faltantes.
- `tools/analysis/analyze_detailed_missing.py` -> análisis más fino de carencias.
- `tools/analysis/informe_final_content_analysis.py` -> informe consolidado.
