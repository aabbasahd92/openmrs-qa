import re

class LoginPage:
    def __init__(self, page):
        self.page = page
        self.username_input = page.locator("#username")
        self.password_input = page.locator("#password")
        self.login_button = page.locator("button[type='submit']")
        self.error_message = page.locator(".cds--inline-notification__subtitle")
        self.location_search = page.locator("input[type='search']")
        self.confirm_button = page.locator("button[type='submit']")

    def navigate(self, base_url):
        self.page.goto(f"{base_url}/login")

    def login(self, username, password):
        self.username_input.wait_for(state="visible", timeout=20000)
        self.username_input.fill(username)
        self.login_button.click()
        if password:
            self.password_input.wait_for(state="visible", timeout=20000)
            self.password_input.fill(password)
            self.login_button.click()

    def select_location(self, location_name="Outpatient Clinic"):
        self.location_search.wait_for(state="visible", timeout=15000)
        self.location_search.fill(location_name)
        self.page.wait_for_timeout(1000)
        self.page.locator(f"label:has-text('{location_name}')").first.click()
        self.confirm_button.click()

    def full_login(self, base_url, username="admin", password="Admin123"):
        self.navigate(base_url)
        self.login(username, password)
        # Handle both: location step required OR session skips straight to home
        self.page.wait_for_url(re.compile(r".*(home|login/location).*"), timeout=15000)
        if "location" in self.page.url:
            self.select_location()
            self.page.wait_for_url("**/home", timeout=15000)
        self.page.wait_for_selector("nav, [class*='header'], svg", timeout=30000)

    def get_error_message(self):
        self.error_message.wait_for(state="visible", timeout=10000)
        return self.error_message.text_content()
