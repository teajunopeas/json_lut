---
name: "evaluar-equivalencia"
description: "Evaluar si una o varias asignaturas de destino justifican una equivalencia académica."
---

# Skill 02 — Evaluar una equivalencia académica

## Propósito

Determinar si una o varias asignaturas de destino pueden justificar el reconocimiento de una asignatura de origen.

Esta skill compara evidencia académica. No debe aceptar equivalencias por similitud superficial, nombre parecido o coincidencia parcial de créditos.

---

## Cuándo usar esta skill

Úsala después de `01_buscar_candidatos.md`, cuando ya exista una lista corta de candidatos, o para revisar una equivalencia actual cuestionada por el coordinador.

---

## Entradas necesarias

Para cada evaluación reúne:

- asignatura de origen: código, nombre, ECTS, semestre;
- resultados de aprendizaje de origen, si existen;
- contenidos de origen, si existen;
- competencias y prerrequisitos relevantes;
- una o varias asignaturas de destino;
- resultados, contenidos, temario, objetivos, métodos o evaluación de destino;
- ECTS, semestre, nivel y restricciones de destino;
- estado actual de créditos en el RAM;
- observaciones del coordinador o del subdirector;
- equivalencias ya validadas que podrían verse afectadas.

---

## Principio de evidencia

Una equivalencia es defendible cuando puede mostrarse con evidencia documental que la combinación de asignaturas de destino cubre de forma suficiente los elementos esenciales de la asignatura de origen.

No hace falta una coincidencia literal o perfecta.

Sí hace falta que los huecos restantes no afecten a los elementos centrales de la materia.

---

## Elección de estrategia de comparación

No uses siempre el mismo tipo de comparación. Decide cuál es más informativa en el caso concreto.

Posibles estrategias:

| Estrategia | Cuándo usarla |
|---|---|
| Resultados origen ↔ Contenidos destino | Cuando el origen define bien qué debe saber hacer el estudiante y el destino publica temarios detallados |
| Contenidos origen ↔ Contenidos destino | Cuando ambas guías tienen bloques temáticos claros |
| Resultados origen ↔ Resultados destino | Cuando ambas instituciones describen resultados verificables y comparables |
| Contenidos origen ↔ Resultados destino | Cuando el destino no tiene temario completo, pero sí resultados específicos |
| Combinada | Cuando ninguna fuente basta por sí sola |

En cada evaluación debes indicar explícitamente:

```text
Estrategia utilizada:
[opción elegida]

Motivo:
[por qué esta comparación es la más fiable con la documentación disponible]
```

---

## Procedimiento

### Paso 1. Identificar los elementos esenciales de origen

Divide la asignatura de origen en:

| Categoría | Significado |
|---|---|
| Esenciales | sin ellos la asignatura no puede considerarse cubierta |
| Importantes | deben aparecer en gran medida, aunque puede haber cobertura parcial |
| Complementarios | aportan calidad, pero su ausencia no invalida por sí sola |
| Contextuales | herramientas, aplicaciones o ejemplos secundarios |

No inventes esta clasificación. Debe derivarse de la guía docente, resultados de aprendizaje, observaciones del coordinador o documentación oficial.

---

### Paso 2. Extraer evidencia de destino

Para cada asignatura de destino, anota únicamente lo que se pueda respaldar con fuente documental.

Clasifica cada elemento como:

- `Cubre claramente`;
- `Cubre parcialmente`;
- `No hay evidencia suficiente`;
- `No cubre`.

No conviertas “no hay evidencia” en “cubre parcialmente”.

---

### Paso 3. Construir una matriz de cobertura

Usa esta tabla:

| Elemento de origen | Prioridad | Evidencia en destino | Cobertura | Observación |
|---|---|---|---|---|
| ... | Esencial / Importante / Complementario | cita o resumen verificable | Clara / Parcial / No demostrada / Ausente | ... |

Una asignatura de destino puede cubrir varios elementos. Varias asignaturas de destino pueden combinarse para cubrir un mismo elemento, siempre que los créditos y la lógica del RAM lo permitan.

---

### Paso 4. Evaluar créditos y estructura

