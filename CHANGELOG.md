# Changelog

All notable changes to this project will be documented in this file.

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
