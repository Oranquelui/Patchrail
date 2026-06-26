# Patchrail

Patchrail is a local-first supervised coding-agent control plane for future-anchored product execution. The current alpha records `task -> plan -> run -> review -> approval` as explicit local state transitions with planning briefs, runner contracts, evidence bundles, artifact metadata, decision traces, fallback approvals, and approval ledgers.

![Patchrail terminal loading screen](patchrail-start.jpg)

Terminal loading/start screen rendered by `patchrail start`. Patchrail is intentionally usable from a terminal before any hosted dashboard exists.

Patchrail keeps coding-agent supervision local instead of hiding planning, review, approval, and artifacts behind a backend runtime. The CLI remains the canonical state engine. The next product direction is skill-first and CLI-backed, so Codex, Claude Code, Grok Build, or another compatible coding agent can follow a reusable Patchrail skill while the local CLI keeps durable records.

Japanese usage notes live in [README.ja.md](README.ja.md).

## Development Purpose

Patchrail is being developed to make supervised coding-agent work auditable before, during, and after implementation. Modern coding agents can move from a vague instruction to repository changes very quickly; the hard part is proving what the operator meant, what boundaries were agreed, what the executor actually did, and why a human approved the result.

The core purpose is to preserve that chain as local, inspectable records:

```text
human intent -> planning briefs -> plan snapshot -> runner execution -> evidence bundle -> review -> approval
```

This is why Patchrail starts with a CLI and headless core rather than a dashboard. The first requirement is not presentation. The first requirement is a reliable local record that can be checked, diffed, tested, and reviewed without trusting a remote service.

## Why This Is Necessary

Coding-agent workflows usually fail in the gaps between intention, execution, and review:

- A chat transcript can describe intent, but it is not a durable operational record.
- A plan can look reasonable, but it becomes unsafe if it is disconnected from the assumptions and boundaries that produced it.
- A review can inspect the final diff, but it cannot reconstruct whether the executor stayed inside the original product, ontology, and approval boundaries.
- A dashboard can make the workflow look organized, but it can also hide which system owns canonical state, evidence, and final approval.

Patchrail addresses those gaps by separating five current concerns:

1. Predict the desired future state before implementation.
2. Define the real-world ontology and approval boundaries before implementation.
3. Define post-implementation acceptance criteria before implementation.
4. Snapshot those inputs into a canonical plan before the runner executes.
5. Capture post-implementation evidence before review and approval.

The result is not an autonomous-agent launcher and not an approval-button factory. It is a supervision rail: a local control plane that turns human judgment into scope, evidence, review, and final outcome approval.

## What You Can Show In 3 Minutes

Patchrail demonstrates a practical safety boundary for coding agents in customer or client repositories:

1. Create a task that describes the supervised work.
2. Attach future, ontology, and product briefs before implementation begins.
3. Validate the brief sequence and store a canonical plan that references those briefs.
4. Inspect the Runner Contract v1 handoff before execution.
5. Run an executor behind an explicit runner assignment.
6. Review the persisted Evidence Bundle v1 artifacts before any final approval.
7. Record the human approval decision and ledgers locally.

The point is not to make an agent autonomous by default. The point is to make the handoff between human intent, agent execution, review evidence, and final approval inspectable from disk.

For a public-facing walkthrough, see [Supervised Agent Rollout](docs/case-studies/supervised-agent-rollout.md).

## Why Patchrail

- Keep the canonical workflow record in Patchrail rather than in a backend runtime.
- Let users bring the coding agent they already use by moving toward portable Agent Skills and future plugins.
- Preserve clear role separation across planner, reviewer, executor, and human approver.
- Constrain present implementation work with operator-defined completion, ontology, and scope documents rather than letting the next tool call decide the shape of the product.
- Make approval boundaries, fallback approvals, artifacts, and decision traces inspectable from disk.
- Support optional workflow backends, including LangGraph, without handing over canonical state ownership.

## Current Release

