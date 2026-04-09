import re
import pytest
from playwright.sync_api import expect
from pages.login_page import LoginPage

def test_valid_login(page, base_url):
    login = LoginPage(page)
    login.navigate(base_url)
    login.login("admin", "Admin123")
    expect(page).to_have_url(re.compile(r".*(home|location).*"))

def test_full_login_with_location(page, base_url):
    login = LoginPage(page)
    login.full_login(base_url)
    expect(page).to_have_url(re.compile(r".*home.*"))

def test_invalid_login(page, base_url):
    login = LoginPage(page)
    login.navigate(base_url)
    login.login("wronguser", "wrongpass")
    expect(page.locator(".cds--inline-notification__subtitle")).to_be_visible()

def test_empty_username(page, base_url):
    login = LoginPage(page)
    login.navigate(base_url)
    login.username_input.wait_for(state="visible", timeout=20000)
    login.username_input.fill("")
    login.login_button.click()
    expect(page).to_have_url(re.compile(r".*login.*"))
