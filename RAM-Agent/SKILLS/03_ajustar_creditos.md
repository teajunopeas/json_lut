# Skill 03 — Ajustar créditos sin desestabilizar el RAM

## Propósito

Resolver déficits, sobrantes o repartos parciales de ECTS con el menor número posible de modificaciones y sin deteriorar equivalencias académicas ya aceptables.

Los scripts son la fuente de verdad para cálculos, capacidad restante y cursos ya utilizados. Esta skill interpreta y decide; no recalcula manualmente lo que pueda consultar la herramienta.

---

## Cuándo usar esta skill

Úsala cuando:

- haya más emparejamientos deficitarios de los permitidos;
- una equivalencia tenga contenido adecuado pero ECTS insuficientes;
- existan créditos sobrantes en una asignatura de destino;
- se necesite repartir una asignatura de destino entre varias asignaturas de origen;
- un cambio de contenidos afecte a la distribución de créditos.

No la uses para “mejorar” créditos si el RAM ya cumple las reglas y el cambio introduciría riesgo innecesario.

---

## Principios

1. **No sacrifiques contenido esencial para cuadrar créditos.**
2. **No rompas una equivalencia OK si existe un ajuste menos invasivo.**
3. **Primero mueve créditos sobrantes; después busca complementos; sustituye solo como último recurso.**
4. **No inventes créditos parciales sin una regla o evidencia que los permita.**
5. **Mantén trazabilidad exacta de cada ECTS usado.**

---

## Entradas necesarias

Antes de actuar, consulta y registra:

- número total de emparejamientos con déficit;
- máximo permitido por la norma aplicable;
- ECTS de cada asignatura de origen;
- ECTS de cada asignatura de destino;
- créditos ya asignados a cada curso de destino;
- capacidad libre de cada curso de destino;
- créditos sobrantes;
- asignaturas bloqueadas como OK;
- equivalencias `Justas` o `Aceptables con reserva`;
- restricciones de semestre, nivel o uso parcial;
- observaciones del coordinador sobre créditos.

---

## Clasificación de problemas de crédito

| Tipo | Definición |
|---|---|
| Déficit aislado | una equivalencia tiene menos ECTS de destino que de origen |
| Déficit acumulado | hay demasiadas equivalencias deficitarias, aunque cada una sea pequeña |
| Sobrante inutilizado | hay ECTS disponibles que no se están usando |
| Sobrecarga | una asignatura de destino tiene más créditos asignados de los que posee |
| Conflicto de reparto | un mismo curso se usa en varias equivalencias y el reparto no es compatible |
| Déficit estructural | no existen créditos compatibles suficientes sin cambiar asignaturas |

---

## Procedimiento

### Paso 1. Consultar el estado real

Ejecuta o usa la herramienta que muestre:

- emparejamientos actuales;
- capacidad por curso de destino;
- déficits;
- sobrantes;
- cursos compartidos;
- total de déficits frente al máximo permitido.

No hagas cambios antes de registrar una fotografía del estado inicial.

Formato:

```md
## Estado inicial de créditos

- Déficits actuales:
- Máximo permitido:
- Cursos con capacidad libre:
- Cursos sobreasignados:
- Equivalencias bloqueadas:
- Equivalencias ajustables:
```

---

### Paso 2. Ordenar los problemas por prioridad

Resuelve en este orden:

1. sobrecargas o errores objetivos;
2. exceso del número máximo de déficits;
3. déficits pequeños que pueden corregirse con sobrantes;
4. déficits de equivalencias `Justas`;
5. mejoras opcionales.

No intentes optimizar todos los déficits si la norma permite algunos y el ajuste adicional obligaría a romper equivalencias sólidas.

---

### Paso 3. Buscar ajustes de coste mínimo

Explora las soluciones en este orden, deteniéndote cuando encuentres una solución válida de menor impacto:

#### Opción A. Reasignar créditos libres de un curso ya usado

