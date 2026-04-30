"""agents/inference_agent.py — Local inference wrapper used by all Open Claw agents."""

from __future__ import annotations

import uuid

from inference.router import InferenceRequest, InferenceResponse, InferenceRouter


class OpenClawInferenceAgent:
    """Thin wrapper around InferenceRouter; all inference stays local via Ollama."""

    def __init__(self, agent_role: str = "executor", ollama_url: str = "http://localhost:11434"):
        self.router = InferenceRouter(ollama_url=ollama_url)
        self.agent_role = agent_role

    async def infer(
        self,
        prompt: str,
        task_type: str = "simple",
    ) -> InferenceResponse:
        request = InferenceRequest(
            task_id=f"{self.agent_role}-{uuid.uuid4()}",
            prompt=prompt,
            task_type=task_type,
            agent_role=self.agent_role,
        )
        return await self.router.infer(request)
