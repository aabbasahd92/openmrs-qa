# OpenMRS QA Automation Framework

Healthcare SaaS QA automation for OpenMRS O3, built with Playwright + Python.

**Highlights:**
- 25 automated tests across 6 modules — UI, REST API, and hybrid UI+API coverage
- 4x parallel execution via pytest-xdist, full CI/CD with Allure reporting
- **AI-assisted test planning** — Claude reviews requirements against live DOM evidence and
  classifies proposed scenarios as VERIFIED / ASSUMPTION_REQUIRES_REVIEW / REJECTED_UNSUPPORTED
  before any test code is written. No auto-generated tests without human approval. See
  [`AI_PLANNER_README.md`](./AI_PLANNER_README.md) for a real documented guardrail case run
  against a live (and, at the time, inaccessible) demo environment.


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

## AI-Assisted Test Planning (Experimental Addition)

### What it does

`ai_planner/planner.py` reads a written requirement, captures a live DOM/accessibility
snapshot of the actual running application via Playwright, and asks Claude (Anthropic API)
to propose test scenarios — each classified `VERIFIED`, `ASSUMPTION_REQUIRES_REVIEW`, or
`REJECTED_UNSUPPORTED` based on whether the requirement and the live evidence actually
support it. No test code is generated automatically; a human reviews and approves the plan
first. Full detail in [`AI_PLANNER_README.md`](./AI_PLANNER_README.md).

### Why evidence-based planning matters here

Public OpenMRS demo servers (test3.openmrs.org, dev3.openmrs.org, demo.openmrs.org) are
shared community infrastructure and go down or change without notice — this framework has
already hit that with the Appointments module gap logged above. An AI planner that reasons
only from training data would hallucinate scenarios against features that were never
verified as present. Grounding every scenario in a live DOM snapshot means the planner
itself catches this class of mismatch and flags it, rather than a human discovering broken
assumptions after test code is already written.

### Status

- 4/4 mocked unit tests passing (classification logic, JSON schema validation, Markdown
  rendering) — see `ai_planner/test_planner.py`
- CI: `AI Planner Smoke Tests` workflow, scoped to `ai_planner/**` changes
- Run live once against test3.openmrs.org — result: 0 VERIFIED / 5 ASSUMPTION_REQUIRES_REVIEW /
  3 REJECTED_UNSUPPORTED, correctly reflecting that the server was unreachable (Cloudflare
  bot-challenge) at run time. Full trace in `AI_PLANNER_README.md`.
- **Logged:** 2026-07-11

## Author

**Ahmed Abbas** — Senior QA Automation Engineer
7+ years Healthcare QA | CVS Health | Aetna

[LinkedIn](https://www.linkedin.com/in/ahamed-abbas-49421856/) · [GitHub](https://github.com/aabbasahd92)
'''

with open('/Users/ahmedabbas/openmrs-qa/README.md', 'w') as f:
    f.write(readme)
print("README written successfully")
PYEOF

---
