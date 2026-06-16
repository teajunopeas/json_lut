"""Scraper para el catálogo de cursos de LUT SISU.

Este módulo consulta el API de búsqueda de Sisu (`course-unit-search`) y
extrae los detalles de cada asignatura sin recortar la información cruda.

DOCUMENTACIÓN DE ENDPOINTS DEL API
===================================

ENDPOINT 1: course-unit-search
URL: https://sisu.lut.fi/kori/api/course-unit-search
Método: GET

Parámetros de entrada:
- fullTextQuery (str): término de búsqueda
- universityOrgId (str): ID de organización (ej: "lut-university-root-id")
- start (int): índice de inicio para paginación (default 0)
- limit (int): número máximo de resultados (default 50)

Campos de respuesta top-level:
- start (int): índice de inicio usado en la solicitud
- limit (int): número límite usado en la solicitud
- total (int): número total de resultados disponibles
- truncated (bool): true si hay más resultados de los returnados
- searchResults (array): lista de cursos encontrados (ver SEARCH_RESULT)
- notifications (array): mensajes o advertencias del servidor

---

SEARCH_RESULT: Estructura de cada elemento en searchResults (17 campos)
Campos principales:
- id (str): identificador único del curso (UUID)
- code (str): código de la asignatura (ej: "MAT101")
- name (object): nombre del curso con localización (keys: en, fi, sv, ...)
- credits (object): créditos con estructura {min, max}
- lang (str): idioma principal (código ISO 639-1: "en", "fi", "sv", etc.)
- organisations (array): organizaciones asociadas

Campos adicionales disponibles:
- learningOutcomes (object): resultados de aprendizaje localizados
- outcomes (object): alternativa de learningOutcomes
- content (object): contenido del curso localizado
- studyLevel (object): nivel del estudio (Bachelor, Master, etc.)
- courseUnitType (str): tipo de unidad de curso
- courseType (str): tipo de curso (lecture, lab, seminar, etc.)
- activityPeriods (array): períodos de actividad [{startDate, endDate}, ...]
- prerequisites (object): requisitos previos localizados
- equivalentCoursesInfo (object): información de cursos equivalentes

---

ENDPOINT 2: course-units/{id}
URL: https://sisu.lut.fi/kori/api/course-units/{course_id}
Método: GET

Campos de respuesta del detalle (~45 campos):
Identificadores y códigos:
- id (str): identificador único (UUID)
- code (str): código de la asignatura

Información básica:
- name (object): nombre localizado {en, fi, sv, ...}
- credits (object): {min (int), max (int)} - rango de créditos
- scope (str): alcance del curso

Contenido educativo:
- learningOutcomes (object): resultados de aprendizaje localizados
- outcomes (object): alternativa de learningOutcomes
- content (object): descripción del contenido localizada
- objectives (object): objetivos del curso localizados
- abstract (object): resumen del curso

Idiomas y nivel:
- lang (str): idioma principal (ISO 639-1)
- possibleAttainmentLanguages (array): idiomas de impartición posibles
- attainmentLanguageUrns (array): URNs de idiomas de impartición
- languageUrns (array): URNs de idiomas disponibles
- studyLevel (object): nivel (Bachelor, Master, Doctoral, etc.)
- courseUnitType (str): tipo de unidad
- courseType (str): clasificación del tipo de curso
- status (str): estado (ACTIVE, ARCHIVED, DRAFT, etc.)

Períodos y validez:
- validityPeriod (object): {startDate, endDate} - período de validez
- activityPeriods (array): períodos de actividad [{startDate, endDate}, ...]
- curriculumPeriodIds (array): IDs de períodos de currículo

Detalles pedagógicos:
- prerequisites (object): requisitos previos localizados
- equivalentCoursesInfo (object): información de equivalencias
- assessmentMethods (array): métodos de evaluación
- gradeScaleId (str): escala de calificación

Estructura organizacional:
- organisations (array): organizaciones responsables
- teachingLanguages (array): idiomas de impartición
- teacherResponsibilities (array): responsables de enseñanza

Metadata:
- createdDate (str): fecha de creación (ISO 8601)
- modifiedDate (str): fecha de última modificación (ISO 8601)
- corequisites (array): co-requisitos
- restrictionInfo (str): información de restricciones

Campos opcionales adicionales que pueden variar según el curso:
- implementationTemplate (object): plantilla de implementación
- courseUnitClass (str): clase de unidad de curso
- minMaxStudents (object): {min, max} de estudiantes
- substitutionEligibility (str): elegibilidad de sustitución

---

MAPEO DE CAMPOS: API → JSON OUTPUT
==================================

Campo JSON         ← Fuentes en API (prioridad)
---------------------
id                 ← id
code               ← code
name               ← name (localizada en>fi>sv)
credits            ← credits.min/max (formatea como "N" o "N+M")
learningOutcomes   ← learningOutcomes OR outcomes (limpieza HTML)
content            ← content (limpieza HTML)
courseLevel        ← studyLevel OR courseUnitType OR courseType
languageOfLearning ← possibleAttainmentLanguages OR attainmentLanguageUrns
                     OR languageUrns OR lang (extrae de URNs)
year               ← curriculumPeriodIds OR validityPeriod.startDate
                     OR activityPeriods[] (busca patrón YYYY-YYYY)
coursePeriod       ← curriculumPeriodIds OR validityPeriod OR activityPeriods
prerequisites      ← prerequisites (limpieza HTML)
equivalentCoursesInfo ← equivalentCoursesInfo (limpieza HTML)
rawDetail          ← (objeto completo si --include-raw-detail)
"""

