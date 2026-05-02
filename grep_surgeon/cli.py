# MIT License - see LICENSE file for details
from __future__ import annotations

import sys
from pathlib import Path

import click

from grep_surgeon.reporter import report_json, report_plain
from grep_surgeon.rules import RuleSet, validate_rules
from grep_surgeon.scanner import scan


@click.group()
def main() -> None:
    """grep-surgeon: scan codebases for configurable rule violations."""


@main.command(name="scan")
@click.option(
    "--rules",
    "rules_path",
    required=True,
    type=click.Path(exists=True, path_type=Path),
    help="Path to YAML rules file.",
)
@click.option(
    "--target",
    "target_path",
    default=".",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    help="Directory to scan (default: current directory).",
)
@click.option(
    "--exclude",
    multiple=True,
    help="Directory or file pattern to exclude. Repeatable.",
)
@click.option(
    "--format",
    "output_format",
    default="plain",
    type=click.Choice(["plain", "json"]),
    help="Output format: plain (default) or json.",
)
@click.option(
    "--quiet",
    is_flag=True,
    help="Suppress all output; rely on exit code only.",
)
def scan_command(
    rules_path: Path,
    target_path: Path,
    exclude: tuple[str, ...],
    output_format: str,
    quiet: bool,
) -> None:
    """Scan a directory for rule violations."""
    try:
        ruleset = RuleSet.from_file(rules_path)
    except ValueError as err:
        click.echo(f"Error loading rules: {err}", err=True)
        sys.exit(2)

    violations = scan(ruleset, target_path, list(exclude))

    if not quiet:
        if output_format == "json":
            click.echo(report_json(violations))
        else:
            report_plain(violations)

    has_errors = any(v.severity == "error" for v in violations)
    if has_errors:
        sys.exit(1)


@main.command(name="validate")
@click.option(
    "--rules",
    "rules_path",
    required=True,
    type=click.Path(exists=True, path_type=Path),
    help="Path to YAML rules file.",
)
def validate_command(rules_path: Path) -> None:
    """Validate a rules YAML file."""
    errors = validate_rules(rules_path)
    if errors:
        for err_msg in errors:
            click.echo(f"  - {err_msg}", err=True)
        click.echo("Rules file is invalid.", err=True)
        sys.exit(1)
    click.echo("Rules file is valid.")
