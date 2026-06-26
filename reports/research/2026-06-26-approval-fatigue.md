# Approval Fatigue Research - 2026-06-26

## Purpose

Patchrail's next direction was reviewed against current public feedback around coding-agent permissions, approval prompts, and human-in-the-loop design. The goal was to decide whether Patchrail should stay CLI-only, move toward portable skills, or build a heavier dashboard/approval surface.

## Sources Reviewed

1. Anthropic Engineering, [How we built Claude Code auto mode](https://www.anthropic.com/engineering/claude-code-auto-mode), 2026-03-25.
2. Kilo Code issue [LLM-based bash command auto-approval #9138](https://github.com/Kilo-Org/kilocode/issues/9138), opened 2026-04-17.
3. Anthropic Claude Code issue [Feature Request: Auto-approve Recommended Actions Setting #7275](https://github.com/anthropics/claude-code/issues/7275).
4. Anthropic Claude Code issue [Task-specific auto-approval incorrectly persists globally #22958](https://github.com/anthropics/claude-code/issues/22958), opened 2026-02-04.
5. OpenAI Codex discussion [How to tell Codex NOT to ask for confirmation all the time? #7740](https://github.com/openai/codex/discussions/7740).
6. OpenAI Codex issue [Cannot set approval_policy = "on-failure" from within CLI #3129](https://github.com/openai/codex/issues/3129), opened 2025-09-03.
7. LangChain4j issue [How to implement Human-in-the-loop? #3405](https://github.com/langchain4j/langchain4j/issues/3405), opened 2025-07-25.
8. LlamaIndex discussion [Managing agentic LLM systems in production #20485](https://github.com/run-llama/llama_index/discussions/20485).
9. Addy Osmani, [Agentic Code Review](https://addyosmani.com/blog/agentic-code-review/), 2026.

## Findings

1. Repeated manual approvals are not a durable safety mechanism.
   Anthropic reports very high permission-prompt acceptance in Claude Code and explicitly frames the problem as approval fatigue. GitHub issues around Claude Code and Codex show the same user pain: people want fewer routine interruptions during active development.

2. Users are asking for a middle ground, not only a bypass.
   Kilo Code, Claude Code, and Codex discussions all point toward a policy/classifier/profile layer between "ask for everything" and "allow everything." This matches Patchrail's planned `ApprovalProfile v1`.

3. Scope lifetime matters.
   Claude Code's task-specific auto-approval bug report shows that a temporary approval must not silently become a global mode. Patchrail should record the effective approval profile per run, not only per repository or global config.

4. Human-in-the-loop needs to be non-blocking and resumable.
   LangChain4j's issue calls out non-blocking, crash-recoverable, and future-oriented human-in-the-loop requirements. This supports Patchrail's local disk records, review queue, and resumable approval packets.

5. Native agent permissions remain part of enforcement.
   Codex discussions distinguish approval prompts from conversation check-ins and emphasize that sandbox/approval settings are runtime policy, not prompt text. Patchrail skills should guide behavior, while enforcement remains in host permissions, sandboxing, Patchrail policy records, hooks, and evidence.

6. Humans should move up to scope, risk, and final accountability.
   Agentic code-review commentary points toward risk-sorted review and escalation rather than reading every line or approving every step. Patchrail should optimize for scope setup, verification evidence, review packets, and high-blast-radius escalation.

## Product Decision

The next Patchrail direction should be:

1. Skill-first and CLI-backed.
   Provide a portable `patchrail-supervise` skill for Codex, Claude Code, Grok Build, and compatible agents, but keep the CLI/headless core as the durable state engine.

2. Approval-profile driven.
   Implement `ApprovalProfile v1` with `auto`, `ask`, and `deny` classes so low-risk work can proceed without repeated prompts while boundary-crossing actions still escalate.

3. Run-ledger backed.
   Implement `RunLedger v1` so each run records the effective profile, auto-approved classes, escalations, denials, receipts, and rollback notes.

4. Evidence-centered.
   Continue improving verification records, approval packets, and review queues before building a dashboard or broad provider abstraction.

5. Explicit about limits.
   Skill instructions are useful distribution and behavior-shaping tools, but they are not the security layer. Patchrail must not claim that a `SKILL.md` file can replace sandboxing, native approval settings, or human final approval.
