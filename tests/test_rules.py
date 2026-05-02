from __future__ import annotations

import re
from pathlib import Path

import pytest

from grep_surgeon.rules import RuleSet, validate_rules

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_rules(tmp_path: Path, content: str) -> Path:
    p = tmp_path / "rules.yaml"
    p.write_text(content, encoding="utf-8")
    return p


MINIMAL_VALID = """\
rules:
  - id: no-todo
    description: No TODO comments
    pattern: 'TODO'
    file_extensions: ['.py']
    severity: error
"""

MULTI_RULE_VALID = """\
rules:
  - id: no-todo
    description: No TODO comments
    pattern: 'TODO'
    file_extensions: ['.py', '.md']
    severity: error
  - id: no-fixme
    description: No FIXME comments
    pattern: 'FIXME'
    file_extensions: ['.py']
    severity: warning
"""


# ---------------------------------------------------------------------------
# RuleSet.from_file -- valid inputs
# ---------------------------------------------------------------------------

def test_load_valid_rules_file(tmp_path: Path) -> None:
    path = _write_rules(tmp_path, MINIMAL_VALID)
    ruleset = RuleSet.from_file(path)
    assert len(ruleset.rules) == 1


def test_rule_has_correct_id(tmp_path: Path) -> None:
    path = _write_rules(tmp_path, MINIMAL_VALID)
    rule = RuleSet.from_file(path).rules[0]
    assert rule.id == "no-todo"


def test_rule_has_correct_severity(tmp_path: Path) -> None:
    path = _write_rules(tmp_path, MINIMAL_VALID)
    rule = RuleSet.from_file(path).rules[0]
    assert rule.severity == "error"


def test_rule_stores_compiled_regex(tmp_path: Path) -> None:
    path = _write_rules(tmp_path, MINIMAL_VALID)
    rule = RuleSet.from_file(path).rules[0]
    assert isinstance(rule.pattern, re.Pattern)
    assert rule.pattern.search("x = 1  # TODO: do something") is not None


def test_rule_extensions_are_tuple(tmp_path: Path) -> None:
    path = _write_rules(tmp_path, MINIMAL_VALID)
    rule = RuleSet.from_file(path).rules[0]
    assert isinstance(rule.file_extensions, tuple)
    assert ".py" in rule.file_extensions


def test_load_multiple_rules(tmp_path: Path) -> None:
    path = _write_rules(tmp_path, MULTI_RULE_VALID)
    ruleset = RuleSet.from_file(path)
    assert len(ruleset.rules) == 2
    ids = [r.id for r in ruleset.rules]
    assert "no-todo" in ids
    assert "no-fixme" in ids


def test_warning_severity_loaded(tmp_path: Path) -> None:
    path = _write_rules(tmp_path, MULTI_RULE_VALID)
    fixme_rule = next(r for r in RuleSet.from_file(path).rules if r.id == "no-fixme")
    assert fixme_rule.severity == "warning"


# ---------------------------------------------------------------------------
# RuleSet.from_file -- invalid inputs
# ---------------------------------------------------------------------------

def test_invalid_yaml_raises_value_error(tmp_path: Path) -> None:
    path = tmp_path / "rules.yaml"
    path.write_text("rules: [\nunclosed", encoding="utf-8")
    with pytest.raises(ValueError, match="Invalid YAML"):
        RuleSet.from_file(path)


def test_missing_rules_key_raises_value_error(tmp_path: Path) -> None:
    path = _write_rules(tmp_path, "config:\n  foo: bar\n")
    with pytest.raises(ValueError, match="top-level 'rules' key"):
        RuleSet.from_file(path)


def test_missing_required_field_raises_value_error(tmp_path: Path) -> None:
    yaml_content = """\
rules:
  - id: no-todo
    pattern: 'TODO'
    file_extensions: ['.py']
    severity: error
"""
    path = _write_rules(tmp_path, yaml_content)
    with pytest.raises(ValueError, match="missing required fields"):
        RuleSet.from_file(path)


def test_invalid_severity_raises_value_error(tmp_path: Path) -> None:
    yaml_content = """\
rules:
  - id: no-todo
    description: Test
    pattern: 'TODO'
    file_extensions: ['.py']
    severity: critical
"""
    path = _write_rules(tmp_path, yaml_content)
    with pytest.raises(ValueError, match="invalid severity"):
        RuleSet.from_file(path)


