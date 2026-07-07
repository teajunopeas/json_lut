# Contexto LUT University y catálogo de destino

## Finalidad

Este archivo explica cómo interpretar el catálogo LUT para el RAM. No sustituye a la ficha concreta de cada curso ni a la comprobación de matrícula real.

## Fuente de datos

- El catálogo local se obtiene desde SISU mediante `scraper.py` y se almacena normalmente en `lut_courses.json`.
- `build_db.py` crea `lut_courses.db` como índice FTS5 regenerable para búsqueda; no es la fuente académica primaria.
- `matcher.py` ayuda a descubrir y ordenar candidatos; no determina que una asignatura sea convalidable.

## Campos que deben comprobarse

Para cada candidato LUT, consultar cuando estén disponibles:

- código y nombre;
- ECTS mínimos, máximos o fijos;
- semestre o periodo de impartición;
- nivel;
- contenido;
- resultados de aprendizaje;
- prerrequisitos;
- idioma;
- disponibilidad para estudiantes de intercambio, si aparece;
- curso académico o vigencia de la ficha.

## Lectura académica

- El nombre es un punto de partida, no una prueba de cobertura.
- Los resultados y contenidos pueden estar incompletos en SISU; si falta evidencia, no rellenar el hueco por inferencia.
- Los ECTS variables se deben tratar como rango hasta confirmar la opción concreta de matrícula.
- Los periodos y semestres de catálogo deben contrastarse con la movilidad real.

## Niveles y restricciones

- El catálogo puede incluir cursos de grado, máster, módulos y MOOC.
- No proponer automáticamente cursos de máster. Antes de usarlos, consultar `casos/master.md` y confirmar elegibilidad, semestre y matrícula.
- No proponer automáticamente MOOC como solución principal. Consultar `casos/mooc.md` y comprobar si su modalidad, créditos y acceso son aceptables.

## Asignaturas LUT ya relevantes en el RAM

- `BM20A5701` `Integral Transforms`.
- `BM20A8600` `Basics of Statistics`.
- `BM20A3003` `Statistical Parameter Estimation`.
- `BM20A7700` `Special Course on Inverse Problems`.
- `BM20A7300` `Functional Analysis`.
- `BM20A8300` `Fourier Analysis`.
- `BM20A8400` `Partial Differential Equations`.
- `BM20A4703` `Partial Differential Equations with Applications`.
- `BM20A7601` `Numerical Methods for Partial Differential Equations`.
- `BH40A1560` `Fundamentals of Computational Fluid Dynamics`.
- `BL40A0130` `Measurement and Control Systems`.
- `BH20A0720` `Engineering Thermodynamics`.
- `CS30A1570` `Complex Systems`.
- `BM30A2200` `Semiconductor and Superconductor Physics`.
- `BM30A0910` `Materials Science and Engineering A`.
- `BM30A0920` `Materials Science and Engineering B`.
- `BM30A2900` `Wave Motion and Wave Phenomena`.
- `BL50A0600` `Electromagnetic Compatibility in Power Electronics`.
- `LES10A410` `Engineering Project Work`.