import argparse
import json
import re
from html import unescape
from typing import Any, Dict, Iterable, List, Optional

import requests

SEARCH_URL = "https://sisu.lut.fi/kori/api/course-unit-search"
DETAIL_URL = "https://sisu.lut.fi/kori/api/course-units/"

DEFAULT_QUERIES = [
    *[chr(code) for code in range(ord("A"), ord("Z") + 1)],
    *[str(digit) for digit in range(10)],
    "Å",
    "Ä",
    "Ö",
    "å",
    "ä",
    "ö",
    "physics",
    "mathematics",
    "computer",
    "data",
    "engineering",
    "algorithm",
    "programming",
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:151.0) Gecko/20100101 Firefox/151.0",
    "X-Sisu-Frontend-Info": "STUDENT/v12.0.2",
}

LANGUAGE_URN_PREFIX = "urn:code:language:"


def clean_html(value: Optional[str]) -> str:
    if not value:
        return ""
    text = unescape(value)
    text = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"&nbsp;", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def choose_localized_text(field: Any) -> Optional[str]:
    if isinstance(field, dict):
        for key in ("en", "fi", "sv"):
            candidate = field.get(key)
            if candidate:
                return clean_html(str(candidate))
        for candidate in field.values():
            if candidate:
                return clean_html(str(candidate))
    elif isinstance(field, str):
        return clean_html(field)
    elif isinstance(field, list):
        return clean_html(" ".join(str(item) for item in field if item))
    return None

def parse_credits(credits: Any) -> Optional[str]:
    if not isinstance(credits, dict):
        return None
    minimum = credits.get("min")
    maximum = credits.get("max")
    if minimum is None and maximum is None:
        return None
    if minimum is not None and maximum is not None and minimum == maximum:
        return str(minimum)
    return "+".join(str(value) for value in (minimum, maximum) if value is not None)

def parse_year(period_ids: Any) -> Optional[str]:
    """Extrae un año o rango de año desde diferentes estructuras del detalle."""
    if isinstance(period_ids, dict):
        period_ids = [period_ids.get("startDate"), period_ids.get("endDate")]
    if isinstance(period_ids, str):
        period_ids = [period_ids]
    if not isinstance(period_ids, list):
        return None
    for period_id in period_ids:
        if not isinstance(period_id, str):
            continue
        match = re.search(r"(\d{4}-\d{4})", period_id)
        if match:
            return match.group(1)
        match = re.search(r"(\d{4})", period_id)
        if match:
            return match.group(1)
    return None

def parse_language(urns: Any) -> Optional[str]:
    """Normaliza idiomas desde URNs o valores de campo simples."""
    if isinstance(urns, dict):
        urns = [urns.get("language") or urns.get("code")]
    if isinstance(urns, str):
        urns = [urns]
    if not isinstance(urns, list):
        return None
    languages = []
    for urn in urns:
        if not isinstance(urn, str):
            continue
        if urn.startswith(LANGUAGE_URN_PREFIX):
            language = urn[len(LANGUAGE_URN_PREFIX):]
        else:
            language = urn
        languages.append(language)
    return ", ".join(dict.fromkeys(languages)) if languages else None

STUDY_LEVEL_MAP = {
    "basic-studies": "Bachelor",
    "bachelor": "Bachelor",
    "intermediate-studies": "Intermediate",
    "intermediate": "Intermediate",
    "advanced-studies": "Master",
    "master": "Master",
    "postgraduate-studies": "Doctoral",
    "doctoral": "Doctoral",
    "other-studies": "Other",
    "other": "Other",
}

def parse_study_level(value: Any) -> Optional[str]:
    """Traduce a formato legible el nivel de estudio."""
    if not isinstance(value, str):
        return choose_localized_text(value)
    key = value.split(":")[-1].lower()
    return STUDY_LEVEL_MAP.get(key, key)

