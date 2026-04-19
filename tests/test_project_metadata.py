from __future__ import annotations

import re
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

    assert project["license"] == {"text": "MIT"}
    assert "License :: OSI Approved :: MIT License" in project["classifiers"]


def test_readme_mentions_mit_license() -> None:
    readme = (REPO_ROOT / "README.md").read_text()

    assert "## License" in readme
    assert "MIT" in readme


def test_english_readme_exists_without_japanese_text() -> None:
    readme = (REPO_ROOT / "README.md").read_text()

    assert not JAPANESE_TEXT_RE.search(readme)
    assert "README.ja.md" in readme
    assert "docs/assets/patchrail-start.jpg" in readme


def test_readme_screenshot_asset_exists() -> None:
    screenshot = REPO_ROOT / "docs" / "assets" / "patchrail-start.jpg"

    assert screenshot.exists()


def test_public_repo_excludes_internal_planning_directories() -> None:
    assert not (REPO_ROOT / ".taskmaster").exists()
    assert not (REPO_ROOT / "docs" / "superpowers").exists()


def test_gitignore_ignores_internal_planning_directories() -> None:
    gitignore = (REPO_ROOT / ".gitignore").read_text()

    assert ".taskmaster/" in gitignore
    assert "docs/superpowers/" in gitignore


def test_public_markdown_docs_do_not_include_local_absolute_paths() -> None:
    markdown_files = [
        REPO_ROOT / "README.md",
        REPO_ROOT / "README.ja.md",
        *sorted((REPO_ROOT / "docs").glob("*.md")),
    ]

    for markdown_file in markdown_files:
        content = markdown_file.read_text()
        assert "/Users/" not in content, markdown_file


def test_japanese_readme_exists_and_links_back_to_english_readme() -> None:
    readme_ja = REPO_ROOT / "README.ja.md"

    assert readme_ja.exists()
    content = readme_ja.read_text()
    assert "README.md" in content
    assert JAPANESE_TEXT_RE.search(content)
