# Herramientas del repositorio

## Regla general de uso

Usa cada herramienta para el dato que realmente calcula. No rehagas manualmente cálculos que ya produce un script. Pero tampoco conviertas la salida de un script en una decisión académica automática.

Antes de ejecutar algo, identifica si la operación es:

- **solo lectura**: consulta, búsqueda, inspección, pruebas sin efectos persistentes;
- **regenerable**: crea un artefacto que puede volver a construirse;
- **modificadora**: sobrescribe o actualiza datos, asignaciones o exportaciones;
- **de red**: consulta servicios externos y puede depender de cookies, disponibilidad o cambios de API.

---

## `scraper.py`

### Función

Extrae cursos de LUT desde el API/SISU y construye o actualiza un JSON de catálogo. El README público indica que puede ejecutarse con consultas limitadas para pruebas y que puede requerir una cookie de sesión SISU.

### Entrada principal

- consultas o filtros de scraping;
- límites de páginas o resultados;
- cookie HTTP cuando el endpoint lo requiera;
- ruta de salida.

### Salida principal

- JSON de cursos LUT, normalmente `lut_courses.json` o un fichero de prueba indicado por el usuario.

### Datos relevantes que intenta conservar

Según la documentación pública, los registros pueden contener:

- `id`, `code`, `name`;
- `credits`;
- `learningOutcomes`, `content`;
- `courseLevel`, `languageOfLearning`, `year`, `coursePeriod`;
- `prerequisites`, `equivalentCoursesInfo`.

### Riesgo

**Modificadora y de red.** Puede sobrescribir el catálogo si se usa la ruta habitual de salida. No la ejecutes para una consulta académica ordinaria si ya existe un catálogo válido: usa primero la base y el matcher.

### Cuándo usarla

- para renovar el catálogo;
- para completar cursos que faltan;
- para reproducir un catálogo en una fecha concreta;
- para realizar pruebas controladas con salida separada.

### Precauciones

- no guardes cookies ni credenciales en Git;
- no sobrescribas `lut_courses.json` sin copia o confirmación;
- documenta fecha, consulta y alcance de una actualización;
- valida que los cursos obtenidos contienen detalles útiles antes de reconstruir la base.

---

## `build_db.py`

### Función

Lee `lut_courses.json` y genera `lut_courses.db`, una base SQLite con una tabla virtual FTS5 llamada `courses`.

### Campos indexados

El código público indexa, entre otros:

- código y nombre;
- créditos mínimo y máximo;
- nivel;
- idioma;
- periodos;
- indicador de intercambio;
- resultados de aprendizaje;
- contenido;
- información de equivalencias.

### Salida

- `lut_courses.db`.

### Riesgo

**Regenerable y modificadora.** Borra y recrea la tabla `courses` de la base. El propio código señala que la base es un artefacto regenerable y no se versiona en Git.

### Cuándo usarla

- inmediatamente después de actualizar `lut_courses.json`;
- si la base falta;
- si el matcher devuelve resultados incoherentes con el JSON actual;
- si se modifica el esquema de datos que necesita indexar.

### Precauciones

- no hace falta ejecutarla para cada búsqueda;
- no cambia el catálogo fuente ni el RAM, pero sí sustituye la base de búsqueda;
- si la ejecución falla, comprueba primero que existe `lut_courses.json` y que su estructura sigue siendo compatible.

---

## `matcher.py` — script vigente según la raíz pública actual

### Función

Es el matcher interactivo para explorar equivalencias ULPGC → LUT.

El código público muestra este flujo:

1. carga asignaturas ULPGC desde `ulpgc_courses.json`;
2. exige que cada una tenga palabras clave;
3. busca candidatos LUT mediante FTS5 en `lut_courses.db`;
4. calcula similitud semántica por contenidos, resultados y texto combinado;
5. permite ver detalles, ampliar resultados, buscar un curso manualmente, seleccionar varios cursos o combinaciones;
6. controla la capacidad disponible cuando un curso LUT ya se usa en otra asignación;
7. mantiene estructuras de asignaciones durante la sesión y muestra el estado del acuerdo.

### Modelo semántico

Usa `all-MiniLM-L6-v2`. Si existe una copia local en `models/all-MiniLM-L6-v2`, la carga sin red; de lo contrario, el código intenta descargarla y guardarla localmente.