Comprueba siempre:

- ECTS de origen;
- ECTS de destino disponibles;
- crédito usado parcialmente;
- déficit o sobrante;
- número de emparejamientos deficitarios;
- semestre y accesibilidad;
- si un curso de destino se está usando en otra equivalencia;
- si se respeta la regla del centro sobre créditos parciales o déficit.

No declares una equivalencia válida si el contenido es bueno pero los créditos la hacen inviable, salvo que la propuesta incluya una solución concreta para los créditos.

---

### Paso 5. Clasificar la equivalencia

Usa una de estas categorías:

| Categoría | Significado |
|---|---|
| Muy sólida | cubre los elementos esenciales, tiene créditos adecuados y no presenta restricciones relevantes |
| Sólida | cubre los elementos esenciales y la debilidad restante es menor o bien explicada |
| Aceptable con reserva | tiene cobertura suficiente, pero hay una carencia o tensión que debe reconocerse |
| Justa | puede ser defendible en conjunto, pero depende de complementos, créditos o interpretación |
| Insuficiente | faltan elementos esenciales o la evidencia es demasiado débil |
| No utilizable | incumple semestre, nivel, acceso, créditos u otra restricción objetiva |

No conviertas una equivalencia `Justa` en `Sólida` por conveniencia.

---

### Paso 6. Analizar impacto global

Antes de recomendar una modificación, responde:

1. ¿La propuesta resuelve un problema real?
2. ¿Rompe una equivalencia ya validada?
3. ¿Aumenta el número de déficits?
4. ¿Consume créditos necesarios para otra asignatura?
5. ¿Complica la defensa del RAM?
6. ¿Existe una solución menos invasiva?

Si modifica una equivalencia validada, la carga de justificación es alta.

---

## Formato de salida obligatorio

```md
## [Código origen] — [Asignatura origen]

### Estado
- Estado actual:
- Observación del coordinador:
- Problema a resolver:

### Estrategia de comparación
- Estrategia utilizada:
- Motivo:

### Elementos esenciales de origen
- ...
- ...

### Matriz de cobertura
| Elemento | Prioridad | Evidencia destino | Cobertura | Nota |
|---|---|---|---|---|

### Créditos y restricciones
- ECTS origen:
- ECTS destino asignados:
- Déficit / sobrante:
- Semestre:
- Restricciones:
- Impacto en otros emparejamientos:

### Evaluación
- Clasificación:
- Fortalezas:
- Debilidades:
- Riesgo académico:
- Confianza:

### Recomendación
- Mantener / Ajustar créditos / Añadir complemento / Sustituir / Descartar
- Justificación breve y verificable:
```

---

## Regla para aceptar una equivalencia

Acepta una equivalencia solo si:

- los elementos esenciales están cubiertos de forma clara o razonablemente complementada;
- los huecos restantes no contradicen observaciones del coordinador;
- los créditos y restricciones son gestionables;
- la justificación se puede explicar sin exagerar;
- no existe un impacto negativo mayor sobre el RAM.

---

## Regla para rechazar una equivalencia

Recházala o clasifícala como insuficiente si:

- falta un elemento esencial;
- depende de un término parecido, pero no de contenido real;
- no hay evidencia documental;
- requiere créditos ya agotados o no utilizables;
- incumple una restricción objetiva;
- solo parece buena en embeddings o en el título.

---

## Condición de salida

La skill termina cuando cada candidato esté clasificado y exista una recomendación argumentada.

Pasa entonces a `03_ajustar_creditos.md` si el problema restante es de créditos, o a la skill de refinamiento del RAM si la recomendación exige un cambio.


## Recursos asociados

- `.agents/context/ulpgc.md`
- `.agents/context/ram_actual.md`
- `.agents/context/normas_ram.md`
- `.agents/context/lut.md`
- `.agents/context/subdirector.md`
- `.agents/context/herramientas.md`
- `.agents/casos/fesc.md`
- `.agents/casos/am4.md`
- `.agents/casos/master.md`
- `.agents/casos/mooc.md`
- `.agents/casos/descartadas.md`
- `.agents/scripts/README.md`
- `matcher.py`
