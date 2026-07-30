# JMeter Performance Testing Project — Setup & Run Guide

## Purpose

This is a self-directed learning project to close a real, recurring gap: performance/load
testing experience. It pairs with your existing OpenMRS Playwright QA suite
(github.com/aabbasahd92/openmrs-qa) so the final artifact is defensible and specific,
not a generic tutorial exercise.

**What this gets you, honestly:** genuine hands-on JMeter experience — building thread
groups, samplers, assertions, and timers, running baseline and stress tests, and reading
aggregate/summary reports. This is NOT "3+ years of production JMeter depth." Be precise
about that distinction in interviews: this is real, current, self-directed exposure, not
years of enterprise production experience. That distinction matters and should never be
blurred on a resume or in conversation.

---

## Step 1: Install JMeter (15–20 minutes)

You'll need this on your own machine (not this sandboxed environment, which can't reach
Apache's download servers).

**Prerequisite:** Java 8+ (you already have Java, confirm with `java -version`)

1. Download Apache JMeter from the official site: https://jmeter.apache.org/download_jmeter.cgi
   - Get the binary `.zip` (Windows) or `.tgz` (Mac/Linux), NOT the source package
2. Extract it anywhere, e.g. `~/apache-jmeter-5.6.3`
3. Add the `bin` folder to your PATH, or just `cd` into it each time
4. Verify install:
   ```
   cd apache-jmeter-5.6.3/bin
   ./jmeter -v
   ```
   You should see the JMeter version banner.

---

## Step 2: Open the provided test plan

1. Copy this entire `jmeter_project` folder to your machine
2. Launch JMeter GUI:
   ```
   cd apache-jmeter-5.6.3/bin
   ./jmeter
   ```
3. In the JMeter GUI: **File → Open** → select `test-plans/openmrs-load-test.jmx`

You'll see two Thread Groups:
- **01 - Baseline Load (5 users)** — enabled by default. Low concurrency, establishes a
  normal-load baseline against the OpenMRS public demo API.
- **02 - Stress Test (ramp to 50 users)** — disabled by default (right-click → Enable
  when you're ready to run it). Ramps concurrency up to see how response times degrade
  under load.

**Important — be a good citizen of the public demo server:** `dev3.openmrs.org` is a
shared public demo instance other people use to learn OpenMRS. Don't run the stress test
repeatedly or leave it running unattended. Run it once or twice to get real data, capture
your results, then stop. If you want to run heavier or repeated load tests, spin up your
own local OpenMRS instance via Docker (OpenMRS publishes reference Docker images) and
point `BASE_URL` at `localhost` instead — this is also a more realistic reflection of
how performance testing works in a real job, since you'd almost always test against a
staging environment, not a shared public one.

---

## Step 3: Run the baseline test

1. Make sure only Thread Group 01 is enabled (right-click Thread Group 02 → Disable, if not already)
2. Click the green ▶ Run button (or Ctrl+R)
3. Watch results populate in:
   - **View Results Tree** — request/response detail, good for debugging failures
   - **Summary Report** — running averages
   - **Aggregate Report** — the report you'll actually want to screenshot/document: min,
     max, average, median, 90th/95th/99th percentile response times, throughput, error %

4. Let it run to completion (10 loops × 5 users = 50 total requests, should take under a
   minute)
5. **Save your results:** File → Save Test Plan will preserve the .jmx; the `.jtl` result
   files will already be written to the `results/` folder. Also take a screenshot of the
   Aggregate Report table — this is your primary evidence artifact.

---

## Step 4: Run the stress test

1. Right-click Thread Group 01 → Disable
2. Right-click Thread Group 02 → Enable
3. Run again (this ramps from 0 to 50 concurrent users over 60 seconds, 20 loops each)
4. Watch the Aggregate Report — you're specifically looking for:
   - At what concurrency does average/95th-percentile response time start climbing sharply?
   - Does the error rate stay at 0%, or do requests start failing/timing out under load?
   - Is there a clear "knee" in the performance curve?

5. Save these results separately (rename the `.jtl` files or copy them to a
   `results/stress-test/` subfolder before re-running, since JMeter overwrites by default)

---

## Step 5: Document your findings

Use `docs/RESULTS_TEMPLATE.md` in this project to write up what you found. This is the
actual artifact you'll reference in interviews and can optionally add to your GitHub
alongside the Playwright suite. Fill in real numbers from your own run — don't estimate
or reuse the placeholder text.

---

## What to say about this in an interview (be precise)

**Accurate framing:**
> "I identified performance testing as a gap in my background, so I built a self-directed
> JMeter project against my own OpenMRS test environment — designed baseline and stress
> test plans, ran them, and analyzed response-time degradation under load. I'm comfortable
> with the fundamentals: thread groups, samplers, assertions, and reading aggregate
> reports. I haven't yet had years of production performance-testing responsibility, but
> I understand the discipline and can ramp quickly given my existing automation
> background."

**Do NOT say or imply:**
> "I have 3+ years of JMeter experience." (You don't, and this is exactly the kind of
> claim that gets tested directly in a technical screen.)

This distinction is important enough that it's worth rehearsing out loud once before an
interview where performance testing might come up.
