# JMeter Performance Test Results — OpenMRS O3 Demo API

## Endpoint scope: what we actually tested, and why

The test plan originally targeted `GET /patient?q=...` and `GET /location` in
addition to `GET /session`. During setup, both of those endpoints returned a
consistent `401 Unauthorized` with the body `"Privileges required: Get
Patients"` / `"Privileges required: Get Locations"` — the shared public
`admin` account on the demo server can authenticate but does not carry the
read privileges those resource collections require. This was verified by
inspecting the actual response body (not assumed), and reproduced identically
across multiple clean, from-scratch runs, ruling out a transient issue.

Rather than fight the demo server's locked-down privilege model, the test
plan was simplified to load-test `GET /session` only, an endpoint every
authenticated request already depends on, and one this account can reliably
call. This is a legitimate load-testing target in its own right and the pivot
itself is worth mentioning in an interview: it shows reading the actual error
response instead of assuming a broken test, and adapting the test scope to
what the environment actually supports.

## Run Log

| Run # | Thread Group(s) | Mode | Notes |
|-------|-----------------|------|-------|
| 1 | Baseline (5 users) + Stress (ramp to 50) | CLI (`-n`) | First clean run, both groups hitting `GET /session` only. 0 errors. |
| 2 | Baseline (5 users) + Stress (ramp to 50) | CLI (`-n`) | Endpoint set expanded to `GET /session` + `GET /concept` (confirmed accessible via direct curl check first). 20,704 total requests, 0 errors. |

## Run 1 Results — GET /session (combined baseline + stress, CLI mode)

| Metric | Value |
|---|---|
| Samples | 50 |
| Average response time (ms) | 78.62 |
| Median response time (ms) | 53.50 |
| 90th percentile (ms) | 108.80 |
| 95th percentile (ms) | 228.50 |
| 99th percentile (ms) | 502.00 |
| Min response time (ms) | 45 |
| Max response time (ms) | 502 |
| Error % | 0.00% |
| Throughput (transactions/sec) | 2.84 |
| Apdex score | 0.990 |

_Source: `results/html-report-01/index.html`, generated from `results/run-01.jtl`._

## Run 2 Results — GET /session vs. GET /concept (combined baseline + stress, CLI mode)

| Metric | Total | GET /session | GET /concept |
|---|---|---|---|
| Samples | 20,704 | 10,364 | 10,340 |
| Average response time (ms) | 293.20 | 166.89 | 419.81 |
| Median response time (ms) | 229.00 | 157.00 | 410.00 |
| 90th percentile (ms) | 618.00 | 267.50 | 699.00 |
| 95th percentile (ms) | 703.00 | 306.00 | 764.00 |
| 99th percentile (ms) | 849.00 | 385.00 | 913.00 |
| Min response time (ms) | 49 | 49 | 76 |
| Max response time (ms) | 1207 | 779 | 1207 |
| Error % | 0.00% | 0.00% | 0.00% |
| Throughput (transactions/sec) | 114.81 | 57.53 | 57.50 |
| Apdex score | 0.905 | 0.999 | 0.811 |

_Source: `results/html-report-02/index.html`, generated from `results/run-02.jtl`._

### Degradation over the course of the stress ramp (from CLI summary output)

| Elapsed time | Active threads | Avg response (ms), all requests | Max (ms) |
|---|---|---|---|
| 0:00-0:31 | 16 | 104 | 504 |
| 0:31-1:01 | 28 | 164 | 544 |
| 1:01-1:31 | 39 | 254 | 845 |
| 1:31-2:01 | 50 | 353 | 974 |
| 2:01-2:31 | 50 (sustained) | 381 | 1207 |
| 2:31-3:00 | winding down | 418 | 1147 |

Average response time climbed roughly 4x (104ms → 418ms) as concurrency rose from
16 to 50 active threads, with zero errors throughout. This is a genuine,
directly-observed degradation curve under load, not an estimate.

## Observations

- Zero errors across both runs (50 requests in Run 1, 20,704 in Run 2) — the
  server never returned a failure under load, it degraded in response time
  instead.
