from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

from patchrail.core.exceptions import PatchrailError
from patchrail.models.entities import CostMetrics, Plan, Task
from patchrail.runners.base import Runner, RunnerResult


class ClaudeCodeRunner(Runner):
    name = "claude_code"
    mode = "stub"
    command = None

    def run(self, task: Task, plan: Plan, workspace_path: Path, run_id: str) -> RunnerResult:
        output_path = workspace_path / "output.json"
        output_path.write_text(
            json.dumps(
                {
                    "execution_summary": f"stub execution for {task.id}",
                    "diff_summary": "- Stubbed execution produced a synthetic patch summary.\n",
                }
            )
        )
        return RunnerResult(
            stdout=f"[claude_code] Executed {task.id} using plan {plan.id}\n",
            stderr="",
            execution_summary=(
                "# Execution Summary\n\n"
                f"Runner: {self.name}\nTask: {task.title}\nPlan Summary: {plan.summary}\n"
            ),
            diff_summary="- Stubbed execution produced a synthetic patch summary.\n- Reviewable output is persisted locally.\n",
            cost_metrics=CostMetrics(
                prompt_tokens=320,
                completion_tokens=180,
                estimated_usd=0.42,
                elapsed_seconds=12.5,
            ),
            exit_code=0,
            runner_trace=None,
        )


class GrokRunner(Runner):
    name = "grok_runner"
    mode = "stub"
    command = None

    def run(self, task: Task, plan: Plan, workspace_path: Path, run_id: str) -> RunnerResult:
        output_path = workspace_path / "output.json"
        output_path.write_text(
            json.dumps(
                {
                    "execution_summary": f"stub execution for {task.id}",
                    "diff_summary": "- Stubbed alternate executor output captured for comparison.\n",
                }
            )
        )
        return RunnerResult(
            stdout=f"[grok_runner] Executed {task.id} using plan {plan.id}\n",
            stderr="",
            execution_summary=(
                "# Execution Summary\n\n"
                f"Runner: {self.name}\nTask: {task.title}\nPlan Summary: {plan.summary}\n"
            ),
            diff_summary="- Stubbed alternate executor output captured for comparison.\n",
            cost_metrics=CostMetrics(
                prompt_tokens=280,
                completion_tokens=165,
                estimated_usd=0.31,
                elapsed_seconds=9.75,
            ),
            exit_code=0,
            runner_trace=None,
        )


class ShellConfiguredRunner(Runner):
    def __init__(self, name: str, command: str) -> None:
        self.name = name
        self.mode = "shell"
        self.command = command

    def run(self, task: Task, plan: Plan, workspace_path: Path, run_id: str) -> RunnerResult:
        output_path = workspace_path / "output.json"
        env = os.environ.copy()
        project_root = Path(__file__).resolve().parents[2]
        python_path = env.get("PYTHONPATH")
        env["PYTHONPATH"] = (
            f"{project_root}{os.pathsep}{python_path}" if python_path else str(project_root)
        )
        env.update(
            {
                "PATCHRAIL_RUN_ID": run_id,
                "PATCHRAIL_RUNNER_NAME": self.name,
                "PATCHRAIL_TASK_FILE": str(workspace_path / "task.json"),
                "PATCHRAIL_PLAN_FILE": str(workspace_path / "plan.json"),
                "PATCHRAIL_OUTPUT_FILE": str(output_path),
            }
        )
        completed = subprocess.run(
            self.command,
            shell=True,
            cwd=workspace_path,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        if completed.returncode != 0:
            raise PatchrailError(
                f"Runner '{self.name}' command failed with exit code {completed.returncode}: {completed.stderr.strip()}"
            )

        payload = {}
        if output_path.exists():
            payload = json.loads(output_path.read_text())

        cost_metrics = payload.get(
            "cost_metrics",
            {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "estimated_usd": 0.0,
                "elapsed_seconds": 0.0,
            },
        )
        execution_summary = payload.get("execution_summary", completed.stdout.strip() or f"shell execution for {task.id}")
        diff_summary = payload.get("diff_summary", "- No diff summary provided by shell runner.\n")

        return RunnerResult(
            stdout=completed.stdout,
            stderr=completed.stderr,
            execution_summary=execution_summary,
            diff_summary=diff_summary,
            cost_metrics=CostMetrics.from_dict(cost_metrics),
            exit_code=completed.returncode,
            runner_trace=payload.get("runner_trace") if isinstance(payload.get("runner_trace"), dict) else None,
        )


def build_runner(name: str, command: str | None = None) -> Runner:
    configured_command = command
    if configured_command is None:
        env_var = f"PATCHRAIL_{name.upper()}_CMD"
        configured_command = os.getenv(env_var)
    if configured_command:
        return ShellConfiguredRunner(name=name, command=configured_command)
    if name == "claude_code":
        return ClaudeCodeRunner()
    if name == "grok_runner":
        return GrokRunner()
    if name == "codex_runner":
        return ShellConfiguredRunner(name=name, command=f"{os.sys.executable} -m patchrail.runners.local_harness")
    raise PatchrailError(f"Unknown runner '{name}'.")
