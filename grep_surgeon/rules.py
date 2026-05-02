# MIT License - see LICENSE file for details
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

REQUIRED_FIELDS: frozenset[str] = frozenset(
    {"id", "description", "pattern", "file_extensions", "severity"}
)
VALID_SEVERITIES: frozenset[str] = frozenset({"error", "warning"})


@dataclass
class Rule:
    id: str
    description: str
    pattern: re.Pattern[str]
    file_extensions: tuple[str, ...]
    severity: str


@dataclass
class RuleSet:
    rules: list[Rule] = field(default_factory=list)

    @classmethod
    def from_file(cls, path: Path) -> RuleSet:
        try:
            with open(path, encoding="utf-8") as fh:
                data = yaml.safe_load(fh)
        except yaml.YAMLError as err:
            raise ValueError(f"Invalid YAML in rules file: {err}") from err
        except OSError as err:
            raise ValueError(f"Cannot read rules file: {err}") from err

        if not isinstance(data, dict) or "rules" not in data:
            raise ValueError("Rules file must contain a top-level 'rules' key")

        raw_rules = data["rules"]
        if not isinstance(raw_rules, list):
            raise ValueError("'rules' must be a list")

        return cls(rules=[_parse_rule(raw) for raw in raw_rules])


def _parse_rule(raw: Any) -> Rule:
    if not isinstance(raw, dict):
        raise ValueError(f"Each rule must be a mapping, got {type(raw).__name__}")

    missing = REQUIRED_FIELDS - set(raw.keys())
    if missing:
        rule_id = raw.get("id", "<unknown>")
        raise ValueError(
            f"Rule '{rule_id}' is missing required fields: {sorted(missing)}"
        )

    rule_id: str = str(raw["id"])
    severity: str = str(raw["severity"])

    if severity not in VALID_SEVERITIES:
        raise ValueError(
            f"Rule '{rule_id}' has invalid severity '{severity}'. "
            f"Must be one of: {sorted(VALID_SEVERITIES)}"
        )

    try:
        compiled: re.Pattern[str] = re.compile(str(raw["pattern"]))
    except re.error as err:
        raise ValueError(
            f"Rule '{rule_id}' has invalid regex pattern: {err}"
        ) from err

    extensions = raw["file_extensions"]
    if not isinstance(extensions, list) or len(extensions) == 0:
        raise ValueError(
            f"Rule '{rule_id}' must have a non-empty file_extensions list"
        )

    return Rule(
        id=rule_id,
        description=str(raw["description"]),
        pattern=compiled,
        file_extensions=tuple(str(e) for e in extensions),
        severity=severity,
    )


def validate_rules(path: Path) -> list[str]:
    errors: list[str] = []

    try:
        with open(path, encoding="utf-8") as fh:
            data = yaml.safe_load(fh)
    except yaml.YAMLError as err:
        return [f"Invalid YAML: {err}"]
    except OSError as err:
        return [f"Cannot read file: {err}"]

    if not isinstance(data, dict) or "rules" not in data:
        return ["Rules file must contain a top-level 'rules' key"]

    raw_rules = data.get("rules", [])
    if not isinstance(raw_rules, list):
        return ["'rules' must be a list"]

    for raw in raw_rules:
        if not isinstance(raw, dict):
            errors.append("Each rule must be a mapping")
            continue

        rule_id: str = str(raw.get("id", "<unknown>"))
        missing = REQUIRED_FIELDS - set(raw.keys())
        if missing:
            errors.append(f"Rule '{rule_id}' is missing fields: {sorted(missing)}")
            continue

        if str(raw["severity"]) not in VALID_SEVERITIES:
            errors.append(
                f"Rule '{rule_id}' has invalid severity '{raw['severity']}'"
            )

        try:
            re.compile(str(raw["pattern"]))
        except re.error as err:
            errors.append(f"Rule '{rule_id}' has invalid pattern: {err}")

        exts = raw.get("file_extensions")
        if not isinstance(exts, list) or len(exts) == 0:
            errors.append(
                f"Rule '{rule_id}' must have a non-empty file_extensions list"
            )

    return errors
