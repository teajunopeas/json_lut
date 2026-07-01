# Skill 01 — Buscar candidatos

## Propósito

Generar una lista corta y útil de asignaturas de destino que **podrían** servir para cubrir una asignatura de origen o un hueco concreto del RAM.

Esta skill sirve para explorar. No decide equivalencias ni modifica el RAM.

---

## Cuándo usar esta skill

Úsala cuando ocurra al menos una de estas situaciones:

- una asignatura de origen no tiene todavía emparejamiento;
- una equivalencia existente tiene un hueco de contenidos o resultados;
- hace falta buscar una asignatura complementaria para resolver créditos;
- el coordinador ha señalado una carencia concreta;
- se quiere comprobar si existe una alternativa claramente mejor.

No la uses para buscar sustitutos de una equivalencia marcada como válida si no hay un problema real que resolver.

---

## Entradas necesarias

Antes de buscar, reúne:

1. **Asignatura de origen**
   - código;
   - nombre;
   - ECTS;
   - semestre;
   - guía docente o ficha académica;
   - resultados de aprendizaje, contenidos, competencias y prerrequisitos disponibles.

2. **Objetivo de la búsqueda**
   - asignatura nueva;
   - complemento de contenidos;
   - complemento de créditos;
   - alternativa a una equivalencia débil;
   - cobertura de una observación del coordinador.

3. **Restricciones**
   - universidad de destino;
   - semestre o periodo de movilidad;
   - nivel permitido: grado, máster, MOOC u otro;
   - ECTS disponibles;
   - asignaturas de destino ya usadas y créditos ya asignados;
   - reglas del centro de origen.

4. **Estado del RAM**
   - si existe una equivalencia actual;
   - anotaciones del coordinador;
   - déficits y sobrantes de créditos;
   - qué partes no deben tocarse.

---

## Regla principal

No busques por el nombre de la asignatura solamente.

Los nombres sirven para encontrar candidatos iniciales, pero la selección debe partir de los conceptos académicos que realmente deben cubrirse.

Ejemplo:

- No buscar solo `Análisis Matemático IV`.
- Extraer primero conceptos como:
  - medida;
  - integración;
  - espacios de medida;
  - funciones medibles;
  - convergencia;
  - análisis de Fourier;
  - espacios funcionales.

---

## Procedimiento

### Paso 1. Delimitar el problema

Escribe una frase precisa que defina lo que se busca.

Formato:

```text
Necesito encontrar una asignatura LUT que cubra [hueco concreto] para [asignatura ULPGC], sin [restricción relevante].
```

Ejemplos:

```text
Necesito encontrar una asignatura LUT que cubra física estadística y sistemas cuánticos para FESC, sin utilizar asignaturas no accesibles en el periodo de movilidad.
```

```text
Necesito encontrar créditos complementarios para reducir un déficit sin modificar emparejamientos ya validados.
```

No pases al paso siguiente si el problema no está delimitado.

---

### Paso 2. Extraer conceptos de búsqueda

Genera cuatro grupos de términos:

| Grupo | Qué contiene |
|---|---|
| Núcleo | conceptos imprescindibles sin los cuales la equivalencia no sería defendible |
| Relacionados | conceptos cercanos que pueden aportar cobertura parcial |
| Métodos | técnicas, herramientas, modelos o formalismos |
| Aplicaciones | ámbitos aplicados que pueden indicar una asignatura útil |

Incluye sinónimos y terminología inglesa.

Ejemplo de estructura:

```text
Núcleo:
- statistical physics
- quantum systems
- canonical ensemble
- partition function

Relacionados:
- thermodynamics
- complex systems
- phase transitions
- fluctuations

Métodos:
- Boltzmann distribution
- Monte Carlo
- kinetic theory

Aplicaciones:
- materials
- condensed matter
- physical modelling
```

No confundas términos relacionados con cobertura suficiente. Que una materia tenga “thermodynamics” no implica que cubra física estadística.

---

### Paso 3. Consultar primero las herramientas

Usa los scripts o la base de datos del proyecto antes de buscar manualmente.

El flujo recomendado es:

1. Consultar el estado actual del RAM.
2. Consultar créditos disponibles o ya utilizados.
3. Buscar por los términos núcleo.
4. Buscar por combinaciones de términos relacionados.
5. Revisar candidatos manuales que no aparezcan bien posicionados por embeddings.
6. Abrir o recuperar el detalle real de los mejores candidatos.

No asumas que el orden de similitud semántica representa la calidad de la equivalencia.

La similitud sirve para descubrir; el detalle de la guía sirve para evaluar.

---

### Paso 4. Clasificar candidatos rápidamente

Para cada candidato encontrado, clasifícalo inicialmente:

| Clasificación | Uso |
|---|---|
| Prioritario | Parece cubrir directamente el núcleo del problema |
| Complementario | Cubre una parte concreta, pero no todo |
| Dudoso | Tiene palabras parecidas, pero falta evidencia de contenido |
| Descartado | No cubre lo imprescindible o incumple restricciones |

No redactes todavía una equivalencia final.

---

### Paso 5. Aplicar filtros obligatorios

Descarta o marca como no utilizable todo candidato que incumpla alguno de estos puntos:

- se imparte fuera del periodo de movilidad;
- no es accesible por nivel, prerrequisitos o reglamento;
- no tiene ECTS utilizables;
- ya está totalmente consumido en otra equivalencia;
- depende de contenidos que el estudiante no puede acreditar;
- su guía no proporciona evidencia suficiente;
- solo coincide por palabras generales o por el nombre.

Si hay incertidumbre, no lo declares válido: clasifícalo como `Dudoso`.

---

### Paso 6. Preparar la lista corta

La salida de esta skill debe contener entre 3 y 8 candidatos como máximo, salvo que haya muy poca oferta.

Para cada candidato, aporta:

```md
### [Código] — [Nombre]

- Semestre:
- ECTS:
- Nivel:
- Fuente:
- Conceptos cubiertos:
- Conceptos que no cubre:
- Restricciones detectadas:
- Clasificación: Prioritario / Complementario / Dudoso / Descartado
- Motivo breve:
```

Ordena los candidatos así:

1. los que cubren directamente el núcleo;
2. los que complementan el hueco principal;
3. los que ayudan a resolver créditos;
4. los dudosos, separados claramente.

---

## Qué no hacer

Nunca:

- decidas una equivalencia definitiva durante la búsqueda;
- uses el porcentaje de embeddings como justificación académica;
- uses una asignatura por tener un nombre parecido;
- ignores el semestre o los ECTS;
- modifiques el RAM en esta fase;
- ocultes candidatos descartados que puedan volver a aparecer en otra búsqueda.

---

## Condición de salida

Esta skill termina cuando exista una lista corta, trazable y filtrada de candidatos.

Pasa entonces a `02_evaluar_equivalencia.md`.

Si no hay candidatos suficientes, informa claramente:

```text
No se ha encontrado una alternativa defendible con la información disponible.
Se recomienda ampliar fuentes, revisar el catálogo manualmente o mantener la equivalencia actual.
```
