"""
Smoke tests for the failure classifier.

Mocks the Anthropic client entirely - no live API calls in CI. Also builds
a synthetic pytest-json-report structure in memory rather than requiring a
real test run, so these tests are fast, free, and deterministic.
"""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from ai_planner.failure_classifier import (
    ClassificationResult,
    ClassifiedFailure,
    classify_failures,
    extract_failures_from_report,
    render_report_markdown,
)

FAKE_MODEL_JSON = {
    "failures": [
        {
            "test_name": "tests/test_login.py::test_valid_login[chromium]",
            "category": "ENVIRONMENT_ISSUE",
            "rationale": "Traceback shows TimeoutError waiting for username field to become visible after 20000ms - this matches a target-server outage pattern, not a locator problem, since the same failure occurs across every test in the file.",
            "suggested_fix": "None - human verification required. Confirm test3.openmrs.org is reachable before re-running.",
        },
        {
            "test_name": "tests/test_patient_search.py::test_search_icon_visible[chromium]",
            "category": "LOCATOR_DRIFT",
            "rationale": "Traceback shows strict mode violation, locator resolved to 2 elements - the Carbon search icon selector likely matches both the header and sidebar instances after a UI update.",
            "suggested_fix": "Scope the locator with a parent container instead of a bare role selector.",
        },
        {
            "test_name": "tests/test_api_patients.py::test_api_get_patient_by_uuid",
            "category": "REAL_DEFECT",
            "rationale": "The traceback shows the search response body was not valid JSON - this indicates the API itself returned an unexpected error page, which is an application-level issue rather than a test or locator problem.",
            "suggested_fix": "None - human verification required. File as a bug against the patient search API endpoint.",
        },
    ]
}


@pytest.fixture
def synthetic_report(tmp_path):
    login_longrepr = "playwright TimeoutError: Locator.wait_for: Timeout 20000ms exceeded waiting for username field to be visible"
    search_longrepr = "playwright Error: strict mode violation: locator resolved to 2 elements"

    report = {
        "tests": [
            {
                "nodeid": "tests/test_login.py::test_valid_login[chromium]",
                "outcome": "failed",
                "call": {"outcome": "failed", "longrepr": login_longrepr},
            },
            {
                "nodeid": "tests/test_patient_search.py::test_search_icon_visible[chromium]",
                "outcome": "failed",
                "call": {"outcome": "failed", "longrepr": search_longrepr},
            },
            {
                "nodeid": "tests/test_login.py::test_full_login_with_location[chromium]",
                "outcome": "passed",
            },
        ]
    }
    report_path = tmp_path / "pytest_report.json"
    report_path.write_text(json.dumps(report))
    return report_path


def _mock_anthropic_response(payload):
    mock_block = MagicMock()
    mock_block.type = "text"
    mock_block.text = json.dumps(payload)
    mock_response = MagicMock()
    mock_response.content = [mock_block]
    return mock_response


def test_extract_failures_only_returns_failed_tests(synthetic_report):
    failures = extract_failures_from_report(synthetic_report)
    assert len(failures) == 2
    test_names = [f["test_name"] for f in failures]
    assert "tests/test_login.py::test_valid_login[chromium]" in test_names
    assert "tests/test_patient_search.py::test_search_icon_visible[chromium]" in test_names
    assert "tests/test_login.py::test_full_login_with_location[chromium]" not in test_names


def test_extract_failures_includes_traceback_text(synthetic_report):
    failures = extract_failures_from_report(synthetic_report)
    login_failure = next(f for f in failures if "test_valid_login" in f["test_name"])
    assert "TimeoutError" in login_failure["traceback"]


@patch("ai_planner.failure_classifier.Anthropic")
def test_classify_failures_returns_expected_categories(mock_anthropic_cls, synthetic_report):
    failures = extract_failures_from_report(synthetic_report)

    mock_client = MagicMock()
    mock_client.messages.create.return_value = _mock_anthropic_response(FAKE_MODEL_JSON)
    mock_anthropic_cls.return_value = mock_client

    result = classify_failures(failures, api_key="fake-key")

    assert len(result.failures) == 3
    env_issues = result.by_category("ENVIRONMENT_ISSUE")
    assert len(env_issues) == 1
    assert "test_valid_login" in env_issues[0].test_name

    drift_issues = result.by_category("LOCATOR_DRIFT")
    assert len(drift_issues) == 1

    real_defects = result.by_category("REAL_DEFECT")
    assert len(real_defects) == 1


@patch("ai_planner.failure_classifier.Anthropic")
def test_classify_failures_rejects_invalid_category(mock_anthropic_cls, synthetic_report):
    failures = extract_failures_from_report(synthetic_report)

    bad_payload = {
        "failures": [
            {
                "test_name": "tests/test_x.py::test_y",
                "category": "TOTALLY_MADE_UP",
                "rationale": "n/a",
                "suggested_fix": "n/a",
            }
        ]
    }

    mock_client = MagicMock()
    mock_client.messages.create.return_value = _mock_anthropic_response(bad_payload)
    mock_anthropic_cls.return_value = mock_client

    with pytest.raises(ValueError, match="Invalid category"):
        classify_failures(failures, api_key="fake-key")


def test_classify_failures_with_no_failures_returns_empty_result():
    result = classify_failures([], api_key="fake-key")
    assert result.failures == []


def test_render_report_markdown_groups_by_category():
    result = ClassificationResult(
        source_report=Path("fake.json"),
        raw_model_output=json.dumps(FAKE_MODEL_JSON),
        failures=[
            ClassifiedFailure(
                test_name=item["test_name"],
                category=item["category"],
                rationale=item["rationale"],
                suggested_fix=item["suggested_fix"],
            )
            for item in FAKE_MODEL_JSON["failures"]
        ],
    )

    md = render_report_markdown(result)

    assert "Test Failure Classification Report" in md
    assert "ENVIRONMENT_ISSUE" in md
    assert "LOCATOR_DRIFT" in md
    assert "REAL_DEFECT" in md
    assert "test_valid_login" in md
    assert "Reviewer: " in md


def test_render_report_markdown_handles_clean_run():
    result = ClassificationResult(
        source_report=Path("fake.json"), raw_model_output="{}", failures=[]
    )
    md = render_report_markdown(result)
    assert "clean run" in md.lower()
