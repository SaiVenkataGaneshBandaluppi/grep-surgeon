from __future__ import annotations

import io
import json

from grep_surgeon.reporter import report_json, report_plain
from grep_surgeon.scanner import Violation

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _v(
    rule_id: str = "no-todo",
    severity: str = "error",
    file: str = "app/main.py",
    line: int = 10,
    matched_text: str = "# TODO: fix this",
) -> Violation:
    return Violation(
        rule_id=rule_id,
        severity=severity,
        file=file,
        line=line,
        matched_text=matched_text,
    )


def _capture_plain(violations: list[Violation]) -> str:
    buf = io.StringIO()
    report_plain(violations, out=buf)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# report_plain
# ---------------------------------------------------------------------------

def test_plain_output_contains_rule_id() -> None:
    output = _capture_plain([_v(rule_id="no-todo")])
    assert "no-todo" in output


def test_plain_output_contains_file_and_line() -> None:
    output = _capture_plain([_v(file="app/main.py", line=42)])
    assert "app/main.py:42" in output


def test_plain_output_contains_matched_text() -> None:
    output = _capture_plain([_v(matched_text="some bad text")])
    assert "some bad text" in output


def test_plain_output_error_label_uppercase() -> None:
    output = _capture_plain([_v(severity="error")])
    assert "ERROR" in output


def test_plain_output_warning_label_uppercase() -> None:
    output = _capture_plain([_v(severity="warning")])
    assert "WARNING" in output


def test_plain_output_summary_counts_plural() -> None:
    violations = [_v(severity="error"), _v(severity="error"), _v(severity="warning")]
    output = _capture_plain(violations)
    assert "2 errors" in output
    assert "1 warning" in output


def test_plain_output_summary_counts_singular() -> None:
    violations = [_v(severity="error")]
    output = _capture_plain(violations)
    assert "1 error," in output
    assert "0 warnings" in output


def test_plain_output_no_violations_shows_clean_message() -> None:
    output = _capture_plain([])
    assert "No violations found" in output


def test_plain_output_violations_present_shows_found_message() -> None:
    output = _capture_plain([_v()])
    assert "Violations found" in output


def test_plain_output_multiple_violations_all_present() -> None:
    v1 = _v(rule_id="rule-a", line=1)
    v2 = _v(rule_id="rule-b", line=2)
    output = _capture_plain([v1, v2])
    assert "rule-a" in output
    assert "rule-b" in output


# ---------------------------------------------------------------------------
# report_json
# ---------------------------------------------------------------------------

def test_json_output_is_valid_json() -> None:
    result = report_json([_v()])
    data = json.loads(result)
    assert isinstance(data, dict)


def test_json_output_has_summary_key() -> None:
    data = json.loads(report_json([]))
    assert "summary" in data


def test_json_output_has_violations_key() -> None:
    data = json.loads(report_json([]))
    assert "violations" in data


def test_json_summary_error_count() -> None:
    violations = [_v(severity="error"), _v(severity="error"), _v(severity="warning")]
    data = json.loads(report_json(violations))
    assert data["summary"]["errors"] == 2
    assert data["summary"]["warnings"] == 1
    assert data["summary"]["total"] == 3


def test_json_empty_violations_list() -> None:
    data = json.loads(report_json([]))
    assert data["violations"] == []
    assert data["summary"]["total"] == 0
    assert data["summary"]["errors"] == 0


def test_json_violation_has_required_fields() -> None:
    v = _v(rule_id="no-todo", severity="error", file="src/app.py", line=5)
    data = json.loads(report_json([v]))
    item = data["violations"][0]
    assert item["rule_id"] == "no-todo"
    assert item["severity"] == "error"
    assert item["file"] == "src/app.py"
    assert item["line"] == 5
    assert "matched_text" in item


def test_json_multiple_violations_all_serialised() -> None:
    violations = [_v(line=1), _v(line=2), _v(line=3)]
    data = json.loads(report_json(violations))
    assert len(data["violations"]) == 3
    lines = [item["line"] for item in data["violations"]]
    assert lines == [1, 2, 3]
