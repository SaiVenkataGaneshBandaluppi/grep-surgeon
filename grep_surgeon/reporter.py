# MIT License - see LICENSE file for details
from __future__ import annotations

import json
import sys
from typing import TextIO

from grep_surgeon.scanner import Violation


def report_plain(violations: list[Violation], out: TextIO | None = None) -> None:
    stream: TextIO = out if out is not None else sys.stdout

    for v in violations:
        level = v.severity.upper()
        location = f"{v.file}:{v.line}"
        stream.write(
            f"{level:<8} {v.rule_id:<30} {location:<35} Found: \"{v.matched_text}\"\n"
        )

    errors = sum(1 for v in violations if v.severity == "error")
    warnings = sum(1 for v in violations if v.severity == "warning")

    stream.write("\n")
    stream.write(
        f"{errors} error{'s' if errors != 1 else ''}, "
        f"{warnings} warning{'s' if warnings != 1 else ''}\n"
    )

    if violations:
        stream.write("Scan complete. Violations found.\n")
    else:
        stream.write("Scan complete. No violations found.\n")


def report_json(violations: list[Violation]) -> str:
    errors = sum(1 for v in violations if v.severity == "error")
    warnings = sum(1 for v in violations if v.severity == "warning")

    payload: dict[str, object] = {
        "summary": {
            "errors": errors,
            "warnings": warnings,
            "total": len(violations),
        },
        "violations": [
            {
                "rule_id": v.rule_id,
                "severity": v.severity,
                "file": v.file,
                "line": v.line,
                "matched_text": v.matched_text,
            }
            for v in violations
        ],
    }

    return json.dumps(payload, indent=2)
