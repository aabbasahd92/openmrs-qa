import pytest
import requests

BASE_URL = "https://test3.openmrs.org/openmrs/ws/rest/v1"
AUTH = ("admin", "Admin123")
HEADERS = {"Content-Type": "application/json"}


def test_api_auth_valid():
    """Valid credentials return 200"""
    response = requests.get(f"{BASE_URL}/session", auth=AUTH)
    assert response.status_code == 200
    data = response.json()
    assert data["authenticated"] is True


def test_api_auth_invalid():
    """Invalid credentials return unauthenticated session (OpenMRS returns 200 with authenticated=false)"""
    response = requests.get(f"{BASE_URL}/session", auth=("wrong", "wrong"))
    assert response.status_code == 200
    data = response.json()
    assert data["authenticated"] is False


def test_api_search_patient_returns_results():
    """Searching by name returns a results array with at least 1 patient"""
    response = requests.get(
        f"{BASE_URL}/patient",
        params={"q": "John", "limit": 5, "v": "default"},
        auth=AUTH
    )
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert len(data["results"]) > 0


def test_api_search_patient_response_shape():
    """Patient results contain expected fields"""
    response = requests.get(
        f"{BASE_URL}/patient",
        params={"q": "John", "limit": 1, "v": "default"},
        auth=AUTH
    )
    assert response.status_code == 200
    patient = response.json()["results"][0]
    assert "uuid" in patient
    assert "display" in patient
    assert "person" in patient
    assert "voided" in patient
    assert patient["voided"] is False


def test_api_get_patient_by_uuid():
    """Fetching a patient by UUID returns correct data"""
    # First get a UUID from search
    search = requests.get(
        f"{BASE_URL}/patient",
        params={"q": "John", "limit": 1, "v": "default"},
        auth=AUTH
    )
    uuid = search.json()["results"][0]["uuid"]

    # Now fetch by UUID
    response = requests.get(f"{BASE_URL}/patient/{uuid}", auth=AUTH)
    assert response.status_code == 200
    data = response.json()
    assert data["uuid"] == uuid


def test_api_search_no_results():
    """Searching a nonsense name returns empty results"""
    response = requests.get(
        f"{BASE_URL}/patient",
        params={"q": "ZZZZNOTAPATIENT99999", "limit": 5, "v": "default"},
        auth=AUTH
    )
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert len(data["results"]) == 0