- Run 2's direct comparison shows `GET /concept` (a search over concept
  metadata) is consistently ~2.5x slower than `GET /session` at every
  percentile measured (e.g. 95th percentile: 306ms for session vs. 764ms for
  concept). This is a genuine, quantified difference in relative endpoint
  cost under identical load conditions, not an assumption.
- Response time degraded steadily and predictably as concurrency rose during
  the stress ramp (see the elapsed-time table above): roughly 4x slower
  (104ms → 418ms average) between 16 and 50 concurrent threads. No sudden
  cliff or error spike was observed, just a smooth, monotonic slowdown.
- This is expected behavior for a shared, public, multi-tenant demo server
  rather than a dedicated performance-test environment: other users' traffic
  and general internet variance are plausible contributors, alongside
  genuine server-side load from this test.
- `GET /patient` and `GET /location` were excluded because the shared demo
  account lacks the `Get Patients` / `Get Locations` privileges required by
  those endpoints (confirmed via direct `curl` and reproduced identically
  across multiple runs) — this was a real environment constraint discovered
  and worked around, not a test-plan oversight.

## Screenshots to keep

- [ ] Aggregate Report table (baseline run)
- [ ] Aggregate Report table (stress run)
- [ ] HTML dashboard summary page
- [ ] Response-time-over-time graph, if degradation was visible

---

## How to represent this honestly

### On your resume (only after you have real numbers — do not add this section pre-emptively)

A defensible, bounded bullet, using the real Run 2 numbers, looks like this shape:

> *Built and executed a JMeter performance test suite (20,000+ requests) against
> a healthcare REST API (OpenMRS), comparing response-time degradation across
> two endpoint types under concurrent load ramping to 50 users; measured a
> ~2.5x relative slowdown on heavier metadata queries versus lightweight
> session checks, with zero errors observed.*

This is stronger than a generic "did some load testing" bullet because it
names a real, specific, quantified finding, not just an activity. Still,
do **not** write "load testing" or "performance engineering" as a core
skill/proficiency line, and do not claim a specific years-of-experience level
with JMeter. One well-executed self-directed project is real, current,
hands-on exposure. It is not a specialization.

### In an interview

If asked "have you done performance testing," the honest, strong answer is:

> "My production QA experience has been functional and API testing, not
> dedicated performance engineering. To close that gap, I built and ran a
> JMeter suite against OpenMRS's REST API myself: a baseline load test and a
> stress test ramping to 50 concurrent users, over 20,000 requests total with
> zero errors. The interesting finding was that a metadata search endpoint was
> consistently about two and a half times slower than a simple session check
> at every percentile, and response times climbed roughly 4x as concurrency
> rose. I can walk you through the setup, the dashboard, and what I'd want to
> learn next to go deeper, like distributed load generation or wiring this
> into CI."

This works because it's true, specific, shows a real comparative finding
(not just "I ran a tool"), and survives a technical follow-up question,
because there's nothing to catch you on. If asked why patient/location data
wasn't included, the honest answer is straightforward: the shared public
demo account didn't carry those read privileges, confirmed directly from the
API's own error response, and metadata endpoints were substituted instead.
That's a good answer, not a weak one: it shows you diagnosed the actual
constraint instead of assuming the test was broken.

### What NOT to say

- Do not imply this was production-scale or business-critical.
- Do not imply years of experience or a JMeter certification.
- Do not omit that it targeted a public demo server, if asked directly.
- Do not claim you tuned or fixed a real performance problem; you observed
  and measured a degradation pattern, you did not diagnose or resolve its
  root cause on the server side.
- Do not claim patient or clinical-record load testing; the actual scenario
  tested was authentication and metadata search, not clinical data
  operations.

## What would extend this project further (not yet done)

- Re-run 2-3 more times on different days to check for consistency, per the
  setup guide's recommendation.
- Consider a longer or higher-concurrency stress test to find an actual
  error threshold or breaking point, since both runs completed with zero
  errors even at 50 concurrent users.
- If broader endpoint access becomes available (e.g. a self-hosted OpenMRS
  instance via Docker, where an admin account has full privileges), add
  clinical-data endpoints back in for a more complete comparison.