def test_invalid_regex_pattern_raises_value_error(tmp_path: Path) -> None:
    yaml_content = """\
rules:
  - id: bad-regex
    description: Test
    pattern: '[unclosed'
    file_extensions: ['.py']
    severity: error
"""
    path = _write_rules(tmp_path, yaml_content)
    with pytest.raises(ValueError, match="invalid regex pattern"):
        RuleSet.from_file(path)


def test_empty_file_extensions_raises_value_error(tmp_path: Path) -> None:
    yaml_content = """\
rules:
  - id: no-todo
    description: Test
    pattern: 'TODO'
    file_extensions: []
    severity: error
"""
    path = _write_rules(tmp_path, yaml_content)
    with pytest.raises(ValueError, match="non-empty file_extensions"):
        RuleSet.from_file(path)


def test_nonexistent_file_raises_value_error(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="Cannot read rules file"):
        RuleSet.from_file(tmp_path / "does_not_exist.yaml")


# ---------------------------------------------------------------------------
# validate_rules
# ---------------------------------------------------------------------------

def test_validate_rules_returns_empty_list_for_valid(tmp_path: Path) -> None:
    path = _write_rules(tmp_path, MINIMAL_VALID)
    assert validate_rules(path) == []


def test_validate_rules_catches_missing_field(tmp_path: Path) -> None:
    yaml_content = """\
rules:
  - id: no-todo
    pattern: 'TODO'
    file_extensions: ['.py']
    severity: error
"""
    path = _write_rules(tmp_path, yaml_content)
    errors = validate_rules(path)
    assert len(errors) == 1
    assert "missing fields" in errors[0]


def test_validate_rules_catches_bad_severity(tmp_path: Path) -> None:
    yaml_content = """\
rules:
  - id: no-todo
    description: Test
    pattern: 'TODO'
    file_extensions: ['.py']
    severity: blocker
"""
    path = _write_rules(tmp_path, yaml_content)
    errors = validate_rules(path)
    assert any("invalid severity" in e for e in errors)


def test_validate_rules_catches_bad_pattern(tmp_path: Path) -> None:
    yaml_content = """\
rules:
  - id: bad-rule
    description: Test
    pattern: '[unclosed'
    file_extensions: ['.py']
    severity: error
"""
    path = _write_rules(tmp_path, yaml_content)
    errors = validate_rules(path)
    assert any("invalid pattern" in e for e in errors)


def test_validate_rules_catches_bad_yaml(tmp_path: Path) -> None:
    path = tmp_path / "rules.yaml"
    path.write_text("rules: [\nbad yaml", encoding="utf-8")
    errors = validate_rules(path)
    assert len(errors) == 1
    assert "Invalid YAML" in errors[0]


def test_validate_rules_catches_empty_extensions(tmp_path: Path) -> None:
    yaml_content = """\
rules:
  - id: no-todo
    description: Test
    pattern: 'TODO'
    file_extensions: []
    severity: error
"""
    path = _write_rules(tmp_path, yaml_content)
    errors = validate_rules(path)
    assert any("non-empty file_extensions" in e for e in errors)


# ---------------------------------------------------------------------------
# CLI: validate command
# ---------------------------------------------------------------------------

def test_cli_validate_exits_0_for_valid_rules(tmp_path: Path) -> None:
    from click.testing import CliRunner

    from grep_surgeon.cli import main

    path = _write_rules(tmp_path, MINIMAL_VALID)
    runner = CliRunner()
    result = runner.invoke(main, ["validate", "--rules", str(path)])
    assert result.exit_code == 0
    assert "valid" in result.output.lower()


def test_cli_validate_exits_1_for_invalid_rules(tmp_path: Path) -> None:
    from click.testing import CliRunner

    from grep_surgeon.cli import main

    yaml_content = """\
rules:
  - id: bad-rule
    pattern: 'TODO'
    file_extensions: ['.py']
    severity: error
"""
    path = _write_rules(tmp_path, yaml_content)
    runner = CliRunner()
    result = runner.invoke(main, ["validate", "--rules", str(path)])
    assert result.exit_code == 1