Usa capacidad libre de una asignatura de destino ya presente en el RAM, siempre que:

- el contenido también respalde la asignatura de origen que recibe esos créditos;
- no se perjudique otra equivalencia;
- el reparto sea defendible.

#### Opción B. Reasignar créditos sobrantes de un curso compatible

Mueve una parte de créditos desde una asignatura con sobrante a otra asignatura de origen, solo si el contenido lo justifica.

No muevas créditos como si fueran neutros: cada crédito debe tener una base académica.

#### Opción C. Añadir una asignatura complementaria pequeña

Busca una materia de destino que aporte tanto contenido como ECTS al hueco existente.

Es preferible cuando el hueco de contenido y el de crédito coinciden.

#### Opción D. Reconfigurar una equivalencia ajustable

Modifica una equivalencia marcada como `Justa` o `Aceptable con reserva`, pero solo si mejora el conjunto y no empeora el contenido esencial.

#### Opción E. Sustituir una equivalencia

Solo como último recurso. Requiere explicar por qué no funcionaban las opciones anteriores.

---

### Paso 4. Calcular el impacto de cada alternativa

Para cada alternativa, registra:

| Criterio | Pregunta |
|---|---|
| Déficits | ¿reduce el número de déficits? |
| Contenido | ¿mantiene o mejora la cobertura? |
| Estabilidad | ¿modifica una equivalencia validada? |
| Reparto | ¿crea conflictos de créditos compartidos? |
| Restricciones | ¿respeta semestre, nivel y reglas? |
| Complejidad | ¿es fácil de explicar y mantener? |

Clasifica el impacto como:

- Muy bajo;
- Bajo;
- Medio;
- Alto;
- Inaceptable.

---

### Paso 5. Elegir la solución

Cuando varias alternativas sean válidas, aplica estas prioridades:

1. menor número de cambios;
2. no tocar equivalencias OK;
3. no reducir cobertura de contenidos;
4. reducir el exceso de déficits;
5. solución fácil de defender;
6. mantener la distribución razonable entre semestres.

No elijas una solución solo porque deje todos los déficits en cero si empeora la calidad global.

---

## Formato de salida obligatorio

```md
## Ajuste de créditos — [asignatura o bloque]

### Estado inicial
- Déficit/sobrante:
- Número total de déficits:
- Máximo permitido:
- Cursos de destino implicados:

### Restricción académica
- Qué contenidos deben mantenerse:
- Qué equivalencias no deben tocarse:
- Reglas de crédito aplicables:

### Alternativas evaluadas

#### Alternativa A — [nombre]
- Cambio:
- Créditos antes / después:
- Contenido afectado:
- Impacto en otros emparejamientos:
- Riesgo:
- Resultado: aceptar / descartar
- Motivo:

#### Alternativa B — [nombre]
...

### Decisión
- Ajuste elegido:
- Déficits antes / después:
- Cambios realizados:
- Justificación:

### Trazabilidad
- Créditos reasignados:
- De:
- A:
- Motivo académico:
- Herramienta o salida consultada:
```

---

## Qué no hacer

Nunca:

- reasignes créditos sin explicar qué contenido los respalda;
- uses más ECTS de un curso de destino de los que existen;
- ignores créditos ya comprometidos;
- “arregles” un déficit creando otro oculto;
- toques una equivalencia OK sin registrar la razón;
- supongas que cualquier fracción de créditos es aceptable;
- conviertas una asignatura insuficiente en válida añadiendo solo ECTS.

---

## Condición de salida

La skill termina cuando:

- el número de déficits cumple la regla aplicable; o
- se ha demostrado que no puede reducirse sin empeorar el RAM.

En el segundo caso, no fuerces cambios. Deja el problema abierto y explica:

```text
No se recomienda realizar un ajuste adicional porque las alternativas disponibles reducirían la cobertura académica o afectarían a equivalencias ya validadas.
```
