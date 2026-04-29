"""agents/base_agent.py — Abstract base class for all Open Claw agents."""

from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from typing import Optional

from agents.context_store import ContextStore
from agents.inference_agent import OpenClawInferenceAgent


class OpenClawAgent(ABC):
    """Base class extended by Researcher, Data, Executor, and Calendar agents."""

    def __init__(
        self,
        agent_id: str,
        agent_name: str,
        primary_role: str,
        context_store: ContextStore,
        inference_agent: OpenClawInferenceAgent,
        cost_threshold_usd: float = 2.0,
    ):
        self.agent_id = agent_id
        self.agent_name = agent_name
        self.primary_role = primary_role
        self.context = context_store
        self.inference = inference_agent
        self.cost_threshold = cost_threshold_usd
        self.current_task_id: Optional[str] = None

    async def process_task(self, prompt: str, task_type: str = "default") -> str:
        task_id = self.context.create_task(
            agent_id=self.agent_id,
            task_type=task_type,
            prompt=prompt,
        )
        self.current_task_id = task_id
        self.context.audit_action(self.agent_id, "task_started", {"task_id": task_id, "task_type": task_type})

        try:
            result = await self._execute_task(prompt, task_id)
            self.context.update_task_status(task_id, "completed", result)
            self.context.audit_action(self.agent_id, "task_completed", {"task_id": task_id})
            return result
        except Exception as exc:
            self.context.update_task_status(task_id, "failed", str(exc))
            self.context.audit_action(self.agent_id, "task_failed", {"task_id": task_id, "error": str(exc)})
            raise

    @abstractmethod
    async def _execute_task(self, prompt: str, task_id: str) -> str:
        """Role-specific execution logic — override in each agent subclass."""

    async def handoff_to(self, target_agent_id: str, task_id: str, reason: str):
        self.context.record_handoff(
            from_agent_id=self.agent_id,
            to_agent_id=target_agent_id,
            task_id=task_id,
            reason=reason,
        )
        self.context.audit_action(
            self.agent_id,
            "task_handoff",
            {"to": target_agent_id, "task_id": task_id, "reason": reason},
        )

    def requires_approval(self, action_type: str, cost_usd: float = 0.0) -> bool:
        gates = {
            "git_push": True,
            "destructive_op": True,
            "publish": True,
            "cost_threshold": cost_usd > self.cost_threshold,
        }
        return gates.get(action_type, False)

    async def request_approval(
        self,
        task_id: str,
        action_type: str,
        cost_usd: float = 0.0,
        timeout_seconds: int = 3600,
    ) -> bool:
        approval_id = self.context.request_approval(
            task_id=task_id,
            agent_id=self.agent_id,
            action_type=action_type,
            cost_usd=cost_usd,
        )
        print(f"\n[{self.agent_name}] Approval required for '{action_type}' (cost=${cost_usd:.4f})")
        print(f"  approval_id: {approval_id}")
        print(f"  Run: python -m openclaw approve {approval_id}")

        deadline = asyncio.get_event_loop().time() + timeout_seconds
        while asyncio.get_event_loop().time() < deadline:
            pending = self.context.get_pending_approvals()
            if not any(a["id"] == approval_id for a in pending):
                return True  # approved (no longer pending)
            await asyncio.sleep(5)

        return False  # timed out
