# Changelog

All notable changes to this project will be documented in this file.

## v0.2.0 - Unreleased

### Added

- `patchrail verify` for recording operator-specified verification commands, exit codes, elapsed time, and stdout/stderr output paths.
- `patchrail list verifications` and `patchrail list review-queue` for local review triage across AI coding runs.
- `patchrail packet show|export` for Markdown and JSON approval packets built from existing local records.
- `patchrail setup project --guided` for Delivery Contract-oriented Future, Ontology, and Product prompt scaffolds while preserving existing brief storage.
- Release check script for build, isolated wheel install, CLI help, and local smoke verification.

### Changed

- Public project metadata and README now position Patchrail around AI coding verification and approval packets.
- Local smoke testing now includes verify and packet export.

## v0.1.0 - 2026-04-19

Initial public MVP release.

### Added

- Local-first canonical records for tasks, plans, runs, reviews, approvals, ledgers, decision traces, and artifact bundles.
- CLI workflow for `task`, `plan`, `run`, `review`, `approve`, `reject`, `status`, `logs`, `artifacts`, and `list`.
- `patchrail start` interactive shell and `patchrail doctor` onboarding surface.
- Role-aware preflight and assignment ontology across planner, reviewer, and executor candidates.
- Local and real config presets, including explicit fallback approval handling.
- Optional workflow backend seam with a default local backend and optional LangGraph planner/reviewer backend.
- Manifest-style artifact metadata and optional runner trace support.
- Local smoke test flow and pipx-based CLI installer.
