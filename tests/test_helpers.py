import pytest

from scraper import clean_html, choose_localized_text, parse_credits, parse_year, parse_language, parse_study_level


def test_clean_html_removes_tags_and_entities():
    html = '<p>Hello&nbsp;<strong>World</strong><br>Line</p>'
    assert clean_html(html) == 'Hello World Line'


def test_choose_localized_text_prefers_english():
    field = {'fi': 'Suomi', 'en': 'English', 'sv': 'Svenska'}
    assert choose_localized_text(field) == 'English'


def test_choose_localized_text_handles_list_and_string():
    assert choose_localized_text(['one', 'two']) == 'one two'
    assert choose_localized_text('plain text') == 'plain text'


def test_parse_credits_formats_range_and_single_value():
    assert parse_credits({'min': 3, 'max': 3}) == '3'
    assert parse_credits({'min': 3, 'max': 5}) == '3+5'
    assert parse_credits({'min': None, 'max': None}) is None


def test_parse_year_extracts_period_and_year():
    assert parse_year(['lut-curriculum-period-2025-2026']) == '2025-2026'
    assert parse_year(['some-other-2024']) == '2024'


def test_parse_language_extracts_urn_codes():
    assert parse_language(['urn:code:language:en']) == 'en'
    assert parse_language('urn:code:language:fi') == 'fi'
    assert parse_language(['fi', 'en']) == 'fi, en'


def test_parse_study_level_normalizes_urns():
    assert parse_study_level('urn:code:study-level:bachelor') == 'Bachelor'
    assert parse_study_level({'en': 'Other'}) == 'Other'
