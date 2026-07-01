# Skill 06 — Exportar y verificar el RAM

## Propósito

Generar versiones legibles, consistentes y trazables del RAM a partir de la fuente estructurada del proyecto, verificando que el documento exportado refleja exactamente las decisiones aprobadas.

Esta skill se ocupa de la salida: JSON, Markdown u otros formatos que el flujo de trabajo tenga definidos. No debe usar la exportación para “arreglar” problemas académicos no resueltos.

---

## Principio de fuente única de verdad

La información estructurada aprobada debe ser la fuente de verdad del RAM.

- El JSON o formato estructurado equivalente debe contener los datos operativos.
- El Markdown debe ser una vista legible y revisable de esos datos.
- La tabla oficial o documento final debe derivar de la misma versión aprobada.

No edites a mano un archivo exportado si puedes corregir primero la fuente estructurada y volver a exportar. Si una corrección manual es imprescindible, regístrala y sincronízala después con la fuente.

---

## Cuándo usar esta skill

Úsala cuando:

- se han aprobado cambios en el RAM;
- se necesita un resumen en Markdown para VS Code o revisión;
- se necesita un JSON limpio para reutilizar en herramientas;
- se va a preparar una tabla oficial o un documento para enviar;
- hay que comprobar que una exportación no ha perdido anotaciones, créditos parciales o reservas.

No la uses para exportar una “versión final” si aún hay decisiones importantes sin resolver.

---

## Estados de exportación

Clasifica toda exportación con una etiqueta visible:

| Estado | Uso |
|---|---|
| `Borrador de trabajo` | Cambios exploratorios o pendientes de comprobación. |
| `Listo para revisión` | Datos verificados, pendiente de validación humana. |
| `Versión validada` | Aprobada expresamente por quien corresponda. |
| `Histórico` | Versión anterior conservada para trazabilidad. |

No llames “final” a una versión que no ha recibido la validación requerida.

---

## Entradas obligatorias

Antes de exportar, verifica que dispones de:

- fuente estructurada actualizada;
- identificador de versión o fecha;
- estado del RAM;
- lista de cambios aplicados desde la versión anterior;
- anotaciones del coordinador incorporadas o marcadas como pendientes;
- resultados actuales de créditos y restricciones;
- nombre de destino, movilidad, titulación y datos básicos correctos;
- reglas de formato del destinatario, si existen.

---

## Procedimiento

### Paso 1. Guardar la versión de partida

Antes de generar una nueva salida:

1. conserva la versión anterior validada o revisable;
2. asigna un nombre de versión claro;
3. anota fecha y motivo del cambio;
4. evita sobrescribir archivos históricos.

Formato orientativo de nombre:

```text
RAM_[titulacion]_[destino]_[AAAA-MM-DD]_[estado].json
RAM_[titulacion]_[destino]_[AAAA-MM-DD]_[estado].md
```

Adapta el formato al convenio ya existente en el repositorio; no impongas uno nuevo si el proyecto ya utiliza otro.

---

### Paso 2. Validar la fuente estructurada

Comprueba como mínimo:

- que cada asignatura de origen tiene código, nombre y ECTS;
- que cada asignatura de destino tiene código, nombre, semestre y ECTS;
- que los créditos parciales se expresan de forma inequívoca;
- que no se supera la capacidad de una asignatura de destino;
- que los nombres, códigos y semestres son consistentes con la base de datos;
- que las observaciones del coordinador están asociadas al elemento correcto;
- que los campos pendientes se distinguen de los campos vacíos;
- que no existen duplicados accidentales.

Si el proyecto proporciona una validación mediante script, úsala antes de cualquier comprobación manual.

---

### Paso 3. Ejecutar exportación reproducible

Usa la herramienta de exportación del proyecto, no una transcripción manual, siempre que sea posible.

El proceso de exportación debe:

- leer una versión identificable de la fuente;
- generar archivos de salida con nombre claro;
- conservar codificación UTF-8;
- no modificar silenciosamente datos de entrada;
- dejar constancia de la versión o fecha;
- separar claramente obligatorias y optativas, cuando aplique.

Si hay que ajustar una plantilla, modifica la plantilla o el exportador, no los datos académicos para “hacer que se vea bien”.

---

### Paso 4. Verificar visualmente y semánticamente

Después de exportar, revisa tanto estructura como contenido.

#### Verificación estructural

- ¿El JSON es válido y legible?
- ¿El Markdown se abre bien en VS Code?
- ¿Las tablas no tienen columnas desplazadas?
- ¿Los saltos de línea hacen legible una equivalencia con varias materias de destino?
- ¿Los caracteres especiales, tildes y códigos se conservan?

#### Verificación semántica

- ¿Aparecen todas las asignaturas acordadas?
- ¿Aparecen todas las anotaciones relevantes del coordinador?
- ¿Los ECTS exportados coinciden con los datos de origen?
- ¿Las asignaturas marcadas como pendientes siguen visibles como pendientes?
- ¿No se ha transformado una reserva en un `OK` por el formato?
- ¿Las asignaturas eliminadas ya no aparecen por error?

---

### Paso 5. Emitir un resumen de cambios

Junto a cada exportación, genera o actualiza un resumen breve:

```md
## Resumen de versión

- Versión:
- Estado:
- Fecha:
- Fuente estructurada:
- Cambios desde la versión anterior:
  - ...
- Problemas aún abiertos:
  - ...
- Verificaciones realizadas:
  - ...
```

Este resumen permite entender una versión sin comparar manualmente archivos extensos.

---

## Formato recomendado para Markdown legible

El Markdown debe priorizar revisión humana en un editor como VS Code:

1. encabezado con versión, estado y origen de los datos;
2. datos básicos de movilidad;
3. tabla de observaciones globales;
4. tabla de asignaturas obligatorias;
5. tabla de optativas;
6. créditos o problemas pendientes;
7. resumen de cambios;
8. notas de trazabilidad.

Para una equivalencia con varias asignaturas de destino, usa saltos de línea dentro de la celda o una lista breve. Evita tablas excesivamente anchas si impiden leer el contenido.

---

## Formato mínimo de JSON

Sin imponer una estructura concreta al proyecto, cada registro debería poder expresar al menos:

```json
{
  "ulpgc": {
    "codigo": "...",
    "asignatura": "...",
    "ects": 0
  },
  "destino": [
    {
      "codigo": "...",
      "asignatura": "...",
      "semestre": "...",
      "ects": 0,
      "ects_asignados": 0
    }
  ],
  "estado": "OK | aceptable_con_reserva | justa | pendiente | insuficiente",
  "anotacion_coordinador": "...",
  "justificacion": "..."
}
```

No añadas campos inventados si el esquema actual ya resuelve esa necesidad. Mantén compatibilidad con las herramientas existentes.

---

## Qué no hacer

Nunca:

- exportes como final una versión no validada;
- cambies valores de ECTS o contenido solo en Markdown;
- ocultes observaciones para que la tabla parezca más limpia;
- sobrescribas un histórico sin copia;
- elimines anotaciones pendientes durante la exportación;
- interpretes un error de formato como una corrección académica;
- des por válida una exportación sin revisar al menos una muestra visual y el estado de créditos.

---

## Condición de salida

La skill termina cuando:

- la fuente está validada;
- se han generado los formatos solicitados;
- la revisión estructural y semántica no detecta discrepancias;
- el estado de la versión está etiquetado correctamente;
- existe un resumen de cambios y problemas pendientes.

Si aparece una discrepancia, vuelve a la fuente estructurada o a la skill correspondiente; no la maquilles en el archivo exportado.
