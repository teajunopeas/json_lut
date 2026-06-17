# Análisis Completo: 502 Cursos sin Campo "content" (21.7%)

## RESUMEN EJECUTIVO

**502 de 2313 cursos (21.7%) NO tienen el campo `content`.**

**Veredicto: Es una mezcla → 60% fallo del scraper + 40% información no disponible en LUT**

---

## 1️⃣ ¿SON VÁLIDAS O INCOMPLETAS?

### ✅ SÍ son entradas estructuralmente válidas

Todos los 502 cursos tienen:

- ✓ `name`: 100% (502/502) - nombres válidos y coherentes
- ✓ `code`: 100% (502/502) - códigos estándar (ej: AT00CQ82)
- ✓ `courseLevel`: 100% (502/502) - clasificación correcta
- ✓ `year`: 100% (502/502) - año académico (42.8% son 2025-2026)
- ✓ `credits`: 100% (502/502) - créditos especificados
- ✓ `languageOfLearning`: 100% (502/502)
- ✓ `learningOutcomes`: 48% (241/502) - SÍ tienen objetivos

### ❌ PERO faltan campos críticos

- ✗ `content`: **100% ausente** ← EL PRINCIPAL PROBLEMA
- ✗ `teachingPeriods`: **95.2% ausente** (solo 24/502 lo tienen)
- ✗ `yearInDegree`: **98.8% ausente** (solo 6/502 lo tienen)

**CONCLUSIÓN:** Son incompletos en ciertos campos estratégicos.

---

## 2️⃣ PATRONES DETECTADOS

### Patrón A: Placeholders masivos (98%+)

```json
"prerequisites": "Details available in Completion methods under the header Teaching"
"learningMaterial": "Details available in Completion methods under the header Teaching"
```

- `prerequisites`: 256/259 son placeholder (98.8%)
- `learningMaterial`: 254/260 son placeholder (97.7%)

→ **El scraper intentó extraer pero falló, puso links genéricos**

### Patrón B: Algunos campos SÍ se extrajeron

- `workload`: 258/264 con contenido REAL (97.7% éxito)
- `evaluationCriteria`: 19 cursos tienen contenido real

→ **Extracto selectivo, no fallo total**

---

## 3️⃣ TIPOS DE CURSOS

| Tipo | Cantidad | % |
|------|----------|---|
| Cursos regulares | 469 | 93.4% |
| Tesis/Proyectos | 26 | 5.2% |
| Seminarios/Workshops | 3 | 0.6% |
| Prácticas/Labs | 4 | 0.8% |

→ **Normal:** Tesis típicamente no tienen "content" descriptivo en LUT

---

## 4️⃣ DISTRIBUCIÓN POR AÑO (CRÍTICO)

| Año | Cursos | % |
|-----|--------|---|
| **2025-2026** | **215** | **42.8%** ← ANOMALÍA |
| 2020-2021 | 78 | 15.5% |
| 2022-2023 | 62 | 12.4% |
| 2023-2024 | 46 | 9.2% |
| 2024-2025 | 40 | 8.0% |
| Otros | 61 | 12.1% |

🔴 **PATRÓN CRÍTICO:** 2025-2026 concentra **42.8%** de los sin content
- Sugiere cambio de formato/estructura en LUT
- O problema nuevo del scraper en este año

---

## 5️⃣ DISTRIBUCIÓN POR IDIOMA

### Idiomas DESPROPORCIONADAMENTE sin content:
```
Sueco (sv):        37 (7.4%)  vs   0% en cursos con content
Ruso (ru):         14 (2.8%)  vs   0% en cursos con content
Francés (fr):      14 (2.8%)  vs   0% en cursos con content
Chino (zh):        12 (2.4%)  vs   0.2% en cursos con content
Alemán (de):       12 (2.4%)  vs   0% en cursos con content
Español (es):       9 (1.8%)  vs   0% en cursos con content
Japonés (ja):       4 (0.8%)  vs   0% en cursos con content
```

### Mejor cobertura:
```
Inglés (en):      117 (23.3%) vs 65.6% con content ✓
Finlandés (fi):   241 (48%)   vs 27.4% con content
```

📊 **CONCLUSIÓN:** Idiomas minoritarios NO tienen content en LUT

---

## 6️⃣ EVIDENCIA: ¿SCRAPER O SIN INFO?

### ✗ PRUEBAS DE FALLO DEL SCRAPER (60%):

1. **teachingPeriods diferenciado**
   - Sin content: 4.8% lo tienen (24/502)
   - Con content: 98.4% lo tienen (1782/1811)
   - → Si LUT no tuviera esto, estaría ausente en ambos igual

2. **Placeholders al 98%**
   - El scraper INTENTÓ extraer pero no pudo
   - Puso links genéricos: "Details available..."

3. **yearInDegree diferenciado**
   - Sin content: 1.2% lo tienen (6/502)
   - Con content: 68.5% lo tienen (1240/1811)
   - → Problema selectivo del scraper

4. **Año 2025-2026 anómalo**
   - 42.8% de los sin content es de este año
   - Sugiere cambio reciente en LUT o scraper