def parse_teaching_periods(detail: Dict[str, Any]) -> Optional[List[int]]:
    """Extrae el periodo de impartición a partir del repeatPossibility."""
    periods = set()
    for method in detail.get("completionMethods", []):
        for repeat in method.get("repeats", []):
            for rp in repeat.get("repeatPossibility", []):
                parts = rp.split("/")
                if len(parts) >= 4:
                    try:
                        x, y = int(parts[2]), int(parts[3])
                        periods.add(x * 3 + y)  # 0/1 -> 1er, 0/2 -> 2do, 1/0 -> 3er, 1/1 -> 4to
                    except ValueError:
                        pass
    return sorted(periods) or None

def get_course_period(detail: Dict[str, Any]) -> Optional[str]:
    """Devuelve el período en que se cursa la asignatura."""
    if isinstance(detail.get("curriculumPeriodIds"), list):
        periods = [str(item) for item in detail.get("curriculumPeriodIds") if isinstance(item, str)]
        if periods:
            return ", ".join(periods)
    
    validity = detail.get("validityPeriod")
    if isinstance(validity, dict):
        start = validity.get("startDate")
        end = validity.get("endDate")
        if start and end:
            return f"{start} - {end}"
        if start:
            return start
        if end:
            return end

    activity_periods = detail.get("activityPeriods")
    if isinstance(activity_periods, list):
        ranges = []
        for activity in activity_periods:
            if isinstance(activity, dict):
                start = activity.get("startDate")
                end = activity.get("endDate")
                if start and end:
                    ranges.append(f"{start} - {end}")
                elif start:
                    ranges.append(start)
                elif end:
                    ranges.append(end)
        if ranges:
            return ", ".join(ranges)

    return None

def build_headers(cookie: Optional[str] = None) -> Dict[str, str]:
    """Construye los encabezados HTTP, añadiendo la cookie si se proporciona."""
    headers = HEADERS.copy()
    if cookie:
        headers["Cookie"] = cookie
    return headers

def detail_to_record(detail: Dict[str, Any], include_raw: bool = False) -> Dict[str, Any]:
    """Convierte un detalle de curso en un registro limpio para JSON.

    Campos extraídos:

    Identificadores:
    - id, code: identificadores únicos de la asignatura
    - name: nombre (localizado, preferencia: en > fi > sv)

    Académico:
    - credits: créditos (formato: "N" o "N+M" si min != max)
    - courseLevel: nivel de estudio legible (Bachelor/Intermediate/Master/Doctoral/Other),
                mapeado desde el URN en 'studyLevel'
    - year: curso académico (formato "YYYY-YYYY", desde 'curriculumPeriodIds' o 'validityPeriod')
    - coursePeriod: período(s) de actividad del curso
    - languageOfLearning: idioma(s) de impartición (desde 'possibleAttainmentLanguages')

    Etiquetas:
    - searchTags: lista de etiquetas libres del curso (desde 'searchTags')
    - isExchangeCourse: True si 'Exchange studies' está entre los searchTags
    - yearInDegree: año en el grado si aparece en searchTags (ej. "Year 1"), None si no

    Contenido educativo:
    - learningOutcomes: resultados de aprendizaje (desde 'outcomes' o 'learningOutcomes')
    - content: descripción del contenido del curso
    - prerequisites: requisitos previos
    - learningMaterial: materiales y recursos del curso

    Evaluación:
    - evaluationCriteria: criterios y pesos de evaluación (desde 'completionMethods[0]')
    - workload: desglose de horas de trabajo (desde 'completionMethods[0].description')

    Otros:
    - equivalentCoursesInfo: información sobre cursos equivalentes (cobertura ~6%)
    - rawDetail: (opcional, si include_raw=True) JSON completo sin procesar
    """
    completion = (detail.get("completionMethods") or [{}])[0]

    record = {
        # — Identificadores —
        "id":                   detail.get("id"),
        "code":                 detail.get("code"),
        "name":                 choose_localized_text(detail.get("name")),

        # — Académico —
        "credits":              parse_credits(detail.get("credits")),
        "courseLevel":          parse_study_level(
                                    detail.get("studyLevel")
                                    or detail.get("courseUnitType")
                                    or detail.get("courseType")
                                ),
        "year":                 parse_year(
                                    detail.get("curriculumPeriodIds")
                                    or detail.get("validityPeriod")
                                    or detail.get("activityPeriods")
                                    or []
                                ),
        "teachingPeriods":      parse_teaching_periods(detail),
        "coursePeriod":         get_course_period(detail),
        "languageOfLearning":   parse_language(
                                    detail.get("possibleAttainmentLanguages")
                                    or detail.get("attainmentLanguageUrns")
                                    or detail.get("languageUrns")
                                    or detail.get("lang")
                                ),

        # — Etiquetas —
        "searchTags":           detail.get("searchTags") or [],
        "isExchangeCourse":     "Exchange studies" in (detail.get("searchTags") or []),
        "yearInDegree":         next(
                                    (t for t in (detail.get("searchTags") or []) if t.startswith("Year")),
                                    None
                                ),

        # — Contenido educativo —
        "learningOutcomes":     choose_localized_text(detail.get("learningOutcomes") or detail.get("outcomes")),
        "content":              choose_localized_text(detail.get("content")),
        "prerequisites":        choose_localized_text(detail.get("prerequisites")),
        "learningMaterial":     choose_localized_text(detail.get("learningMaterial")),

        # — Evaluación —
        "evaluationCriteria":   choose_localized_text(completion.get("evaluationCriteria")),
        "workload":             choose_localized_text(completion.get("description")),

        # — Equivalencias —
        "equivalentCoursesInfo": choose_localized_text(detail.get("equivalentCoursesInfo")),
    }

    if include_raw:
        record["rawDetail"] = detail

    return record