`v0.2.0-alpha.1` consolidates the development work since `v0.1.0` around three local contracts:

- Brief Schema v1: `future`, `ontology`, and `product` planning briefs now carry `schema_version=patchrail.brief_schema.v1`; plan snapshots preserve the same schema marker.
- Runner Contract v1: shell-backed runners receive an explicit workspace and reserved environment boundary, inspectable through `patchrail contracts runner`.
- Evidence Bundle v1: run artifacts carry `schema_version=patchrail.evidence_bundle.v1`, manifest metadata, structured runner trace support, and collected runner-local artifacts.

The current alpha also updates the smoke flow to create all three briefs, validate the sequence, execute the local harness, collect runner artifacts, and complete review plus human approval from local state.

## Next Direction

Patchrail is moving toward a skill-first, CLI-backed workflow. The next release line should reduce approval fatigue by defining policy once, letting low-risk work proceed inside that policy, and escalating boundary crossings instead of asking humans to approve every routine edit or local command.

The next direction is:

- `ApprovalProfile v1`: define `auto`, `ask`, and `deny` action classes for local coding-agent work.
- `RunLedger v1`: record the effective profile, auto-approved action classes, escalations, denials, receipts, and rollback notes.
- `patchrail-supervise`: harden the portable Agent Skill scaffold for Codex, Claude Code, Grok Build, and compatible agents while keeping the CLI as the durable local engine.

Skill instructions are not the enforcement layer. Enforcement must come from host-agent permissions, sandbox settings, Patchrail policy records, hooks where available, and local evidence.

## Phase 1 Direction

The next planning layer is aimed at turning Patchrail into a supervised control plane for product definition and risk-aware delegation before execution starts.

Phase 1 is structured around two onboarding passes:

- `machine/runtime onboarding`: select the provider set, access modes, workflow backend, and approval-profile defaults that this machine can supervise safely
- `project/planning onboarding`: define the task, `Future Completion Brief`, `Ontology Brief`, `Product Brief`, future approval profile, and then generate the canonical plan

The brief sequence is intentionally ordered:

1. `Future Completion Brief` / prediction layer: describe what should be true in the future, the invariants that must hold, the failure conditions, and the non-goals.
2. `Ontology Brief` / reality-boundary layer: define what exists, what does not exist, who owns what, and where approval or artifact boundaries sit.
3. `Product Brief` / post-implementation acceptance layer: define the user problem, the MVP boundary, and what must be true after implementation for users and operators.
4. `Approval Profile` / delegation-policy layer, next: define low-risk actions the agent can take automatically, risky actions that require escalation, and denied actions.
5. `Plan` / execution-translation layer: convert those constraints into executable implementation steps that Patchrail can supervise.
6. `Harness` / post-implementation evidence layer: after executor run and before review, capture execution summary, diff summary, stdout/stderr, invocation, runner trace, and artifact metadata. `RunLedger v1` is the next planned extension to this layer.

Patchrail continues to own the canonical `Task`, `Plan`, `Run`, `ReviewResult`, `ApprovalRecord`, ledgers, and artifact bundles. The future, ontology, and product briefs are plan-scoped companion artifacts or metadata, not a second canonical state machine.

Patchrail’s preferred distribution path is now skill-first and CLI-backed. The repository includes a first `patchrail-supervise` skill scaffold that teaches compatible agents how to set scope, collect evidence, escalate boundary crossings, and hand off final review. The CLI remains the durable local engine behind that skill.

Brief records now declare the local companion-artifact schema version `patchrail.brief_schema.v1`. Generated project scaffolds include that schema marker, persisted brief records store it with the content digest, and canonical plan references snapshot it so later plan and review steps can reconstruct which brief contract was used.

Runner handoff now declares the local workspace and reserved environment schema version `patchrail.runner_contract.v1`. Shell-backed runners receive the contract schema version plus task, plan, output, artifact, and trace paths without owning canonical task state, plans, reviews, approvals, or ledgers.

