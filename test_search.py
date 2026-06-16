import pytest
import requests

from scraper import search_courses


@pytest.fixture
def session():
    return requests.Session()


def test_search_courses_returns_json_structure(session):
    data = search_courses(
        session=session,
        query='physics',
        university_org_id='lut-university-root-id',
        start=0,
        limit=1,
        cookie=None,
    )

    assert isinstance(data, dict)
    assert 'searchResults' in data
    assert 'total' in data
    assert data['searchResults'] is not None
