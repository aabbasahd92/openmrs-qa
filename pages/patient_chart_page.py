class PatientChartPage:
    def __init__(self, page):
        self.page = page
        self.vitals_heading = page.locator("h4:has-text('Vitals')")
        self.biometrics_heading = page.locator("h4:has-text('Biometrics')")
        self.conditions_heading = page.locator("h4:has-text('Conditions')")
        self.active_medications_heading = page.locator("h4:has-text('Active Medications')")

    def navigate(self, base_url, patient_uuid):
        self.page.goto(f"{base_url}/patient/{patient_uuid}/chart")
        self.page.wait_for_load_state("domcontentloaded", timeout=20000)
        self.page.locator("h4").first.wait_for(state="visible", timeout=30000)

    def get_current_url(self):
        return self.page.url
