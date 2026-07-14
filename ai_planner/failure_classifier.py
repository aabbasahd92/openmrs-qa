"""
Test Failure Classifier — "Self-Healing" Diagnostic Layer
=============================================================

Purpose
-------
When a pytest test fails, this module sends the failure (test name, full
traceback, and any captured Playwright evidence) to Claude and asks it to
classify the likely root cause, then propose the smallest safe correction —
for a human to review. It does not modify test code, retry tests, or open
pull requests. "Self-healing" here means "self-diagnosing with a suggested
fix," not "self-modifying."

This mirrors ai_planner/planner.py's design: real evidence in, structured
classification out, human approval gate before anything touches test code.

Root-cause categories
----------------------
- LOCATOR_DRIFT: the element's selector/structure likely changed in the app
  (e.g., a CSS class renamed, an id removed, a Carbon component restructured)
- TIMING_ISSUE: the test is racing the app (e.g., needs a wait_for/expect
  instead of a fixed sleep, or a genuine flake under load)
- ENVIRONMENT_ISSUE: the target environment itself is the problem (a demo
  server outage, a bot-challenge block, a network failure) — not a code
  or test defect at all. This framework has hit this class of failure
  directly; see AI_PLANNER_README.md's documented guardrail case.
- REAL_DEFECT: the test correctly caught a genuine behavior change or bug
  in the application under test — nothing to "fix" in the test itself.
- UNKNOWN: the evidence doesn't clearly support any of the above; a human
  needs to look at this one directly.

Usage
-----
    python -m ai_planner.failure_classifier --report path/to/pytest_report.json \
                                              --out specs/healing_reports/run_2026-07-11.md

Where pytest_report.json is produced by running:
    pytest --json-report --json-report-file=pytest_report.json

Requires:
    pip install anthropic pytest-json-report
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from anthropic import Anthropic

MODEL = "claude-sonnet-4-6"

VALID_CATEGORIES = {
    "LOCATOR_DRIFT",
    "TIMING_ISSUE",
    "ENVIRONMENT_ISSUE",
    "REAL_DEFECT",
    "UNKNOWN",
}

SYSTEM_PROMPT = """You are a senior SDET triaging failed Playwright/pytest tests for a \
healthcare EMR application (OpenMRS O3). For each failed test you are given the test name, \
the full traceback, and (when available) the test's source code.

Classify the ROOT CAUSE of each failure as exactly one of:
- LOCATOR_DRIFT: the traceback suggests a selector/locator no longer matches the page
  (e.g., TimeoutError waiting for an element, "strict mode violation", element not found).
  This is likely because the application's DOM/CSS structure changed, not a real defect.
- TIMING_ISSUE: the traceback suggests a race condition — the test acted before the app
  was ready (e.g., intermittent timeouts under parallel load, network-dependent timing).
- ENVIRONMENT_ISSUE: the traceback or evidence suggests the TARGET ENVIRONMENT itself is
  broken or unreachable (e.g., HTTP 403/500 from the whole app, connection refused, a
  bot-challenge/CAPTCHA page, DNS failure) — not a defect in the test or the feature at all.
- REAL_DEFECT: the traceback shows a clear application behavior mismatch (e.g., an assertion
  on business logic failed with a specific wrong value) that is NOT explained by locator
  drift, timing, or environment issues. This means the test is correctly catching a bug.
- UNKNOWN: the evidence is genuinely ambiguous and a human needs to investigate directly.

For each failure, propose the SMALLEST safe suggested fix — a specific, minimal change \
(e.g., "wait for locator X with expect() instead of a fixed sleep", "update selector from \
'#old-id' to the Carbon label pattern used elsewhere in this codebase"). If the category is \
REAL_DEFECT or UNKNOWN, do not propose a code fix — instead say what a human should verify.

Never propose fixes that would hide, skip, or weaken an assertion (e.g., do not suggest \
loosening an assertion, adding a bare try/except, or increasing a timeout as a first resort \
if a smaller root-cause fix is evident from the evidence).

Respond ONLY with valid JSON matching this schema, no preamble or markdown fences:
{
  "failures": [
    {
      "test_name": "string, exact nodeid from the report",
      "category": "LOCATOR_DRIFT | TIMING_ISSUE | ENVIRONMENT_ISSUE | REAL_DEFECT | UNKNOWN",
      "rationale": "string, 1-3 sentences citing the specific traceback evidence",
      "suggested_fix": "string — a concrete minimal fix, or 'None — human verification required' \
if category is REAL_DEFECT or UNKNOWN"
    }
  ]
}
"""


@dataclass
class ClassifiedFailure:
    test_name: str
    category: str
    rationale: str
    suggested_fix: str


@dataclass
class ClassificationResult:
    source_report: Path
    raw_model_output: str
    failures: list = field(default_factory=list)

    def by_category(self, category: str) -> list:
        return [f for f in self.failures if f.category == category]


def extract_failures_from_report(report_path: Path) -> list:
    """Parse a pytest-json-report output file and extract only the failed tests,
    with their nodeid and full traceback/longrepr text."""
    with open(report_path) as f:
        report = json.load(f)

    failures = []
    for test in report.get("tests", []):
        outcome = test.get("outcome")
        if outcome not in ("failed", "error"):
            continue
        nodeid = test.get("nodeid", "unknown")
        traceback_text = ""
        for phase in ("setup", "call", "teardown"):
            phase_data = test.get(phase, {})
            phase_outcome = phase_data.get("outcome")
            if phase_outcome in ("failed", "error"):
                longrepr = phase_data.get("longrepr", "")
                traceback_text += f"\n--- {phase} phase ({phase_outcome}) ---\n{longrepr}"
        failures.append({"test_name": nodeid, "traceback": traceback_text.strip()})

    return failures


def classify_failures(failures: list, api_key: str = None) -> ClassificationResult:
    if not failures:
        return ClassificationResult(
            source_report=Path("(none)"), raw_model_output="{}", failures=[]
        )

    client = Anthropic(api_key=api_key) if api_key else Anthropic()

    failures_text = "\n\n".join(
        f"### Test: {f['test_name']}\nTraceback:\n{f['traceback']}" for f in failures
    )

    user_message = f"""Here are the failed tests from this run, with their tracebacks:

