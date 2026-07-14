"""
AI Test Planner — openmrs-qa Framework Extension
==================================================

Purpose
-------
Takes a written requirement (Markdown file) plus a snapshot of the actual
application state (DOM text pulled live via Playwright) and asks Claude to
draft a structured, evidence-based test plan. Every proposed scenario is
classified as VERIFIED, ASSUMPTION_REQUIRES_REVIEW, or REJECTED_UNSUPPORTED.

Nothing here is auto-approved. The plan is written to disk as a Markdown
file under specs/pending/ and a human (you) reviews it before any test code
is generated. Approval is a manual step: move the file to specs/approved/
and only then does a separate generator step touch it.

This is a thin orchestration layer around two things this framework already
has: the existing Playwright/Python page objects (for live DOM evidence),
and the Anthropic API (for structured reasoning over that evidence). It does
not generate or modify test code itself — that separation is the whole
point of the human approval gate.

Usage
-----
    python -m ai_planner.planner --requirement requirements/GH-001-appointment-scheduling.md \
                                   --url https://test3.openmrs.org/openmrs/spa/home \
                                   --out specs/pending/GH-001-plan.md

Requires:
    pip install anthropic playwright
    export ANTHROPIC_API_KEY=...
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from anthropic import Anthropic
from playwright.sync_api import sync_playwright

MODEL = "claude-sonnet-4-6"

VALID_CLASSIFICATIONS = {"VERIFIED", "ASSUMPTION_REQUIRES_REVIEW", "REJECTED_UNSUPPORTED"}

SYSTEM_PROMPT = """You are a senior SDET assisting with test planning for a healthcare EMR \
application (OpenMRS O3). You will be given:
1. A written requirement with acceptance criteria and explicit out-of-scope items.
2. Live DOM/accessibility-tree evidence captured from the actual running application.

Your job is to propose test scenarios that are grounded ONLY in what the requirement states \
and what the DOM evidence shows is actually present in the application. You must not invent \
functionality that isn't supported by the evidence.

For every scenario you propose, classify it as exactly one of:
- VERIFIED: directly supported by both the requirement text and the DOM evidence.
- ASSUMPTION_REQUIRES_REVIEW: plausible given the requirement, but the DOM evidence is \
incomplete or ambiguous — a human must confirm before this is automated.
- REJECTED_UNSUPPORTED: not supported by the requirement (e.g., explicitly listed as \
out-of-scope) or contradicted by the DOM evidence (e.g., the element/flow does not exist).

Respond ONLY with valid JSON matching this schema, no preamble or markdown fences:
{
  "scenarios": [
    {
      "id": "string, e.g. GH-001-SC01",
      "title": "string",
      "classification": "VERIFIED | ASSUMPTION_REQUIRES_REVIEW | REJECTED_UNSUPPORTED",
      "rationale": "string, 1-3 sentences citing the requirement line AND the DOM evidence \
that led to this classification",
      "steps": ["string", "..."]
    }
  ],
  "unsupported_inputs_flagged": ["string — any part of the requirement or DOM evidence that \
seemed like a hint at a feature but could not be verified"]
}
"""


@dataclass
class PlannerResult:
    requirement_path: Path
    target_url: str
    dom_evidence: str
    raw_model_output: str
    scenarios: list[dict] = field(default_factory=list)
    unsupported_inputs_flagged: list[str] = field(default_factory=list)

    @property
    def verified(self) -> list[dict]:
        return [s for s in self.scenarios if s["classification"] == "VERIFIED"]

    @property
    def needs_review(self) -> list[dict]:
        return [s for s in self.scenarios if s["classification"] == "ASSUMPTION_REQUIRES_REVIEW"]

    @property
    def rejected(self) -> list[dict]:
        return [s for s in self.scenarios if s["classification"] == "REJECTED_UNSUPPORTED"]


def capture_dom_evidence(url: str, timeout_ms: int = 15000) -> str:
    """Pull a lightweight, text-only accessibility snapshot of the live page.

    Uses Locator.aria_snapshot(), the current supported Playwright API for
    accessibility-tree capture. The older Page.accessibility.snapshot() API
    this originally used was removed in recent Playwright releases (this
    framework hit that removal directly — see AI_PLANNER_README.md for the
    live trace where a real navigation failure surfaced this).

    If the page fails to load at all (timeout, DNS failure, server error),
    that failure is captured as evidence too, rather than raised — an
    unreachable page is itself a valid, important signal for the planner:
    it means no scenario can be VERIFIED against this environment right now.
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        nav_error = None
        try:
            page.goto(url, timeout=timeout_ms)
            page.wait_for_timeout(2000)
        except Exception as e:
            nav_error = str(e)

        try:
            aria_tree = page.locator("body").aria_snapshot()
        except Exception as e:
            aria_tree = f"(aria_snapshot failed: {e})"

        try:
            visible_text = page.inner_text("body")[:4000]
        except Exception as e:
            visible_text = f"(inner_text failed: {e})"

        browser.close()

    return json.dumps(
        {
            "navigation_error": nav_error,
            "aria_snapshot_excerpt": aria_tree[:6000],
            "visible_text_excerpt": visible_text,
        },
        indent=2,
    )


