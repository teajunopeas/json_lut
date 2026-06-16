"""Pruebas de mapeo del detalle de curso en scraper.py."""

import pytest

from scraper import detail_to_record


def test_detail_to_record_extracts_expected_fields():
    """Prueba mapeo limpio de campos sin rawDetail por defecto."""
    detail = {
        'id': 'otm-1234',
        'code': 'TEST100',
        'name': {'en': 'Test Course', 'fi': 'Testi'},
        'credits': {'min': 5, 'max': 5},
        'outcomes': {'en': '<p>Learn stuff</p>'},
        'content': {'en': '<p>Course content</p>'},
        'studyLevel': 'urn:code:study-level:bachelor',
        'possibleAttainmentLanguages': ['urn:code:language:en'],
        'curriculumPeriodIds': ['lut-curriculum-period-2025-2026'],
        'prerequisites': {'en': '<p>Prior knowledge</p>'},
        'equivalentCoursesInfo': {'en': '<p>Equivalent</p>'},
        'activityPeriods': [{'startDate': '2025-01-15', 'endDate': '2025-05-30'}],
    }

    record = detail_to_record(detail, include_raw=False)

    assert record['id'] == 'otm-1234'
    assert record['code'] == 'TEST100'
    assert record['name'] == 'Test Course'
    assert record['credits'] == '5'
    assert record['learningOutcomes'] == 'Learn stuff'
    assert record['content'] == 'Course content'
    assert record['courseLevel'] == 'Bachelor'
    assert record['languageOfLearning'] == 'en'
    assert record['year'] == '2025-2026'
    assert record['prerequisites'] == 'Prior knowledge'
    assert record['equivalentCoursesInfo'] == 'Equivalent'
    assert 'rawDetail' not in record  # Por defecto no debe incluirse


def test_detail_to_record_includes_raw_detail_when_requested():
    """Prueba que rawDetail se incluye cuando include_raw=True."""
    detail = {
        'id': 'otm-5678',
        'code': 'TEST200',
        'name': {'en': 'Advanced Course'},
        'credits': {'min': 6, 'max': 6},
        'outcomes': None,
        'content': None,
    }

    record = detail_to_record(detail, include_raw=True)

    assert 'rawDetail' in record
    assert record['rawDetail'] == detail
