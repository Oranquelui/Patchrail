from __future__ import annotations

import re
import subprocess
import tomllib
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
JAPANESE_TEXT_RE = re.compile(r"[\u3040-\u30ff\u3400-\u9fff]")


def test_repo_includes_mit_license_file() -> None:
    license_path = REPO_ROOT / "LICENSE"

    assert license_path.exists()
    content = license_path.read_text()
    assert "MIT License" in content
    assert "Permission is hereby granted, free of charge" in content


def test_pyproject_declares_mit_license_metadata() -> None:
    project = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text())["project"]

    assert project["license"] == "MIT"
    assert project["license-files"] == ["LICENSE"]
    assert "License :: OSI Approved :: MIT License" not in project["classifiers"]


def test_pyproject_declares_public_pypi_metadata() -> None:
    project = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text())["project"]

    assert project["version"] == "0.2.0"
    assert project["description"] == "Local verification and approval packets for AI coding agent work"
    assert "ai-coding" in project["keywords"]
    assert "verification" in project["keywords"]
    assert "approval" in project["keywords"]
    assert "Programming Language :: Python :: 3.12" in project["classifiers"]
    assert "Topic :: Software Development :: Quality Assurance" in project["classifiers"]
    assert project["urls"]["Repository"] == "https://github.com/louistoyozaki/Patchrail"
    assert project["urls"]["Documentation"] == "https://github.com/louistoyozaki/Patchrail#readme"


def test_readme_mentions_mit_license() -> None:
    readme = (REPO_ROOT / "README.md").read_text()

    assert "## License" in readme
    assert "MIT" in readme


def test_english_readme_exists_without_japanese_text() -> None:
    readme = (REPO_ROOT / "README.md").read_text()

    assert not JAPANESE_TEXT_RE.search(readme)
    assert "README.ja.md" in readme
    assert "patchrail-start.jpg" in readme
    assert "pipx install patchrail" in readme
    assert "patchrail packet show" in readme
    assert "patchrail verify" in readme


def test_readme_screenshot_exists_at_repo_root() -> None:
    screenshot = REPO_ROOT / "patchrail-start.jpg"

    assert screenshot.exists()


def test_public_repo_excludes_internal_planning_directories() -> None:
    result = subprocess.run(
        ["git", "ls-files", ".taskmaster", "docs/superpowers"],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    assert result.stdout == ""


def test_gitignore_ignores_internal_planning_directories() -> None:
    gitignore = (REPO_ROOT / ".gitignore").read_text()

    assert ".taskmaster/" in gitignore
    assert "docs/superpowers/" in gitignore


def test_gitignore_ignores_local_environment_files() -> None:
    gitignore = (REPO_ROOT / ".gitignore").read_text()

    assert ".env" in gitignore
    assert ".env.*" in gitignore


def test_public_markdown_docs_do_not_include_local_absolute_paths() -> None:
    markdown_files = [
        REPO_ROOT / "README.md",
        REPO_ROOT / "README.ja.md",
        *sorted((REPO_ROOT / "docs").glob("*.md")),
    ]

    for markdown_file in markdown_files:
        content = markdown_file.read_text()
        assert ("/User" + "s/") not in content, markdown_file


def test_japanese_readme_exists_and_links_back_to_english_readme() -> None:
    readme_ja = REPO_ROOT / "README.ja.md"

    assert readme_ja.exists()
    content = readme_ja.read_text()
    assert "README.md" in content
    assert JAPANESE_TEXT_RE.search(content)
