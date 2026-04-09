class PatientRegistrationPage:
    def __init__(self, page):
        self.page = page
        self.given_name = page.locator("#givenName")
        self.middle_name = page.locator("#middleName")
        self.family_name = page.locator("#familyName")
        self.dob_input = page.locator("input[name='birthdate'][type='date']")
        self.address1 = page.locator("#address1")
        self.city = page.locator("#cityVillage")
        self.state = page.locator("#stateProvince")
        self.country = page.locator("#country")
        self.postal_code = page.locator("#postalCode")
        self.phone = page.locator("#phone")
        self.submit_button = page.locator("button[type='submit']")

    def navigate(self, base_url):
        self.page.goto(f"{base_url}/patient-registration")
        self.given_name.wait_for(state="visible", timeout=20000)

    def fill_name(self, given, middle, family):
        self.given_name.fill(given)
        self.middle_name.fill(middle)
        self.family_name.fill(family)

    def select_gender(self, gender="male"):
        # Click the label, not the hidden radio input (Carbon Design System)
        self.page.locator(f"label[for='gender-option-{gender}']").click()

    def fill_dob(self, date):
        self.dob_input.fill(date)

    def fill_address(self, address1, city, state, country, postal):
        self.address1.fill(address1)
        self.city.fill(city)
        self.state.fill(state)
        self.country.fill(country)
        self.postal_code.fill(postal)

    def fill_phone(self, phone):
        self.phone.fill(phone)

    def submit(self):
        self.submit_button.click()

    def register_patient(self, base_url, given, middle, family,
                         gender="male", dob="1990-01-15",
                         address1="123 Main St", city="Nairobi",
                         state="Nairobi", country="Kenya",
                         postal="00100", phone="0712345678"):
        self.navigate(base_url)
        self.fill_name(given, middle, family)
        self.select_gender(gender)
        self.fill_dob(dob)
        self.fill_address(address1, city, state, country, postal)
        self.fill_phone(phone)
        self.submit()
