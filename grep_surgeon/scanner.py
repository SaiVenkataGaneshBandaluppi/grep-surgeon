# MIT License - see LICENSE file for details
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from grep_surgeon.rules import Rule, RuleSet

ALWAYS_SKIP: frozenset[str] = frozenset(
    {".git", ".pytest_cache", "__pycache__", "node_modules"}
)


@dataclass(frozen=True)
class Violation:
    rule_id: str
    severity: str
    file: str
    line: int
    matched_text: str


def scan(
    ruleset: RuleSet,
    target: Path,
    exclude: list[str] | None = None,
) -> list[Violation]:
    exclude_normalized: set[str] = {e.rstrip("/\\") for e in (exclude or [])}
    violations: list[Violation] = []

    for file_path in _walk(target, exclude_normalized):
        for rule in ruleset.rules:
            if file_path.suffix not in rule.file_extensions:
                continue
            violations.extend(_scan_file(file_path, rule, target))

    return violations


def _walk(root: Path, exclude: set[str]) -> list[Path]:
    results: list[Path] = []

    for dirpath_str, dirnames, filenames in os.walk(str(root), topdown=True):
        current = Path(dirpath_str)

        dirnames[:] = [
            d
            for d in dirnames
            if d not in ALWAYS_SKIP
            and not _dir_is_excluded(current / d, root, exclude)
        ]

        for filename in filenames:
            results.append(current / filename)

    return results


def _dir_is_excluded(dir_path: Path, root: Path, exclude: set[str]) -> bool:
    try:
        relative = dir_path.relative_to(root)
    except ValueError:
        return False

    relative_str = str(relative).replace("\\", "/")

    for excl in exclude:
        if relative_str == excl:
            return True
        if relative_str.startswith(excl + "/"):
            return True
        if relative.name == excl:
            return True

    return False


def _scan_file(file_path: Path, rule: Rule, root: Path) -> list[Violation]:
    try:
        raw = file_path.read_bytes()
    except OSError:
        return []

    try:
        content = raw.decode("utf-8")
    except UnicodeDecodeError:
        return []

    try:
        relative = str(file_path.relative_to(root)).replace("\\", "/")
    except ValueError:
        relative = str(file_path).replace("\\", "/")

    violations: list[Violation] = []
    for line_num, line_text in enumerate(content.splitlines(), start=1):
        if rule.pattern.search(line_text):
            violations.append(
                Violation(
                    rule_id=rule.id,
                    severity=rule.severity,
                    file=relative,
                    line=line_num,
                    matched_text=line_text.strip(),
                )
            )

    return violations
