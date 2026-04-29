"""agents/inference_agent.py — Inference wrapper used by all Open Claw agents."""

from __future__ import annotations

import uuid
from typing import Optional

from inference.router import (
    InferenceRequest,
    InferenceResponse,
    InferenceRouter,
    QualityValidator,
)


class OpenClawInferenceAgent:
    """Thin wrapper around InferenceRouter that each agent role uses."""

    def __init__(self, claude_api_key: str, agent_role: str = "executor"):
        self.router = InferenceRouter(claude_api_key)
        self.validator = QualityValidator(claude_api_key)
        self.agent_role = agent_role

    async def infer(
        self,
        prompt: str,
        task_type: str = "simple",
        validate_quality: bool = False,
    ) -> InferenceResponse:
        request = InferenceRequest(
            task_id=f"{self.agent_role}-{uuid.uuid4()}",
            prompt=prompt,
            task_type=task_type,
            agent_role=self.agent_role,
        )

        response = await self.router.infer(request)

        if validate_quality and response.provider == "local":
            score = await self.validator.validate(prompt, response.content)
            response.quality_score = score
            if score >= 0.85:
                self.router.proven_cache.mark_proven(prompt, task_type, score)

        return response
