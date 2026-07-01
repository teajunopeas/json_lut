# Skill 04 — Refinar un RAM existente

## Propósito

Mejorar un RAM que ya tiene una estructura y, cuando corresponda, observaciones de un coordinador o subdirector, mediante cambios mínimos, trazables y académicamente defendibles.

Esta skill **no** sirve para reconstruir un RAM desde cero. Su función es actuar sobre problemas concretos sin desestabilizar las equivalencias que ya funcionan.

---

## Cuándo usar esta skill

Úsala cuando exista una versión de RAM con al menos uno de estos elementos:

- emparejamientos ya aceptados o marcados como `OK`;
- anotaciones del coordinador;
- equivalencias `justas`, `con reserva` o pendientes;
- déficits de créditos que superarían un límite;
- necesidad de corregir uno o varios huecos concretos de contenidos o resultados.

No la uses para buscar asignaturas sin tener antes un diagnóstico del RAM. Para esa fase, usa `01_buscar_candidatos.md` y `02_evaluar_equivalencia.md`.

---

## Resultado esperado

Una propuesta de ajuste que:

1. resuelva o reduzca los problemas abiertos;
2. mantenga intactas las equivalencias válidas siempre que sea posible;
3. no introduzca nuevos problemas de contenido, créditos o disponibilidad;
4. deje una trazabilidad clara de qué se modificó y por qué;
5. permita decidir si procede actualizar el JSON/Markdown del RAM.

---

## Entradas obligatorias

Antes de modificar nada, reúne:

- la última versión válida del RAM;
- el JSON estructurado que usa el proyecto, si existe;
- las anotaciones más recientes del coordinador/subdirector;
- el estado de créditos, capacidad y cursos compartidos obtenido mediante las herramientas del proyecto;
- las guías o fichas de las asignaturas afectadas;
- la lista de asignaturas con movilidad, semestre y restricciones de nivel;
- cualquier regla explícita del centro sobre déficits, créditos parciales o uso de máster/MOOC.

---

## Principio de intervención mínima

Toda modificación tiene un coste. Por defecto, prefiere la propuesta que resuelva el problema con menos impacto.

Orden de preferencia:

1. mantener exactamente el emparejamiento actual;
2. mover créditos ya libres y académicamente justificables;
3. añadir una asignatura complementaria sin tocar una equivalencia aceptada;
4. ajustar una equivalencia marcada como `Justa` o `Con reserva`;
5. sustituir una equivalencia no validada;
6. tocar una equivalencia `OK`, solo cuando sea imprescindible y el beneficio global sea claramente mayor.

No sustituir una equivalencia solo porque otra parezca más elegante o tenga una similitud semántica mayor.

---

## Procedimiento

### Paso 1. Congelar y clasificar el estado actual

Crea una tabla de trabajo con todas las equivalencias y clasifícalas de este modo:

| Estado | Tratamiento |
|---|---|
| `OK` / validada | Bloqueada por defecto. No tocar. |
| `Aceptable con reserva` | Mantener salvo que el cambio resuelva un problema relevante. |
| `Justa` | Ajustable si mejora la cobertura o los créditos. |
| `Pendiente` / `Insuficiente` | Prioridad de revisión. |
| `Sin revisar` | No modificar hasta disponer de evidencia suficiente. |

Incluye, para cada fila, la fuente del estado: documento RAM, correo, reunión, regla o análisis propio.

---

### Paso 2. Convertir observaciones en problemas verificables

No trabajes con una anotación vaga como “falta materia”. Conviértela en una condición comprobable.

Formato:

```text
Observación original:
[texto literal o resumen fiel]

Problema verificable:
[contenidos/resultados/créditos concretos que faltan o no están demostrados]

Criterio de resolución:
[qué evidencia tendría que aparecer para poder considerar el problema resuelto]
```

Ejemplo abstracto:

```text
Problema verificable:
La equivalencia no demuestra cobertura de X e Y, que son elementos esenciales de la asignatura de origen.

Criterio de resolución:
Una combinación de asignaturas de destino debe incluir evidencia documental explícita de X e Y y mantener un reparto de ECTS compatible.
```

---

### Paso 3. Priorizar los problemas

