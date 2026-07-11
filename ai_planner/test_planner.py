"""
Smoke tests for the AI test planner.

These do NOT call the live Anthropic API or a live browser — they mock both
so the test suite runs fast and free in CI. The point is to prove the
classification-parsing and Markdown-rendering logic is correct.
"""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from ai_planner.planner import (
    PlannerResult,
    render_plan_markdown,
    run_planner,
)

FAKE_MODEL_JSON = {
    "scenarios": [
        {
            "id": "GH-001-SC01",
            "title": "Clinician creates appointment with valid service and time",
            "classification": "VERIFIED",
            "rationale": "Requirement AC3 states this explicitly; DOM evidence shows a "
            "'New Appointment' button and service/date/time form fields present.",
            "steps": [
                "Open patient chart",
                "Navigate to Appointments tab",
                "Click New Appointment",
                "Select service, date, time",
                "Save and verify confirmation",
            ],
        },
        {
            "id": "GH-001-SC02",
            "title": "Appointment payment collection at booking time",
            "classification": "REJECTED_UNSUPPORTED",
            "rationale": "Requirement explicitly lists payment collection as out of scope; "
            "no payment UI elements found in DOM evidence.",
            "steps": [],
        },
        {
            "id": "GH-001-SC03",
            "title": "Appointment reminder opt-in during booking",
            "classification": "ASSUMPTION_REQUIRES_REVIEW",
            "rationale": "DOM evidence shows a checkbox labeled 'Notify patient' but the "
            "requirement does not mention reminders — unclear if in scope.",
            "steps": ["Open new appointment form", "Locate notify checkbox"],
        },
    ],
    "unsupported_inputs_flagged": [
        "DOM evidence contained a 'Recurring appointment' toggle not mentioned anywhere "
        "in the requirement — flagging for product clarification, not automating."
    ],
}


@pytest.fixture
def requirement_file(tmp_path: Path) -> Path:
    req = tmp_path / "GH-001-appointment-scheduling.md"
    req.write_text(
        "## Acceptance Criteria\n"
        "3. The clinician can create a new appointment by selecting a service, date, and time.\n"
        "## Out of Scope\n- Payment collection for appointments\n"
    )
    return req


def _mock_anthropic_response():
    mock_block = MagicMock()
    mock_block.type = "text"
    mock_block.text = json.dumps(FAKE_MODEL_JSON)

    mock_response = MagicMock()
    mock_response.content = [mock_block]
    return mock_response


@patch("ai_planner.planner.capture_dom_evidence")
@patch("ai_planner.planner.Anthropic")
def test_run_planner_classifies_scenarios_correctly(mock_anthropic_cls, mock_capture_dom, requirement_file):
    mock_capture_dom.return_value = '{"visible_text_excerpt": "New Appointment button present"}'

    mock_client = MagicMock()
    mock_client.messages.create.return_value = _mock_anthropic_response()
    mock_anthropic_cls.return_value = mock_client

    result = run_planner(requirement_file, "https://fake.test/url", api_key="fake-key")

    assert len(result.verified) == 1
    assert result.verified[0]["id"] == "GH-001-SC01"

    assert len(result.rejected) == 1
    assert result.rejected[0]["id"] == "GH-001-SC02"

    assert len(result.needs_review) == 1
    assert result.needs_review[0]["id"] == "GH-001-SC03"

    assert len(result.unsupported_inputs_flagged) == 1


@patch("ai_planner.planner.capture_dom_evidence")
@patch("ai_planner.planner.Anthropic")
def test_run_planner_rejects_invalid_classification(mock_anthropic_cls, mock_capture_dom, requirement_file):
    bad_json = {
        "scenarios": [
            {
                "id": "GH-001-SC99",
                "title": "Bad scenario",
                "classification": "TOTALLY_MADE_UP_LABEL",
                "rationale": "n/a",
                "steps": [],
            }
        ],
        "unsupported_inputs_flagged": [],
    }
    mock_capture_dom.return_value = "{}"

    mock_block = MagicMock()
    mock_block.type = "text"
    mock_block.text = json.dumps(bad_json)
    mock_response = MagicMock()
    mock_response.content = [mock_block]

    mock_client = MagicMock()
    mock_client.messages.create.return_value = mock_response
    mock_anthropic_cls.return_value = mock_client

    with pytest.raises(ValueError, match="Invalid classification"):
        run_planner(requirement_file, "https://fake.test/url", api_key="fake-key")


def test_render_plan_markdown_separates_scenarios_by_bucket(requirement_file):
    result = PlannerResult(
        requirement_path=requirement_file,
        target_url="https://fake.test/url",
        dom_evidence="{}",
        raw_model_output=json.dumps(FAKE_MODEL_JSON),
        scenarios=FAKE_MODEL_JSON["scenarios"],
        unsupported_inputs_flagged=FAKE_MODEL_JSON["unsupported_inputs_flagged"],
    )

    md = render_plan_markdown(result)

    assert "PENDING HUMAN APPROVAL" in md
    assert "GH-001-SC01" in md
    assert "✅ VERIFIED" in md
    assert "❌ REJECTED_UNSUPPORTED" in md
    assert "⚠️ ASSUMPTION_REQUIRES_REVIEW" in md
    assert "Recurring appointment" in md
    assert "Reviewer: " in md


def test_render_plan_markdown_handles_empty_bucket(requirement_file):
    result = PlannerResult(
        requirement_path=requirement_file,
        target_url="https://fake.test/url",
        dom_evidence="{}",
        raw_model_output="{}",
        scenarios=[],
        unsupported_inputs_flagged=[],
    )
    md = render_plan_markdown(result)
    assert "_None._" in md
