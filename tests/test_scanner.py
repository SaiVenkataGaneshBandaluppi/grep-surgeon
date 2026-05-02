from __future__ import annotations

import re
from pathlib import Path

from grep_surgeon.rules import Rule, RuleSet
from grep_surgeon.scanner import scan

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_rule(
    rule_id: str = "test-rule",
    pattern: str = "TODO",
    extensions: tuple[str, ...] = (".py",),
    severity: str = "error",
) -> Rule:
    return Rule(
        id=rule_id,
        description="Test rule",
        pattern=re.compile(pattern),
        file_extensions=extensions,
        severity=severity,
    )


def _ruleset(*rules: Rule) -> RuleSet:
    return RuleSet(rules=list(rules))


# ---------------------------------------------------------------------------
# Basic violation detection
# ---------------------------------------------------------------------------

def test_finds_violation_in_matching_file(tmp_path: Path) -> None:
    target = tmp_path / "src"
    target.mkdir()
    (target / "app.py").write_text("x = 1  # TODO: fix later\n", encoding="utf-8")

    violations = scan(_ruleset(_make_rule()), target)
    assert len(violations) == 1
    assert violations[0].rule_id == "test-rule"


def test_no_violation_when_pattern_absent(tmp_path: Path) -> None:
    target = tmp_path / "src"
    target.mkdir()
    (target / "app.py").write_text("x = 1 + 2\n", encoding="utf-8")

    violations = scan(_ruleset(_make_rule()), target)
    assert violations == []


def test_correct_line_number_reported(tmp_path: Path) -> None:
    target = tmp_path / "src"
    target.mkdir()
    content = "line one\nline two\nTODO: fix this\nline four\n"
    (target / "app.py").write_text(content, encoding="utf-8")

    violations = scan(_ruleset(_make_rule()), target)
    assert len(violations) == 1
    assert violations[0].line == 3


def test_violation_file_path_is_relative_to_target(tmp_path: Path) -> None:
    target = tmp_path / "src"
    target.mkdir()
    (target / "app.py").write_text("# TODO\n", encoding="utf-8")

    violations = scan(_ruleset(_make_rule()), target)
    assert violations[0].file == "app.py"


def test_nested_file_path_uses_forward_slashes(tmp_path: Path) -> None:
    target = tmp_path / "src"
    sub = target / "pkg"
    sub.mkdir(parents=True)
    (sub / "mod.py").write_text("# TODO\n", encoding="utf-8")

    violations = scan(_ruleset(_make_rule()), target)
    assert "/" in violations[0].file
    assert "\\" not in violations[0].file


def test_matched_text_is_stripped_of_whitespace(tmp_path: Path) -> None:
    target = tmp_path / "src"
    target.mkdir()
    (target / "app.py").write_text("    x = 1  # TODO: fix\n", encoding="utf-8")

    violations = scan(_ruleset(_make_rule()), target)
    assert violations[0].matched_text == "x = 1  # TODO: fix"


def test_multiple_violations_in_one_file(tmp_path: Path) -> None:
    target = tmp_path / "src"
    target.mkdir()
    content = "# TODO: first\nx = 1\n# TODO: second\n"
    (target / "app.py").write_text(content, encoding="utf-8")

    violations = scan(_ruleset(_make_rule()), target)
    assert len(violations) == 2
    assert violations[0].line == 1
    assert violations[1].line == 3


def test_multiple_rules_each_find_own_violations(tmp_path: Path) -> None:
    target = tmp_path / "src"
    target.mkdir()
    content = "# TODO: do something\n# FIXME: broken\n"
    (target / "app.py").write_text(content, encoding="utf-8")

    rule_todo = _make_rule("no-todo", "TODO")
    rule_fixme = _make_rule("no-fixme", "FIXME", severity="warning")
    violations = scan(_ruleset(rule_todo, rule_fixme), target)

    ids = [v.rule_id for v in violations]
    assert "no-todo" in ids
    assert "no-fixme" in ids