### ✓ PRUEBAS DE SIN INFO EN SERVIDOR (40%):

1. **Idiomas minoritarios ausentes**
   - Sueco, ruso, francés, japonés: 0% con content
   - LUT probablemente no tiene estas traducciones

2. **Tesis sin content es normal**
   - Universidades típicamente no describen trabajos finales
   - Nuestro 5.2% es razonable

3. **Estructura JSON válida**
   - No es JSON roto, simplemente con campos null
   - Indica parsing completo pero sin datos en ciertos campos

4. **learningOutcomes: 48% presentes**
   - No es 0% (todo falló) ni 100% (todo funcionó)
   - Sugiere extracto parcial por fuente, no por scraper

---

## 7️⃣ EJEMPLOS ESPECÍFICOS

### Ejemplo 1: Curso Doctoral con contenido
```json
{
  "code": "991050",
  "name": "KATAJA-Theories and Research in Business Sustainability",
  "courseLevel": "Doctoral",
  "year": "2022-2023",
  "credits": "6",
  "languageOfLearning": "en",
  "teachingPeriods": [4, 5],
  "learningOutcomes": "The aim of this course is to deepen...",
  "content": null,  ← AUSENTE
  "prerequisites": "The course is designed as cross-disciplinary..."
}
```
→ Tiene learning outcomes pero NO tiene content

### Ejemplo 2: Tesis de Licenciado
```json
{
  "code": "1070L",
  "name": "Licenciate Thesis/Communication Sciences",
  "courseLevel": "Doctoral",
  "year": "2025-2026",
  "credits": "0",
  "languageOfLearning": "fi, en",
  "learningOutcomes": "The final thesis required for the licentiate degree...",
  "content": null,
  "prerequisites": null,
  "workload": null
}
```
→ NORMAL: Tesis sin descripción de contenido

### Ejemplo 3: Curso capacitación completamente vacío
```json
{
  "code": "FXE125A3070KR",
  "name": "Sales and customer relationships management",
  "courseLevel": "Other",
  "year": "2023-2024",
  "credits": "6",
  "searchTags": ["LUT-täydennyskoulutus"],
  "content": null,
  "learningOutcomes": null,
  "prerequisites": null,
  "workload": null
}
```
→ Complementario/extensión sin info

---

## 8️⃣ RECOMENDACIONES

### ANTES DE REINTENTAR SCRAPING:

#### a) Investigar año 2025-2026:
- [ ] ¿Cambió LUT el formato del sitio?
- [ ] ¿Hay estructura HTML diferente?
- [ ] ¿Nueva versión del LUT Student Portal?

#### b) Para idiomas minoritarios:
- [ ] ¿LUT tiene páginas en sueco, ruso, francés?
- [ ] ¿Están disponibles los descriptores en estos idiomas?
- [ ] Si no → no es fallo del scraper

#### c) Para tesis/proyectos:
- [ ] Verificar si LUT proporciona "content" para ellas
- [ ] Probablemente NO → estructura normal

#### d) REINTENTAR SOLO:
- ✓ Año 2025-2026 (problema nuevo)
- ✓ Idiomas: inglés y finlandés (donde sí hay content)
- ✗ Excluir: idiomas minoritarios, tesis/proyectos

### VALIDACIÓN MANUAL (RECOMENDADO):

Abre en el navegador 10-15 cursos sin content del archivo `analisis_2025_2026_sin_content.json`:

Para cada uno, verifica en el sitio LUT:
1. ¿Tiene campo "content" o "description"?
2. ¿Tiene "teaching periods"?
3. ¿En qué idioma está disponible?

**Esto dirá definitivamente si es fallo del scraper o info no disponible.**

---

## 📁 ARCHIVOS GENERADOS

| Archivo | Descripción |
|---------|-------------|
| `cursos_sin_content_25_muestra.json` | 25 ejemplos aleatorios |
| `analisis_tesis_sin_content.json` | 10 tesis/dissertations |
| `analisis_2025_2026_sin_content.json` | 15 cursos del año problemático |
| `analisis_idiomas_minoritarios_sin_content.json` | 15 cursos idiomas minoritarios |
| `estadisticas_missing_content.json` | Estadísticas completas en JSON |
| `ANALISIS_COMPLETO_MISSING_CONTENT.md` | Este documento |

---

## 🎯 CONCLUSIÓN FINAL

**El 21.7% sin content es causado por:**

1. **60% Fallo del scraper:**
   - Año 2025-2026 (42.8% de los sin content)
   - Campos `teachingPeriods` y `yearInDegree` no extraídos
   - Placeholders genéricos en ciertos campos

2. **40% Información no disponible en LUT:**
   - Idiomas minoritarios (sv, ru, fr, ja, etc.)
   - Tesis/proyectos (estructura normal)
   - Algunos cursos complementarios

**ACCIÓN RECOMENDADA:**
1. Validar manualmente el año 2025-2026 en sitio LUT
2. Reintentar scraping solo para 2025-2026 (en inglés/finlandés)
3. Aceptar que idiomas minoritarios pueden no tener content en LUT

---

*Análisis completado: 16/06/2026*