Ordena los problemas mediante esta prioridad:

1. incumplimientos objetivos: exceso de créditos usados, semestre incompatible, asignatura no accesible o regla vulnerada;
2. observaciones explícitas del coordinador/subdirector;
3. ausencia de un contenido o resultado esencial;
4. exceso del número permitido de déficits;
5. equivalencias `Justas` que podrían fortalecerse sin coste relevante;
6. mejoras estéticas u opcionales.

No dediques tiempo a optimizar puntos 5 o 6 mientras los puntos 1 a 4 sigan abiertos.

---

### Paso 4. Diseñar alternativas antes de modificar

Para cada problema prioritario, genera entre dos y cuatro alternativas realistas. Como mínimo, prueba estas familias de solución, en orden:

1. conservar la equivalencia y aclarar/mejorar la justificación si la evidencia ya existe;
2. redistribuir créditos compatibles;
3. añadir un complemento de destino;
4. cambiar una asignatura de destino no validada;
5. cambiar una equivalencia validada, únicamente como último recurso.

Cada alternativa debe indicar:

- qué cambia;
- qué problema resuelve;
- qué elementos de contenido se mantienen o se pierden;
- ECTS antes y después;
- impacto en otras equivalencias;
- riesgo o incertidumbre;
- motivo para descartarla o mantenerla.

---

### Paso 5. Evaluar impacto global

Puntúa cada alternativa cualitativamente:

| Criterio | Pregunta |
|---|---|
| Cobertura | ¿Resuelve el hueco esencial? |
| Créditos | ¿Cumple o mejora la regla aplicable? |
| Estabilidad | ¿Evita tocar equivalencias `OK`? |
| Disponibilidad | ¿Respeta semestre, nivel y acceso? |
| Trazabilidad | ¿Se puede justificar con fuentes reales? |
| Complejidad | ¿Es fácil de revisar y mantener? |

No uses una puntuación numérica ficticia como sustituto del análisis. La tabla sirve para hacer explícitos los compromisos.

---

### Paso 6. Decidir y aplicar en modo seguro

Antes de alterar el archivo fuente:

1. guarda una copia o versión del estado actual;
2. registra el cambio en una propuesta;
3. comprueba que el cambio no sobreasigna ECTS ni rompe restricciones;
4. aplica solo los cambios aprobados o expresamente solicitados;
5. vuelve a consultar el estado de créditos y emparejamientos;
6. no exportes una versión “definitiva” si quedan problemas críticos abiertos.

Si el agente tiene capacidad de escritura, debe preferir crear una nueva versión de trabajo antes que sobrescribir la última versión validada.

---

## Formato de salida obligatorio

```md
# Refinamiento del RAM — [fecha o versión]

## Estado de partida
- Versión analizada:
- Problemas abiertos:
- Equivalencias bloqueadas:
- Restricciones activas:

## Cambios propuestos

### Cambio [número] — [asignatura o bloque]
- Estado previo:
- Problema verificable:
- Alternativas consideradas:
- Cambio elegido:
- Contenido que mantiene/añade:
- Créditos antes/después:
- Impacto en el RAM:
- Riesgo:
- Confianza:
- Justificación breve:

## Equivalencias que se mantienen sin cambios
- ...

## Problemas que permanecen abiertos
- ...

## Decisión de exportación
- Exportar versión de trabajo: Sí / No
- Exportar versión final: Sí / No
- Motivo:
```

---

## Reglas de seguridad

Nunca:

- sobrescribas la última versión validada sin una copia;
- cambies una asignatura `OK` para obtener una mejora marginal;
- apliques una propuesta no evaluada mediante `02_evaluar_equivalencia.md`;
- uses créditos como fichas intercambiables sin respaldo académico;
- declares resuelto un problema solo porque el número de ECTS mejora;
- ocultes que un problema sigue abierto.

---

## Condición de salida

La skill termina cuando se da una de estas situaciones:

- hay una propuesta mínima y justificada lista para aplicar;
- los problemas críticos se han resuelto y las verificaciones posteriores son correctas;
- no existe una mejora defendible sin empeorar el conjunto.

En el último caso, no fuerces un cambio. Documenta la limitación y solicita revisión humana o más información.
