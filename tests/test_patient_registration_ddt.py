import re
import json
import pytest
from pathlib import Path
from playwright.sync_api import expect
from pages.login_page import LoginPage
from pages.patient_registration_page import PatientRegistrationPage

# Load patient data from JSON
DATA_FILE = Path(__file__).parent / "data" / "patients.json"
patients = json.loads(DATA_FILE.read_text())

@pytest.fixture
def logged_in(page, base_url):
    login = LoginPage(page)
    login.full_login(base_url)
    return page

@pytest.mark.parametrize("patient", patients, ids=[p["given"] for p in patients])
def test_register_patient_from_json(logged_in, base_url, patient):
    """Register each patient from JSON data file"""
    reg = PatientRegistrationPage(logged_in)
    reg.register_patient(
        base_url,
        given=patient["given"],
        middle=patient["middle"],
        family=patient["family"],
        gender=patient["gender"],
        dob=patient["dob"],
        address1=patient["address1"],
        city=patient["city"],
        state=patient["state"],
        country=patient["country"],
        postal=patient["postal"],
        phone=patient["phone"]
    )
    expect(logged_in).to_have_url(re.compile(r".*/patient/.*/chart.*"), timeout=15000)