Files written to the reserved runner artifact directory are collected by Patchrail into the canonical Evidence Bundle v1 manifest as `runner_artifact` entries. The runner can provide exchange files, but Patchrail still owns the stored evidence bundle.

Inspect that handoff contract without starting a run:

```bash
patchrail contracts runner
patchrail --json contracts runner
```

The first local path for that layer is available through:

```bash
patchrail brief create --task-id <task_id> --kind future --file future.md
patchrail brief create --task-id <task_id> --kind ontology --file ontology.md
patchrail brief create --task-id <task_id> --kind product --file product.md
patchrail brief validate --task-id <task_id>
patchrail brief list --task-id <task_id>
patchrail brief show --brief-id <brief_id>
```

`patchrail brief show` displays the brief's `schema_version` in human-readable output. JSON mode exposes the same value at `brief.schema_version`.

`patchrail brief validate` is a read-side readiness check for Brief Schema v1. It reports the required `future -> ontology -> product` sequence, present kinds, and missing kinds without changing task state or blocking manual plan creation.

When `patchrail plan` stores the canonical plan, it snapshots references to the task's current briefs under `planning_briefs` while leaving the canonical state machine unchanged.

Phase 1 also gives the three live providers distinct planning roles instead of treating them as interchangeable model slots:

- `Codex / OpenAI`: structure the plan and preserve the supervisory viewpoint
- `Claude`: expand the implementation path and keep the plan coherent across longer reasoning spans
- `Grok`: challenge weak assumptions, missing constraints, and product drift

The goal is triangulated planning with explicit traces, not generic multi-model fan-out.

## Install CLI

From the repository root:

```bash
cd /path/to/Patchrail
brew install pipx
pipx ensurepath
sh scripts/install_cli.sh --python "$(command -v python3.13)"
patchrail --help
patchrail setup
patchrail start
```

To install the optional LangGraph runtime into the same `pipx` environment:

```bash
cd /path/to/Patchrail
sh scripts/install_cli.sh --python "$(command -v python3.13)" --with-langgraph
```

The `patchrail` command is exposed through the package entrypoint. `scripts/install_cli.sh` only installs that entrypoint via `pipx`. If your default `python3` is older than 3.12, pass an explicit interpreter path such as `--python /opt/homebrew/bin/python3.13`.

Patchrail defaults to human-readable CLI output. Use `patchrail --json ...` only for automation and scripting.

`patchrail setup` is the first-run CLI path. It bootstraps runtime config, runs role preflight checks, and returns concrete next commands. Use `patchrail setup project --title ... --description ...` to create a task plus editable planning brief scaffolds. Edit those files, persist them with `patchrail brief create ...`, and only then create the canonical plan.

## Quickstart

```bash
cd /path/to/Patchrail
sh scripts/install_cli.sh --python "$(command -v python3.13)"
patchrail setup
patchrail setup project --title "First task" --description "Describe the supervised work"
# edit the generated future/ontology/product files, then persist each edited brief
patchrail brief create --task-id <task_id> --kind future --file <future_brief_file>
patchrail brief create --task-id <task_id> --kind ontology --file <ontology_brief_file>
patchrail brief create --task-id <task_id> --kind product --file <product_brief_file>
patchrail plan --task-id <task_id> --auto
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
patchrail setup
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
patchrail brief list --task-id <task_id>
patchrail brief show --brief-id <brief_id>
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
- [Brief Schema v1](docs/contracts/brief-schema-v1.md)
- [Runner Contract v1](docs/contracts/runner-contract-v1.md)
- [Evidence Bundle v1](docs/contracts/evidence-bundle-v1.md)
- [Patchrail Supervise Skill](skills/patchrail-supervise/SKILL.md)
- [MVP](docs/mvp.md)
- [Local Testing](docs/local-testing.md)
- [Backlog](docs/backlog.md)
- [Changelog](CHANGELOG.md)
- [Agents Contract](AGENTS.md)
- [Japanese README](README.ja.md)

## License

MIT. See [LICENSE](LICENSE).