### Interpretación del umbral

El código fija un umbral orientativo de 75 %. Esto debe interpretarse como señal para priorizar revisión, no como aprobación automática. El propio comentario inicial del script dice que no constituye aprobación automática.

### Operaciones y riesgo

- **Consulta/búsqueda:** carga JSON, consulta SQLite y muestra resultados.
- **Asignación interactiva:** puede cambiar la estructura de asignaciones en memoria y, según las opciones finales del flujo, guardar o exportar resultados.
- **Modelo:** puede descargar archivos al primer uso si no existe la copia local.

Antes de utilizar opciones de guardado, exportación o reemplazo, confirma el nombre y la ruta de salida en la versión local del script.

### Cuándo usarlo

- para descubrir candidatos;
- para revisar detalladamente contenidos y resultados;
- para explorar combinaciones de cursos;
- para comprobar capacidad restante de cursos LUT ya compartidos;
- para preparar una propuesta, nunca como sustituto de la revisión académica.

### Precauciones

- no asumas que el candidato primero es el mejor académicamente;
- filtra máster/niveles según reglas documentadas del caso;
- abre la vista detallada antes de aceptar;
- no distribuyas ECTS entre asignaturas sin justificar contenido;
- confirma si el RAM local usa archivos de asignación, opciones de exportación o nombres distintos a los del repositorio remoto.

---

## `ulpgc_courses.json`

### Función

Es el catálogo de origen que alimenta el matcher. El código público requiere, como mínimo, palabras clave por asignatura y utiliza contenidos/resultados para la comparación semántica cuando están disponibles.

### Riesgo

**Dato fuente académico.** Cambiarlo puede alterar las búsquedas y la calidad de las comparaciones. No reescribas descripciones, resultados o keywords sin conservar la fuente o la razón del cambio.

### Buenas prácticas

- separar texto oficial de notas o interpretaciones;
- conservar código, ECTS, semestre y tipo;
- usar keywords en inglés precisas y revisables;
- no convertir keywords en una lista de términos demasiado amplia: empeora la preselección FTS.

---

## `lut_courses.json`

### Función

Catálogo fuente de destino obtenido por el scraper y usado para generar la base FTS5.

### Riesgo

**Dato fuente de destino.** No debe editarse manualmente como forma habitual de corregir una búsqueda. Si hay una carencia, documenta primero si procede de scraping, de ausencia de detalles en SISU o de una necesidad de normalización.

---

## `lut_courses.db`

### Función

Índice SQLite FTS5 para la búsqueda rápida de cursos LUT.

### Riesgo

**Artefacto regenerable.** No es la fuente de verdad académica. Se reconstruye desde `lut_courses.json` con `build_db.py`.

---

## `MATCHER_README.md`, `MATCHER_GUIDE.md` y `RAM_plantilla.md`

### Función

- Los dos primeros documentan uso, flujo y opciones del matcher.
- `RAM_plantilla.md` sirve como base de presentación de la salida en Markdown.
- 
---

## `tests/`

### Función

Pruebas del scraper y del mapeo de campos.

### Riesgo

Al menos una prueba mencionada en el README consulta el endpoint real de LUT. Trátala como prueba de integración: puede fallar por falta de red, cookies, cambios en SISU o límites externos, sin que ello demuestre un error local.

---

## `tools/analysis/`

### Función

Contiene análisis exploratorios sobre calidad del dataset.

### Uso recomendado

Úsalo para diagnóstico, auditoría y mejora de datos. No asumas que sus conclusiones modifican el flujo productivo si no están integradas explícitamente en los scripts vigentes.

---

## `reciclaje/`

### Función

Material histórico, prototipos o versiones sustituidas.

### Regla

No ejecutes ni cites archivos de esta carpeta como procedimiento actual salvo que se haya confirmado expresamente que siguen siendo necesarios. Puede ser útil para recuperar decisiones técnicas o comparar implementaciones antiguas.

---

## Verificación local obligatoria antes de una tarea de modificación

Antes de pedir al agente que toque datos o scripts, comprobar localmente:

```bash
git status --short
find . -maxdepth 2 -type f | sort
python matcher.py --help
python scraper.py --help
```

Si `matcher.py --help` no existe o el script es puramente interactivo, consulta su código y la documentación antes de inventar comandos.
