from __future__ import annotations

import tomllib
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_repo_includes_mit_license_file() -> None:
    license_path = REPO_ROOT / "LICENSE"

    assert license_path.exists()
    content = license_path.read_text()
    assert "MIT License" in content
    assert "Permission is hereby granted, free of charge" in content


def test_pyproject_declares_mit_license_metadata() -> None:
    project = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text())["project"]

    assert project["license"] == {"text": "MIT"}
    assert "License :: OSI Approved :: MIT License" in project["classifiers"]


def test_readme_mentions_mit_license() -> None:
    readme = (REPO_ROOT / "README.md").read_text()

    assert "## License" in readme
    assert "MIT" in readme