# ---------------------------------------------------------------------------
# File extension filtering
# ---------------------------------------------------------------------------

def test_filters_by_file_extension(tmp_path: Path) -> None:
    target = tmp_path / "src"
    target.mkdir()
    (target / "app.py").write_text("# TODO\n", encoding="utf-8")
    (target / "notes.md").write_text("TODO: update\n", encoding="utf-8")

    violations = scan(_ruleset(_make_rule(extensions=(".py",))), target)
    assert all(v.file.endswith(".py") for v in violations)
    assert len(violations) == 1


def test_no_violation_for_wrong_extension(tmp_path: Path) -> None:
    target = tmp_path / "src"
    target.mkdir()
    (target / "data.json").write_text('{"key": "TODO"}', encoding="utf-8")

    violations = scan(_ruleset(_make_rule(extensions=(".py",))), target)
    assert violations == []


# ---------------------------------------------------------------------------
# Directory skipping
# ---------------------------------------------------------------------------

def test_skips_git_directory(tmp_path: Path) -> None:
    target = tmp_path / "src"
    git_dir = target / ".git"
    git_dir.mkdir(parents=True)
    (git_dir / "config.py").write_text("# TODO\n", encoding="utf-8")

    violations = scan(_ruleset(_make_rule()), target)
    assert violations == []


def test_skips_pycache_directory(tmp_path: Path) -> None:
    target = tmp_path / "src"
    cache = target / "__pycache__"
    cache.mkdir(parents=True)
    (cache / "module.py").write_text("# TODO\n", encoding="utf-8")

    violations = scan(_ruleset(_make_rule()), target)
    assert violations == []


def test_skips_node_modules_directory(tmp_path: Path) -> None:
    target = tmp_path / "src"
    nm = target / "node_modules"
    nm.mkdir(parents=True)
    (nm / "lib.py").write_text("# TODO\n", encoding="utf-8")

    violations = scan(_ruleset(_make_rule()), target)
    assert violations == []


def test_skips_pytest_cache_directory(tmp_path: Path) -> None:
    target = tmp_path / "src"
    pc = target / ".pytest_cache"
    pc.mkdir(parents=True)
    (pc / "v.py").write_text("# TODO\n", encoding="utf-8")

    violations = scan(_ruleset(_make_rule()), target)
    assert violations == []


def test_skips_user_excluded_directory(tmp_path: Path) -> None:
    target = tmp_path / "src"
    tests_dir = target / "tests"
    tests_dir.mkdir(parents=True)
    (tests_dir / "test_app.py").write_text("# TODO\n", encoding="utf-8")
    (target / "app.py").write_text("x = 1\n", encoding="utf-8")

    violations = scan(_ruleset(_make_rule()), target, exclude=["tests"])
    assert violations == []


def test_exclude_does_not_affect_sibling_directories(tmp_path: Path) -> None:
    target = tmp_path / "src"
    tests_dir = target / "tests"
    app_dir = target / "app"
    tests_dir.mkdir(parents=True)
    app_dir.mkdir(parents=True)
    (tests_dir / "test_foo.py").write_text("# TODO\n", encoding="utf-8")
    (app_dir / "main.py").write_text("# TODO\n", encoding="utf-8")

    violations = scan(_ruleset(_make_rule()), target, exclude=["tests"])
    assert len(violations) == 1
    assert "app/main.py" in violations[0].file


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

def test_empty_file_produces_no_violations(tmp_path: Path) -> None:
    target = tmp_path / "src"
    target.mkdir()
    (target / "empty.py").write_text("", encoding="utf-8")

    violations = scan(_ruleset(_make_rule()), target)
    assert violations == []


def test_binary_file_produces_no_violations(tmp_path: Path) -> None:
    target = tmp_path / "src"
    target.mkdir()
    (target / "data.py").write_bytes(b"\xff\xfe\x00\x01\x80\x90\xaa\xbb")

    violations = scan(_ruleset(_make_rule()), target)
    assert violations == []


