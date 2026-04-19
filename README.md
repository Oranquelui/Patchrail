# Patchrail

Patchrail is a local-first supervised coding-agent control plane. It stays focused on a CLI-first, headless-core-first workflow that records `task -> plan -> run -> review -> approval` as explicit local state transitions, together with artifact bundles, decision traces, and approval ledgers.

Patchrail keeps coding-agent supervision in a local CLI instead of hiding planning, review, approval, and artifacts behind a backend runtime.

Japanese usage notes live in [README.ja.md](README.ja.md).

## Why Patchrail

- Keep the canonical workflow record in Patchrail rather than in a backend runtime.
- Preserve clear role separation across planner, reviewer, executor, and human approver.
- Make approval boundaries, fallback approvals, artifacts, and decision traces inspectable from disk.
- Support optional workflow backends, including LangGraph, without handing over canonical state ownership.

## Install CLI

From the repository root:

```bash
cd /path/to/Patchrail
brew install pipx
pipx ensurepath
sh scripts/install_cli.sh --python "$(command -v python3.13)"
patchrail --help
patchrail start
```

To install the optional LangGraph runtime into the same `pipx` environment:

```bash
cd /path/to/Patchrail
sh scripts/install_cli.sh --python "$(command -v python3.13)" --with-langgraph
```

The `patchrail` command is exposed through the package entrypoint. `scripts/install_cli.sh` only installs that entrypoint via `pipx`. If your default `python3` is older than 3.12, pass an explicit interpreter path such as `--python /opt/homebrew/bin/python3.13`.

Patchrail defaults to human-readable CLI output. Use `patchrail --json ...` only for automation and scripting.

## Quickstart

```bash
cd /path/to/Patchrail
sh scripts/install_cli.sh --python "$(command -v python3.13)"
patchrail start
```

`patchrail start` opens the interactive shell in TTY sessions. Use `patchrail start --once` to render the home screen and exit immediately.

Inside the shell you can run the existing subcommands directly:

```text
help
doctor
list tasks
task create --title "First task" --description "Describe the work"
exit
```

## Basic Flow

Deterministic local flow:

```bash
cd /path/to/Patchrail
patchrail config init
patchrail preflight --role planner
patchrail preflight --role reviewer
patchrail preflight --role executor --runner auto
sh scripts/local_smoke_test.sh
```

LangGraph-backed auto plan and review:

```bash
cd /path/to/Patchrail
sh scripts/install_cli.sh --python "$(command -v python3.13)" --with-langgraph
patchrail config init --workflow-backend langgraph
PATCHRAIL_WORKFLOW_BACKEND=langgraph PATCHRAIL_AUTO_PLAN=1 PATCHRAIL_AUTO_REVIEW=1 sh scripts/local_smoke_test.sh
```

Real readiness checks:

```bash
cd /path/to/Patchrail
patchrail config init --preset real --workflow-backend local
patchrail preflight --role executor --runner auto
```

## Workflow Backends

Patchrail keeps the canonical records for:

- `Task`
- `Plan`
- `Run`
- `ReviewResult`
- `ApprovalRecord`
- `Approval Ledger`
- `Decision Trace`
- `Artifact Bundle`

The default workflow backend is `local`. LangGraph is available as an optional subordinate backend for `plan --auto` and `review --auto`.

Current LangGraph graphs are stateless:

- planner: `collect_plan_context -> generate_plan -> validate_plan -> finalize_plan`
- reviewer: `collect_review_context -> generate_review -> validate_review -> finalize_review`

Patchrail stores only workflow metadata such as `graph_version`, `checkpointer`, `delegate_backend`, and `node_trace` on the canonical plan or review record. Approval meaning, artifact ownership, and the canonical state machine remain Patchrail-owned.

## Current Live Support

Auto generation:

- planner: `claude subscription`, `codex api`
- reviewer: `codex subscription`, `claude api`

Execution:

- `codex subscription`
- `claude subscription`
- `codex api`
- `claude api`
- `grok api`

`grok` is API-only in the default policy set. Patchrail does not currently ship a default `grok subscription` candidate.

## Local Storage

Patchrail persists state under `.patchrail/` or the directory pointed to by `PATCHRAIL_HOME`.

Useful read-side commands:

```bash
patchrail list tasks
patchrail list plans
patchrail list runs
patchrail list reviews
patchrail list approvals
patchrail list fallback-requests
patchrail list preflight-snapshots
patchrail list artifact-bundles --has-trace
patchrail --json status --task-id <task_id>
```

## Docs

- [Architecture](docs/architecture.md)
- [MVP](docs/mvp.md)
- [Local Testing](docs/local-testing.md)
- [Backlog](docs/backlog.md)
- [Changelog](CHANGELOG.md)
- [Agents Contract](AGENTS.md)
- [Japanese README](README.ja.md)

## License

MIT. See [LICENSE](LICENSE).
