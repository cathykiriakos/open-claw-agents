"""agents/executor.py — Executor Agent implementation."""

from __future__ import annotations

import asyncio
import subprocess
from typing import Optional

from agents.base_agent import OpenClawAgent


class ExecutorAgent(OpenClawAgent):
    """
    Executes code, CLI commands, and manages git operations.

    PRIMARY:  Execution — bash commands, Python scripts, git operations
    FLEX:     Can research before executing; can schedule via CalendarAgent
    APPROVAL: git push / commit / merge and destructive ops always prompt first
    """

    DESTRUCTIVE_OPS = {"rm ", "rmdir", "delete", "drop", "truncate", "clear"}
    GIT_APPROVAL_OPS = {"git push", "git commit", "git merge", "git reset --hard", "git rebase"}

    def __init__(self, context_store, inference_agent, working_dir: str = "."):
        super().__init__(
            agent_id="executor",
            agent_name="Executor Agent",
            primary_role="execution",
            context_store=context_store,
            inference_agent=inference_agent,
        )
        self.working_dir = working_dir

    async def _execute_task(self, prompt: str, task_id: str) -> str:
        prompt_lower = prompt.lower()

        needs_approval = (
            any(op in prompt_lower for op in self.DESTRUCTIVE_OPS)
            or any(op in prompt_lower for op in self.GIT_APPROVAL_OPS)
        )

        if needs_approval:
            gate = "git_push" if any(op in prompt_lower for op in self.GIT_APPROVAL_OPS) else "destructive_op"
            approved = await self.request_approval(task_id, gate)
            if not approved:
                return f"[executor] Action blocked — approval denied or timed out."

        # Use Gemma to plan the execution steps
        plan_prompt = (
            f"You are an execution planner. Given this task, describe the exact shell commands "
            f"or steps needed. Be specific and safe.\n\nTask: {prompt}\n\n"
            f"List the commands/steps in order. If anything is unclear, say so."
        )
        response = await self.inference.infer(prompt=plan_prompt, task_type="complex")

        self.context.audit_action(
            self.agent_id,
            "execution_planned",
            {"prompt": prompt[:200], "plan": response.content[:200]},
        )

        return response.content

    # ------------------------------------------------------------------
    # Tools
    # ------------------------------------------------------------------

    async def run_command(self, command: str, require_approval: bool = False, task_id: Optional[str] = None) -> str:
        """Run a shell command and return stdout. Blocks on approval if flagged."""
        if require_approval and task_id:
            approved = await self.request_approval(task_id, "destructive_op")
            if not approved:
                return "Command blocked — approval denied."

        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=60,
                cwd=self.working_dir,
            )
            output = result.stdout or result.stderr
            self.context.audit_action(
                self.agent_id,
                "command_executed",
                {"command": command, "exit_code": result.returncode, "output": output[:200]},
            )
            return output
        except subprocess.TimeoutExpired:
            return "Command timed out after 60 seconds."
        except Exception as exc:
            return f"Command failed: {exc}"

    async def git_status(self) -> str:
        return await self.run_command("git status")

    async def git_diff(self) -> str:
        return await self.run_command("git diff")

    async def git_commit(self, message: str, task_id: str) -> str:
        approved = await self.request_approval(task_id, "git_push")
        if not approved:
            return "git commit blocked — approval denied."
        return await self.run_command(f'git add -A && git commit -m "{message}"')

    async def git_push(self, branch: str, task_id: str) -> str:
        approved = await self.request_approval(task_id, "git_push")
        if not approved:
            return "git push blocked — approval denied."
        return await self.run_command(f"git push origin {branch}")

    async def explain_and_run(self, task: str, task_id: str) -> tuple[str, str]:
        """Ask Gemma to explain what it will do, then run it. Returns (explanation, output)."""
        explain_prompt = f"In one sentence, what shell command would accomplish: '{task}'? Then provide just the command on the next line."
        resp = await self.inference.infer(prompt=explain_prompt, task_type="simple")
        lines = [l.strip() for l in resp.content.strip().splitlines() if l.strip()]
        explanation = lines[0] if lines else ""
        command = lines[-1] if len(lines) > 1 else ""

        if not command:
            return explanation, "Could not determine a command to run."

        output = await self.run_command(command)
        return explanation, output
