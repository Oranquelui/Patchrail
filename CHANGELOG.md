# Changelog

All notable changes to this project will be documented in this file.

## v0.2.0-alpha.1 - 2026-06-26

Direction-setting alpha release for AI coding verification, approval packets, and the skill-first, CLI-backed Patchrail roadmap.

### Added

- Brief Schema v1 for `future`, `ontology`, and `product` planning briefs, including persisted `schema_version` markers and plan-snapshot references.
- `patchrail brief validate` for read-only readiness checks over the required planning brief sequence.
- Runner Contract v1 for shell-backed executor handoff, reserved environment variables, workspace paths, and read-only CLI inspection through `patchrail contracts runner`.
- Evidence Bundle v1 manifest metadata, schema markers, structured runner trace support, and canonical collection of runner-local artifacts.
- `patchrail verify` for recording operator-specified verification commands, exit codes, elapsed time, and stdout/stderr output paths.
- `patchrail list verifications` and `patchrail list review-queue` for local review triage across AI coding runs.
- `patchrail packet show|export` for Markdown and JSON approval packets built from existing local records.
- `patchrail setup project --guided` for Delivery Contract-oriented Future, Ontology, and Product prompt scaffolds while preserving existing brief storage.
- Release check script for build, isolated wheel install, CLI help, and local smoke verification.
- Local smoke coverage that creates all three briefs, validates them, executes the local harness, records verification evidence, exports an approval packet, reviews, and records human approval.
- First public `patchrail-supervise` Agent Skill scaffold for Codex, Claude Code, Grok Build, and compatible agents.
- Approval-fatigue research note grounding the next `ApprovalProfile v1`, `RunLedger v1`, and skill-first delegation direction.

### Changed

- README and PRD direction now separate implemented alpha behavior from the next `ApprovalProfile v1`, `RunLedger v1`, and skill-first delegation work.
- Public positioning now emphasizes local verification evidence and approval packets for AI coding agent work.
- Runner invocation metadata now includes the Runner Contract schema version, artifact directory, and trace file path.
- Local harness output now includes runtime contract evidence and a reproducibility report collected into the canonical evidence bundle.
- Project metadata now uses modern license metadata and public package keywords for AI coding verification.

### Not Yet Included

- `ApprovalProfile v1` runtime storage and editing.
- `RunLedger v1` action receipt, escalation, denial, and rollback persistence.
- Codex plugin packaging for the `patchrail-supervise` skill after the scaffold is validated.

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
