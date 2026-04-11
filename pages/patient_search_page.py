class PatientSearchPage:
    def __init__(self, page):
        self.page = page
        self.search_icon_button = page.locator("button[aria-label='Search patient']")
        self.search_input = page.locator("input[placeholder='Search for a patient by name or identifier number']")
        self.results_text = page.locator("[class*='resultsText']")
        self.search_results = page.locator("[class*='patientSearchResults'] [class*='container'], [class*='patient-search'] li a")
        self.no_results = page.locator("[class*='emptyResultsContainer'], [class*='empty']")

    def open_search(self):
        self.search_icon_button.wait_for(state="visible", timeout=10000)
        self.search_icon_button.click()
        self.search_input.wait_for(state="visible", timeout=10000)

    def search(self, query):
        self.search_input.fill(query)
        self.page.wait_for_timeout(2000)

    def get_results_text(self):
        self.results_text.wait_for(state="visible", timeout=10000)
        return self.results_text.text_content()

    def click_first_result(self):
        first_result = self.search_results.first
        first_result.wait_for(state="visible", timeout=10000)
        first_result.click()

    def search_patient(self, query):
        self.open_search()
        self.search(query)
