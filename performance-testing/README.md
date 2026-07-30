# JMeter Performance Testing — OpenMRS O3 Demo API

A self-directed performance testing project targeting the public OpenMRS O3
demo REST API (`dev3.openmrs.org`), the same system covered by the
[`openmrs-qa`](https://github.com/aabbasahd92/openmrs-qa) Playwright functional
test suite. Built to gain genuine, current, hands-on exposure to JMeter,
closing a recurring gap flagged across job description evaluations.

## Contents

- `test-plans/openmrs-load-test.jmx` — the JMeter test plan. Two thread groups:
  a 5-user baseline load test and a stress test ramping to 50 concurrent users.
- `docs/SETUP_AND_RUN_GUIDE.md` — step-by-step install and run instructions.
- `docs/RESULTS_TEMPLATE.md` — real results from two executed runs, plus
  explicit guidance on how to represent this honestly on a resume and in
  interviews.

## Summary of results (see docs/RESULTS_TEMPLATE.md for full detail)

Two full runs executed in CLI mode against the live public demo API, zero
errors across 20,750+ combined requests. Run 2 directly compares a lightweight
endpoint (`GET /session`) against a heavier one (`GET /concept`) under load
ramping to 50 concurrent users, finding the heavier endpoint consistently
~2.5x slower at every percentile, with response times climbing roughly 4x as
concurrency increased.

`GET /patient` and `GET /location` were tried first but excluded after
confirming (via direct API error response, reproduced across multiple runs)
that the shared public demo account lacks the read privileges those
endpoints require.

## Honest scope

This is one self-directed project against a public demo system, not
production performance-engineering experience. See "How to represent this
honestly" in `docs/RESULTS_TEMPLATE.md` before adding anything to a resume or
saying anything in an interview.
