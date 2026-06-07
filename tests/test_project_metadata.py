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

    assert project["version"] == "0.2.0a1"
    assert project["description"] == "Local-first verification and approval packets for AI coding agent work"
    assert "ai-coding" in project["keywords"]
    assert "verification" in project["keywords"]
    assert "approval" in project["keywords"]
    assert "Programming Language :: Python :: 3.12" in project["classifiers"]
    assert "Topic :: Software Development :: Quality Assurance" in project["classifiers"]
    assert project["urls"]["Repository"] == "https://github.com/Oranquelui/Patchrail"
    assert project["urls"]["Documentation"] == "https://github.com/Oranquelui/Patchrail#readme"


def test_release_version_is_synchronized() -> None:
    project = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text())["project"]
    init_globals: dict[str, str] = {}
    exec((REPO_ROOT / "patchrail" / "__init__.py").read_text(), init_globals)

    assert project["version"] == "0.2.0a1"
    assert init_globals["__version__"] == project["version"]


def test_changelog_documents_alpha_release_direction() -> None:
    changelog = (REPO_ROOT / "CHANGELOG.md").read_text()

    assert "## v0.2.0-alpha.1 - 2026-06-26" in changelog
    assert "Brief Schema v1" in changelog
    assert "Runner Contract v1" in changelog
    assert "Evidence Bundle v1" in changelog
    assert "skill-first, CLI-backed" in changelog


def test_readme_mentions_mit_license() -> None:
    readme = (REPO_ROOT / "README.md").read_text()

    assert "## License" in readme
    assert "MIT" in readme


def test_readme_separates_current_release_from_next_direction() -> None:
    readme = (REPO_ROOT / "README.md").read_text()

    assert "## Current Release" in readme
    assert "## Next Direction" in readme
    current = readme.split("## Current Release", 1)[1].split("## Next Direction", 1)[0]
    next_direction = readme.split("## Next Direction", 1)[1]
    assert "Brief Schema v1" in current
    assert "Runner Contract v1" in current
    assert "Evidence Bundle v1" in current
    assert "ApprovalProfile v1" not in current
    assert "ApprovalProfile v1" in next_direction
    assert "RunLedger v1" in next_direction
    assert "patchrail-supervise" in next_direction


def test_english_readme_exists_without_japanese_text() -> None:
    readme = (REPO_ROOT / "README.md").read_text()

    assert not JAPANESE_TEXT_RE.search(readme)
    assert "README.ja.md" in readme
    assert "patchrail-start.jpg" in readme
    assert "scripts/install_cli.sh" in readme
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


def test_public_patchrail_supervise_skill_exists() -> None:
    skill_path = REPO_ROOT / "skills" / "patchrail-supervise" / "SKILL.md"

    assert skill_path.exists()
    content = skill_path.read_text()
    assert "name: patchrail-supervise" in content
    assert "patchrail brief validate" in content
    assert "patchrail contracts runner" in content
    assert "Do not approve or reject the final outcome without explicit human instruction." in content
    assert "Skill instructions are not the enforcement layer." in content


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
