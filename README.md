---

## Test Modules

### Module 1 — Login (4 tests)
Valid login, invalid credentials, empty username, full login with location selection.

### Module 2 — Patient Registration (3 tests)
Male and female patient registration, form element visibility.

### Module 3 — Patient Search (4 tests)
Search icon, overlay open, results returned, no-results message.

### Module 4 — Data-Driven Registration (3 tests)
JSON-parametrized registration across multiple patient profiles. Zero hardcoded test data.

### Module 5 — REST API Tests (6 tests)
Auth validation, patient search response shape, UUID fetch, empty results. Documents OpenMRS API deviation from REST 401 standard.

### Module 6 — Patient Chart (5 tests — Hybrid UI + API)
Dynamically fetches patient UUID via REST API, then validates chart UI — Vitals, Conditions, Medications, URL structure.

---

## Tech Stack

| Tool | Version | Purpose |
|---|---|---|
| Python | 3.9 | Core language |
| Playwright | 1.58 | Browser automation |
| pytest | 8.4.2 | Test runner |
| pytest-playwright | 0.7.1 | Playwright fixtures |
| pytest-xdist | 3.8.0 | Parallel execution |
| allure-pytest | 2.15.3 | HTML reporting |
| requests | 2.32 | REST API testing |
| GitHub Actions | — | CI/CD |

---

## Running Locally

```bash
git clone https://github.com/aabbasahd92/openmrs-qa.git
cd openmrs-qa
python3.9 -m venv venv
source venv/bin/activate
pip install playwright==1.58.0 pytest pytest-playwright pytest-xdist allure-pytest requests
playwright install chromium

# Run all tests
pytest --tb=short -q

# Run with Allure reporting
pytest --alluredir=allure-results -q
allure serve allure-results

# Run a single module
pytest tests/test_patient_chart.py -v
```

---

## Healthcare Domain Knowledge Demonstrated

- **Two-step SPA login** — OpenMRS O3 separates username/password steps; password field is `aria-hidden` until step 1 completes
- **Location selection workflow** — clinicians must select ward before accessing EMR; healthcare-specific flow not seen in general SaaS
- **Carbon Design System** — IBM Carbon radio buttons require clicking `label[for=...]` not the hidden input
- **API contract documentation** — OpenMRS returns `200 + authenticated:false` instead of `401` for invalid credentials; deviation documented and asserted correctly
- **SPA background polling** — OpenMRS O3 never reaches `networkidle`; tests anchor on visible DOM elements instead

---

## Known Environment Limitations

### Appointments Module (test3.openmrs.org)
- **UI:** `esm-appointments` microfrontend not installed on test3 — page loads blank
- **API:** `appointmentscheduling` REST module not deployed on this server
- **Decision:** Tests deferred pending environment with module installed
- **Logged:** 2026-04-15

---

## Author

**Ahmed Abbas** — Senior QA Automation Engineer
7+ years Healthcare QA | CVS Health | Aetna

[LinkedIn](https://www.linkedin.com/in/ahamed-abbas-49421856/) · [GitHub](https://github.com/aabbasahd92)
'''

with open('/Users/ahmedabbas/openmrs-qa/README.md', 'w') as f:
    f.write(readme)
print("README written successfully")
PYEOF
