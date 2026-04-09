import re
import pytest
from playwright.sync_api import expect
from pages.login_page import LoginPage
from pages.patient_registration_page import PatientRegistrationPage

@pytest.fixture
def logged_in(page, base_url):
    login = LoginPage(page)
    login.full_login(base_url)
    return page

def test_register_new_patient(logged_in, base_url):
    reg = PatientRegistrationPage(logged_in)
    reg.register_patient(
        base_url,
        given="John",
        middle="Michael",
        family="TestPatient"
    )
    expect(logged_in).to_have_url(re.compile(r".*/patient/.*/chart.*"), timeout=15000)

def test_register_female_patient(logged_in, base_url):
    reg = PatientRegistrationPage(logged_in)
    reg.register_patient(
        base_url,
        given="Sarah",
        middle="Anne",
        family="TestPatient",
        gender="female",
        dob="1985-06-20"
    )
    expect(logged_in).to_have_url(re.compile(r".*/patient/.*/chart.*"), timeout=15000)

def test_registration_page_loads(logged_in, base_url):
    reg = PatientRegistrationPage(logged_in)
    reg.navigate(base_url)
    expect(logged_in.locator("#givenName")).to_be_visible()
    expect(logged_in.locator("#familyName")).to_be_visible()
    expect(logged_in.locator("#gender-option-male")).to_be_visible()
