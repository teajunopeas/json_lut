# 📚 Guía de Uso: Matcher ULPGC ↔ LUT

## ¿Qué es esto?

Este programa te ayuda a **encontrar equivalencias** entre tus asignaturas de la ULPGC y cursos de la Universidad de Lund (LUT) en Suecia, durante tu Erasmus.

**No necesitas saber programación.** Solo abre una terminal y ejecuta el programa. ¡El menú hace el resto!

---

## 🚀 Cómo iniciar

### Opción 1: Doble clic (Windows)

Si ves un archivo llamado `run_matcher.bat`, simplemente haz doble clic.

### Opción 2: Línea de comandos

```bash
python matcher.py
```

---

## 📋 Menú Principal

Cuando el programa inicia, verás 7 opciones principales:

### 1️⃣ **Seleccionar asignatura**

- Elige una asignatura ULPGC de la lista
- El programa busca automáticamente cursos equivalentes en LUT
- Te muestra los mejores candidatos con su similitud (%)
- Puedes:
  - Ver detalles completos de cada candidato
  - Seleccionar uno para asignarlo
  - Escribir `c` para buscar **combinaciones** (múltiples cursos LUT juntos)

### 2️⃣ **Ver emparejamientos actuales**

Muestra una tabla con todas las asignaciones que has hecho:

- Qué curso ULPGC asignaste
- A qué curso(s) LUT
- Cuántos créditos llevan cada uno

### 3️⃣ **Estado de capacidad en cursos LUT**

Te muestra para cada curso LUT asignado:

- Cuántos créditos tiene disponibles
- Cuántos ya usaste
- Cuántos te quedan libres (%)

**Útil para:** saber si un curso LUT puede aceptar otra asignatura ULPGC sin sobrepasarse.

### 4️⃣ **Procesar obligatorias sin asignar**

- Busca automáticamente equivalencias para **todas** las asignaturas obligatorias que no hayas asignado aún
- Útil para empezar rápido
- Te irá preguntando para cada una

### 5️⃣ **Revisar todas las sin asignar**

- Como la opción 4, pero incluye también las **optativas** (si las tienes habilitadas en Configuración)
- Perfecto para terminar de emparejar todo

### 6️⃣ **Guardar resultados (JSON)**

- Exporta todas tus asignaciones a un archivo llamado `emparejamientos.json`
- Lo puedes enviar por email, compartir o guardar como copia de seguridad
- Formato legible y fácil de consultar

### 7️⃣ **Configuración**

- **Mostrar asignaturas optativas:** activa/desactiva si quieres ver optativas en el menú

---

## 💡 Consejos prácticos

### ¿Cómo funciona la búsqueda?

1. **FTS (Full-Text Search):** El programa busca palabras clave en inglés
2. **Embeddings semánticos:** Ordena resultados por similitud (machine learning)
3. **Porcentaje:** Muestra qué tan similar es cada candidato (ideal > 75%)

### ¿Qué es una "combinación"?

A veces **un curso ULPGC necesita 2 o 3 cursos LUT juntos** para cubrir todos los temas.

**Ejemplo:** "Análisis Matemático III (6 ECTS)" podría cubrirse con:

- "Fourier Analysis" (3 ECTS) + "Complex Analysis" (3 ECTS)

Cuando busques candidatos, escribe `c` para ver combinaciones disponibles.

### ¿Puedo asignar lo mismo varias veces?

**Sí.** Un curso LUT puede ser usado para múltiples asignaturas ULPGC siempre que tenga créditos disponibles.

Por ejemplo:

- Curso LUT "Engineering Mathematics" tiene 6 ECTS
- Lo asignas a ULPGC1 (4 ECTS)
- Te quedan 2 ECTS, ¡puedes usarlos para otra asignatura!

(Verifica en "Estado de capacidad" cuántos créditos quedan libres)

### ¿Cómo sé si la asignación es buena?

1. **Porcentaje de similitud** > 75%: generalmente es bueno
2. **Contenido comparable:** verifica manualmente si los temas se solapan
3. **Créditos compatibles:** ULPGC y LUT deben tener créditos similares

---

## 📁 Archivos generados

Después de usar el programa, encontrarás:

- **`emparejamientos.json`** — Tus asignaciones guardadas (opción 6 del menú)
- **`lut_courses.db`** — Base de datos de cursos LUT (no toques)
- **`ulpgc_courses.json`** — Lista de asignaturas ULPGC (no toques)

---

## ❓ Preguntas frecuentes

### P: ¿Puedo tener más de una asignatura ULPGC sin asignar?

**R:** Sí. El programa te deja trabajar con una y luego seguir con otra cuando lo desees.

### P: ¿Puedo deshacer una asignación?

**R:** El programa no tiene función "deshacer" integrada. Pero puedes:

1. Cerrar sin guardar (opción `q`)
2. O editar manualmente `emparejamientos.json`

### P: ¿El programa necesita internet?

**R:** No. Descarga el modelo de IA la primera vez, pero luego funciona offline.

### P: ¿Puedo usar esto en otro idioma?

**R:** El programa está en español/inglés. Los cursos LUT están en inglés en la base de datos.

### P: ¿Qué pasa si no encuentro equivalencias?

**R:** Algunas asignaturas ULPGC podrían no tener equivalentes en LUT. En ese caso:

1. Habla con tu coordinador Erasmus
2. Propón una asignatura alternativa
3. O pide reconocimiento de créditos sin equivalencia directa

---

## 🆘 ¿Necesitas ayuda?

Si algo no funciona:

1. Verifica que `lut_courses.db` existe en la carpeta
2. Verifica que `ulpgc_courses.json` existe
3. Intenta cerrar y abrir de nuevo el programa
4. Si persiste, contacta con tu coordinador Erasmus o el desarrollador

---

**¡Buena suerte con tu movilidad!** 🎓✨
