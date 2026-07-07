# Checklist — Antes de exportar una versión del RAM

Usa esta lista antes de generar JSON, Markdown, tablas oficiales o documentos para revisión.

## 1. Fuente y versión

- [ ] ¿La fuente estructurada es la versión correcta?
- [ ] ¿Tiene fecha, identificador o estado de versión?
- [ ] ¿La última versión anterior está conservada?
- [ ] ¿Está claro si la salida es `Borrador de trabajo`, `Listo para revisión`, `Versión validada` o `Histórico`?

## 2. Coherencia de datos

- [ ] ¿Cada asignatura ULPGC tiene código, nombre y ECTS?
- [ ] ¿Cada asignatura LUT/destino tiene código, nombre, semestre y ECTS?
- [ ] ¿Los créditos parciales están expresados sin ambigüedad?
- [ ] ¿No hay cursos de destino sobreasignados?
- [ ] ¿El total y número de déficits cumplen las reglas aplicables o están visiblemente marcados como pendientes?
- [ ] ¿No hay duplicados accidentales ni asignaturas antiguas que debían haberse eliminado?

## 3. Decisiones y observaciones

- [ ] ¿Las anotaciones del coordinador/subdirector siguen asociadas a las asignaturas correctas?
- [ ] ¿Los estados `OK`, `Con reserva`, `Justa`, `Pendiente` e `Insuficiente` se conservan correctamente?
- [ ] ¿Las reservas y problemas abiertos siguen visibles?
- [ ] ¿Las justificaciones coinciden con la decisión real y no prometen más de lo que cubre la documentación?

## 4. Calidad del formato

- [ ] ¿El JSON es válido y codificado en UTF-8?
- [ ] ¿El Markdown se visualiza correctamente en VS Code?
- [ ] ¿Las tablas son legibles y no están desplazadas?
- [ ] ¿Los saltos de línea en equivalencias múltiples se ven correctamente?
- [ ] ¿Tildes, caracteres especiales, guiones y códigos se conservan?
- [ ] ¿Obligatorias y optativas aparecen separadas cuando corresponde?

## 5. Trazabilidad y entrega

- [ ] ¿Se ha incluido un resumen de cambios respecto a la versión anterior?
- [ ] ¿Se indica la fuente estructurada usada?
- [ ] ¿Se han anotado problemas todavía abiertos?
- [ ] ¿Se ha realizado una comprobación visual del archivo final?
- [ ] ¿Se ha guardado el resultado con un nombre de versión claro?

## Decisión

- [ ] Exportar como borrador.
- [ ] Exportar para revisión.
- [ ] Marcar como validada solo si existe aprobación correspondiente.
- [ ] No exportar: hay discrepancias que deben volver a la fuente o a la skill de análisis.
