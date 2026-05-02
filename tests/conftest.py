from __future__ import annotations

import pytest

SIMPLE_RULES_YAML = """\
rules:
  - id: no-todo
    description: No TODO comments allowed in source files
    pattern: 'TODO'
    file_extensions: ['.py', '.md', '.txt']
    severity: error
  - id: no-fixme
    description: No FIXME comments allowed in source files
    pattern: 'FIXME'
    file_extensions: ['.py']
    severity: warning
"""


@pytest.fixture
def rules_yaml(tmp_path: pytest.TempPathFactory) -> pytest.FixtureRequest:
    path = tmp_path / "rules.yaml"
    path.write_text(SIMPLE_RULES_YAML, encoding="utf-8")
    return path


@pytest.fixture
def target_dir(tmp_path: pytest.TempPathFactory) -> pytest.FixtureRequest:
    d = tmp_path / "project"
    d.mkdir()
    return d