{failures_text}
"""

    response = client.messages.create(
        model=MODEL,
        max_tokens=4000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )

    raw_text = "".join(block.text for block in response.content if block.type == "text")

    try:
        parsed = json.loads(raw_text)
    except json.JSONDecodeError as e:
        raise ValueError(f"Model did not return valid JSON. Raw output:\n{raw_text}") from e

    classified = []
    for item in parsed.get("failures", []):
        if item.get("category") not in VALID_CATEGORIES:
            raise ValueError(f"Invalid category returned by model: {item}")
        classified.append(
            ClassifiedFailure(
                test_name=item["test_name"],
                category=item["category"],
                rationale=item["rationale"],
                suggested_fix=item["suggested_fix"],
            )
        )

    return ClassificationResult(
        source_report=Path("(from pytest-json-report)"),
        raw_model_output=raw_text,
        failures=classified,
    )


def render_report_markdown(result: ClassificationResult) -> str:
    lines = [
        f"# Test Failure Classification Report",
        "",
        f"- **Generated:** {datetime.now(timezone.utc).isoformat()}",
        f"- **Model:** {MODEL}",
        f"- **Total failures classified:** {len(result.failures)}",
        "",
        "> ⚠️ This report contains SUGGESTED fixes only. No test code has been modified.",
        "> A human must review each suggestion before applying it.",
        "",
    ]

    if not result.failures:
        lines.append("No failures to classify — clean run.")
        return "\n".join(lines)

    counts = {}
    for f in result.failures:
        counts[f.category] = counts.get(f.category, 0) + 1

    lines.append("## Summary")
    lines.append("")
    lines.append("| Category | Count |")
    lines.append("|---|---|")
    for cat in sorted(VALID_CATEGORIES):
        lines.append(f"| {cat} | {counts.get(cat, 0)} |")
    lines.append("")

    category_labels = {
        "ENVIRONMENT_ISSUE": "🌐 ENVIRONMENT_ISSUE — target environment problem, not a code defect",
        "LOCATOR_DRIFT": "🔧 LOCATOR_DRIFT — selector likely needs updating",
        "TIMING_ISSUE": "⏱️ TIMING_ISSUE — likely a race condition",
        "REAL_DEFECT": "🐛 REAL_DEFECT — test is correctly catching a real bug",
        "UNKNOWN": "❓ UNKNOWN — needs direct human investigation",
    }

    for category in ["ENVIRONMENT_ISSUE", "LOCATOR_DRIFT", "TIMING_ISSUE", "REAL_DEFECT", "UNKNOWN"]:
        bucket = result.by_category(category)
        if not bucket:
            continue
        lines.append(f"## {category_labels[category]}")
        lines.append("")
        for f in bucket:
            lines.append(f"### `{f.test_name}`")
            lines.append(f"**Rationale:** {f.rationale}")
            lines.append("")
            lines.append(f"**Suggested fix:** {f.suggested_fix}")
            lines.append("")

    lines.append("## Human Review Decision")
    lines.append("")
    lines.append("- [ ] Reviewed each suggested fix above")
    lines.append("- [ ] Applied fixes manually where appropriate (no auto-apply)")
    lines.append("- [ ] Confirmed REAL_DEFECT items are tracked as actual bugs, not test issues")
    lines.append("- Reviewer: ______________________")
    lines.append("- Date: ______________________")
    lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Classify pytest failures via Claude and suggest fixes (human review required)"
    )
    parser.add_argument(
        "--report", required=True, type=Path, help="Path to pytest-json-report JSON output"
    )
    parser.add_argument("--out", required=True, type=Path, help="Output path for the classification report")
    args = parser.parse_args()

    if not args.report.exists():
        print(f"Report file not found: {args.report}", file=sys.stderr)
        sys.exit(1)

    failures = extract_failures_from_report(args.report)

    if not failures:
        print("No failed tests found in report — nothing to classify.")
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(render_report_markdown(
            ClassificationResult(source_report=args.report, raw_model_output="{}", failures=[])
        ))
        return

    result = classify_failures(failures)
    result.source_report = args.report

    report_md = render_report_markdown(result)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(report_md)

    print(f"Classification report written to {args.out}")
    for category in sorted(VALID_CATEGORIES):
        count = len(result.by_category(category))
        if count:
            print(f"  {category}: {count}")
    print("\nNo test code modified. Review suggested fixes before applying.")


if __name__ == "__main__":
    main()