def search_courses(
    session: requests.Session,
    query: str,
    university_org_id: str,
    start: int,
    limit: int,
    cookie: Optional[str] = None,
) -> Dict[str, Any]:
    params = {
        "fullTextQuery": query,
        "universityOrgId": university_org_id,
        "start": start,
        "limit": limit,
    }
    response = session.get(SEARCH_URL, params=params, headers=build_headers(cookie), timeout=30)
    response.raise_for_status()
    return response.json()


def fetch_course_detail(
    session: requests.Session,
    course_id: str,
    cookie: Optional[str] = None,
) -> Dict[str, Any]:
    response = session.get(f"{DETAIL_URL}{course_id}", headers=build_headers(cookie), timeout=30)
    response.raise_for_status()
    return response.json()


def collect_course_ids(
    session: requests.Session,
    queries: Iterable[str],
    university_org_id: str,
    page_limit: int,
    max_pages: int,
    cookie: Optional[str] = None,
) -> List[str]:
    ids: List[str] = []
    seen = set()
    for query in queries:
        start = 0
        for _ in range(max_pages):
            data = search_courses(session, query, university_org_id, start, page_limit, cookie)
            results = data.get("searchResults") or []
            if not results:
                break
            for item in results:
                course_id = item.get("id")
                if course_id and course_id not in seen:
                    seen.add(course_id)
                    ids.append(course_id)
            if len(results) < page_limit:
                break
            start += page_limit
    return ids


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Scrapea el catálogo de cursos de LUT SISU y exporta los resultados a JSON.",
    )
    parser.add_argument(
        "--university-org-id",
        default="lut-university-root-id",
        help="ID de organización para la búsqueda (por defecto lut-university-root-id).",
    )
    parser.add_argument(
        "--cookie",
        default=None,
        help="Cookie HTTP opcional cuando el endpoint la exige.",
    )
    parser.add_argument(
        "--queries",
        nargs="*",
        default=DEFAULT_QUERIES,
        help="Lista de consultas para barrer el catálogo.",
    )
    parser.add_argument(
        "--page-limit",
        type=int,
        default=50,
        help="Número de resultados por página en la búsqueda.",
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=20,
        help="Número máximo de páginas por consulta.",
    )
    parser.add_argument(
        "--output",
        default="lut_courses.json",
        help="Ruta de salida para el JSON resultante.",
    )
    parser.add_argument(
        "--include-raw-detail",
        action="store_true",
        help="Incluir rawDetail con el JSON completo sin procesar de cada curso (aumenta tamaño del archivo).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    session = requests.Session()

    course_ids = collect_course_ids(
        session=session,
        queries=args.queries,
        university_org_id=args.university_org_id,
        page_limit=args.page_limit,
        max_pages=args.max_pages,
        cookie=args.cookie,
    )

    print(f"Encontrados {len(course_ids)} cursos únicos.")

    courses = []
    for index, course_id in enumerate(course_ids, start=1):
        try:
            detail = fetch_course_detail(session, course_id, args.cookie)
            courses.append(detail_to_record(detail, include_raw=args.include_raw_detail))
            print(f"[{index}/{len(course_ids)}] {course_id}: {courses[-1].get('name')}")
        except Exception as exc:
            print(f"Advertencia: no se pudo descargar {course_id}: {exc}")

    with open(args.output, "w", encoding="utf-8") as output_file:
        json.dump(courses, output_file, ensure_ascii=False, indent=2)

    print(f"Guardado {len(courses)} cursos en {args.output}")


if __name__ == "__main__":
    main()
