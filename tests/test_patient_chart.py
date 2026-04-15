import re
import requests
import pytest
from playwright.sync_api import expect
from pages.login_page import LoginPage
from pages.patient_chart_page import PatientChartPage

BASE_API = "https://test3.openmrs.org/openmrs/ws/rest/v1"
AUTH = ("admin", "Admin123")

def get_patient_uuid(query="John"):
    """Fetch a real patient UUID from the API"""
    response = requests.get(
        f"{BASE_API}/patient",
        params={"q": query, "limit": 1, "v": "default"},
        auth=AUTH
    )
    results = response.json().get("results", [])
    assert len(results) > 0, f"No patients found for query: {query}"
    return results[0]["uuid"]

@pytest.fixture
def logged_in(page, base_url):
    login = LoginPage(page)
    login.full_login(base_url)
    return page

def test_patient_chart_loads(logged_in, base_url):
    """Patient chart page loads successfully and redirects to Patient Summary"""
    uuid = get_patient_uuid("John")
    chart = PatientChartPage(logged_in)
    chart.navigate(base_url, uuid)
    assert "chart" in chart.get_current_url()
    assert uuid in chart.get_current_url()

def test_patient_chart_shows_vitals(logged_in, base_url):
    """Patient chart displays Vitals section"""
    uuid = get_patient_uuid("John")
    chart = PatientChartPage(logged_in)
    chart.navigate(base_url, uuid)
    expect(chart.vitals_heading.first).to_be_visible(timeout=15000)

def test_patient_chart_shows_conditions(logged_in, base_url):
    """Patient chart displays Conditions section"""
    uuid = get_patient_uuid("John")
    chart = PatientChartPage(logged_in)
    chart.navigate(base_url, uuid)
    expect(chart.conditions_heading).to_be_visible(timeout=15000)

def test_patient_chart_shows_medications(logged_in, base_url):
    """Patient chart displays Active Medications section"""
    uuid = get_patient_uuid("John")
    chart = PatientChartPage(logged_in)
    chart.navigate(base_url, uuid)
    expect(chart.active_medications_heading).to_be_visible(timeout=15000)

def test_patient_chart_url_structure(logged_in, base_url):
    """Chart URL follows OpenMRS O3 pattern: /patient/{uuid}/chart/Patient Summary"""
    uuid = get_patient_uuid("John")
    chart = PatientChartPage(logged_in)
    chart.navigate(base_url, uuid)
    expect(logged_in).to_have_url(re.compile(r".*/patient/.*/chart.*"), timeout=15000)
