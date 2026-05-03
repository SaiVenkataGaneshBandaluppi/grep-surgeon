# grep-surgeon

<p align="center">
  <img src="assets/logo.svg" alt="grep-surgeon logo" width="120"/>
</p>

<p align="center">
  A production-grade CLI tool that scans codebases for configurable rule violations.
</p>

---

## What it does

grep-surgeon reads a YAML rules file and recursively scans a target directory for pattern violations. For each match it reports the file, line number, rule ID, and the offending text. It exits with code 1 when any `error`-severity rules fire, making it a drop-in CI gate.

---

## Features

- YAML-driven rules: regex patterns with per-extension targeting and severity levels
- Recursive directory scan with smart defaults (.git, `__pycache__`, node_modules skipped)
- `--exclude` flag to skip directories or patterns at scan time
- Plain and JSON output formats
- Singular `error` / `warning` severity distinction
- `validate` command to lint rules files before using them in CI
- Exit code 1 on errors, 0 on warnings-only or clean runs
- Zero runtime dependencies beyond PyYAML and Click

---

## Tech stack

- Python 3.11+
- [Click](https://click.palletsprojects.com/) - CLI framework
- [PyYAML](https://pyyaml.org/) - rules file parsing
- [pytest](https://pytest.org/) + coverage for testing
- [Ruff](https://docs.astral.sh/ruff/) for linting
- [Bandit](https://bandit.readthedocs.io/) for security scanning

---

## Prerequisites

- Python 3.11 or later
- pip

---

## Setup

```bash
git clone https://github.com/SaiVenkataGaneshBandaluppi/grep-surgeon.git
cd grep-surgeon
pip install -r requirements.txt
pip install -e .
```

---

## Usage

**Scan a directory:**
```bash
grep-surgeon scan --rules examples/rules.yaml --target ./myproject
```

**Scan with exclusions:**
```bash
grep-surgeon scan --rules rules.yaml --target . --exclude tests/ --exclude data/
```

**JSON output (for CI pipelines):**
```bash
grep-surgeon scan --rules rules.yaml --target ./src --format json
```

**Silent mode (exit code only):**
```bash
grep-surgeon scan --rules rules.yaml --target ./src --quiet
echo $?  # 0 = clean, 1 = errors found
```

**Validate a rules file:**
```bash
grep-surgeon validate --rules rules.yaml
```

### Example output

```
ERROR    no-em-dash                     app/main.py:42                      Found: "some text with a dash"
WARNING  no-optional-type               app/schemas.py:12                   Found: "Optional[str]"

1 error, 1 warning
Scan complete. Violations found.
```

### Rules file format

```yaml
rules:
  - id: no-optional-type
    description: Use X | None instead of Optional[X] in Python 3.10+
    pattern: "Optional\\["
    file_extensions: [".py"]
    severity: warning
```

| Field | Required | Description |
|---|---|---|
| `id` | yes | Unique string identifier |
| `description` | yes | Human-readable explanation |
| `pattern` | yes | Python regex pattern |
| `file_extensions` | yes | List of file extensions to scan |
| `severity` | yes | `error` (causes exit 1) or `warning` |

See `examples/rules.yaml` for a full set of example rules.

---

## Running tests

```bash
pip install -r requirements-dev.txt
python -m coverage run -m pytest tests/ -v
python -m coverage report
```

---

## License

MIT. See [LICENSE](LICENSE) for details.