def test_file_with_no_trailing_newline(tmp_path: Path) -> None:
    target = tmp_path / "src"
    target.mkdir()
    (target / "app.py").write_bytes(b"# TODO: no newline at end")

    violations = scan(_ruleset(_make_rule()), target)
    assert len(violations) == 1
    assert violations[0].line == 1


# ---------------------------------------------------------------------------
# CLI: scan command
# ---------------------------------------------------------------------------

def _write_rules_file(tmp_path: Path, severity: str = "error") -> Path:
    content = f"""\
rules:
  - id: no-todo
    description: No TODO comments
    pattern: 'TODO'
    file_extensions: ['.py']
    severity: {severity}
"""
    path = tmp_path / "rules.yaml"
    path.write_text(content, encoding="utf-8")
    return path


def test_cli_scan_exits_1_when_errors_found(tmp_path: Path) -> None:
    from click.testing import CliRunner

    from grep_surgeon.cli import main

    rules = _write_rules_file(tmp_path, "error")
    target = tmp_path / "src"
    target.mkdir()
    (target / "app.py").write_text("# TODO: fix\n", encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(main, ["scan", "--rules", str(rules), "--target", str(target)])
    assert result.exit_code == 1


def test_cli_scan_exits_0_when_no_violations(tmp_path: Path) -> None:
    from click.testing import CliRunner

    from grep_surgeon.cli import main

    rules = _write_rules_file(tmp_path, "error")
    target = tmp_path / "src"
    target.mkdir()
    (target / "app.py").write_text("x = 1 + 2\n", encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(main, ["scan", "--rules", str(rules), "--target", str(target)])
    assert result.exit_code == 0


def test_cli_scan_warnings_only_exits_0(tmp_path: Path) -> None:
    from click.testing import CliRunner

    from grep_surgeon.cli import main

    rules = _write_rules_file(tmp_path, "warning")
    target = tmp_path / "src"
    target.mkdir()
    (target / "app.py").write_text("# TODO: warning only\n", encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(main, ["scan", "--rules", str(rules), "--target", str(target)])
    assert result.exit_code == 0


def test_cli_scan_json_format_produces_valid_json(tmp_path: Path) -> None:
    import json

    from click.testing import CliRunner

    from grep_surgeon.cli import main

    rules = _write_rules_file(tmp_path, "error")
    target = tmp_path / "src"
    target.mkdir()
    (target / "app.py").write_text("# TODO: fix\n", encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(
        main,
        ["scan", "--rules", str(rules), "--target", str(target), "--format", "json"],
    )
    data = json.loads(result.output)
    assert "summary" in data
    assert "violations" in data
    assert data["summary"]["errors"] == 1


def test_cli_scan_quiet_suppresses_output(tmp_path: Path) -> None:
    from click.testing import CliRunner

    from grep_surgeon.cli import main

    rules = _write_rules_file(tmp_path, "error")
    target = tmp_path / "src"
    target.mkdir()
    (target / "app.py").write_text("# TODO: fix\n", encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(
        main,
        ["scan", "--rules", str(rules), "--target", str(target), "--quiet"],
    )
    assert result.output.strip() == ""
    assert result.exit_code == 1


def test_cli_scan_exclude_flag_skips_directory(tmp_path: Path) -> None:
    from click.testing import CliRunner

    from grep_surgeon.cli import main

    rules = _write_rules_file(tmp_path, "error")
    target = tmp_path / "src"
    tests_dir = target / "tests"
    tests_dir.mkdir(parents=True)
    (tests_dir / "test_app.py").write_text("# TODO\n", encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "scan",
            "--rules",
            str(rules),
            "--target",
            str(target),
            "--exclude",
            "tests",
        ],
    )
    assert result.exit_code == 0
