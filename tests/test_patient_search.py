import re
import pytest
from playwright.sync_api import expect
from pages.login_page import LoginPage
from pages.patient_search_page import PatientSearchPage

@pytest.fixture
def logged_in(page, base_url):
    login = LoginPage(page)
    login.full_login(base_url)
    return page

def test_search_icon_visible(logged_in, base_url):
    """Search patient button is visible in the nav bar"""
    expect(logged_in.locator("button[aria-label='Search patient']")).to_be_visible()

def test_search_overlay_opens(logged_in, base_url):
    """Clicking search icon opens the search input overlay"""
    search = PatientSearchPage(logged_in)
    search.open_search()
    expect(logged_in.locator("input[placeholder='Search for a patient by name or identifier number']")).to_be_visible()

def test_search_returns_results(logged_in, base_url):
    """Searching by name returns at least 1 result"""
    search = PatientSearchPage(logged_in)
    search.search_patient("John")
    results_text = search.get_results_text()
    assert "search result" in results_text.lower(), f"Expected results, got: {results_text}"

def test_search_no_results(logged_in, base_url):
    """Searching for a nonsense name shows no results message"""
    search = PatientSearchPage(logged_in)
    search.search_patient("ZZZZNOTAPATIENT99999")
    logged_in.wait_for_timeout(2000)
    # Actual OpenMRS O3 message when no patient found
    expect(logged_in.locator("text=Sorry, no patient charts were found")).to_be_visible(timeout=5000)