def run_planner(requirement_path: Path, target_url: str, api_key: str = None) -> PlannerResult:
    requirement_text = requirement_path.read_text()
    dom_evidence = capture_dom_evidence(target_url)

    client = Anthropic(api_key=api_key) if api_key else Anthropic()

    user_message = f"""## Requirement
{requirement_text}

## Live DOM Evidence (captured {datetime.now(timezone.utc).isoformat()})
{dom_evidence}
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

    scenarios = parsed.get("scenarios", [])
    for s in scenarios:
        if s.get("classification") not in VALID_CLASSIFICATIONS:
            raise ValueError(f"Invalid classification returned by model: {s}")

    return PlannerResult(
        requirement_path=requirement_path,
        target_url=target_url,
        dom_evidence=dom_evidence,
        raw_model_output=raw_text,
        scenarios=scenarios,
        unsupported_inputs_flagged=parsed.get("unsupported_inputs_flagged", []),
    )


def render_plan_markdown(result: PlannerResult) -> str:
    lines = [
        f"# Test Plan (PENDING HUMAN APPROVAL) — {result.requirement_path.stem}",
        "",
        f"- **Source requirement:** `{result.requirement_path}`",
        f"- **Target URL exercised:** {result.target_url}",
        f"- **Generated:** {datetime.now(timezone.utc).isoformat()}",
        f"- **Model:** {MODEL}",
        "",
        "> ⚠️ No test code has been generated from this plan. A human must review every ",
        "> scenario below, move REJECTED/REVIEW items to a decision, and only then run the ",
        "> generator against the VERIFIED (and any manually-upgraded) scenarios.",
        "",
        "## Scenario Classification Summary",
        "",
        f"| Classification | Count |",
        f"|---|---|",
        f"| VERIFIED | {len(result.verified)} |",
        f"| ASSUMPTION_REQUIRES_REVIEW | {len(result.needs_review)} |",
        f"| REJECTED_UNSUPPORTED | {len(result.rejected)} |",
        "",
    ]

    for label, bucket in [
        ("✅ VERIFIED — eligible for automation", result.verified),
        ("⚠️ ASSUMPTION_REQUIRES_REVIEW — needs human decision", result.needs_review),
        ("❌ REJECTED_UNSUPPORTED — not automated", result.rejected),
    ]:
        lines.append(f"## {label}")
        lines.append("")
        if not bucket:
            lines.append("_None._")
            lines.append("")
            continue
        for s in bucket:
            lines.append(f"### {s['id']} — {s['title']}")
            lines.append(f"**Rationale:** {s['rationale']}")
            lines.append("")
            lines.append("**Steps:**")
            for step in s.get("steps", []):
                lines.append(f"- {step}")
            lines.append("")

    if result.unsupported_inputs_flagged:
        lines.append("## Flagged During Planning (not scenarios, just notes)")
        lines.append("")
        for note in result.unsupported_inputs_flagged:
            lines.append(f"- {note}")
        lines.append("")

    lines.append("## Human Approval Decision")
    lines.append("")
    lines.append("- [ ] Reviewed all VERIFIED scenarios — approved as-is")
    lines.append("- [ ] Reviewed all ASSUMPTION_REQUIRES_REVIEW scenarios — resolved (approved/rejected each)")
    lines.append("- [ ] Confirmed REJECTED_UNSUPPORTED scenarios are correctly out of scope")
    lines.append("- Reviewer: ______________________")
    lines.append("- Date: ______________________")
    lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="AI test planner with human approval gate")
    parser.add_argument("--requirement", required=True, type=Path)
    parser.add_argument("--url", required=True, help="Live URL to capture DOM evidence from")
    parser.add_argument("--out", required=True, type=Path, help="Output path for the plan markdown")
    args = parser.parse_args()

    if not args.requirement.exists():
        print(f"Requirement file not found: {args.requirement}", file=sys.stderr)
        sys.exit(1)

    result = run_planner(args.requirement, args.url)
    plan_md = render_plan_markdown(result)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(plan_md)

    print(f"Plan written to {args.out}")
    print(f"  VERIFIED: {len(result.verified)}")
    print(f"  ASSUMPTION_REQUIRES_REVIEW: {len(result.needs_review)}")
    print(f"  REJECTED_UNSUPPORTED: {len(result.rejected)}")
    print("\nNo test code generated. Review the plan and approve before automating.")


if __name__ == "__main__":
    main()

