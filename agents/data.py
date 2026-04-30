"""agents/data.py — Data Agent implementation."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from agents.base_agent import OpenClawAgent


class DataAgent(OpenClawAgent):
    """
    Synthesises findings across sources and publishes insights.

    PRIMARY:  Synthesis — combine research findings into structured reports
    FLEX:     Can run searches; can schedule publications via CalendarAgent
    APPROVAL: Any publish action requires human sign-off
    """

    OUTPUT_DIR = Path("data/syntheses")

    def __init__(self, context_store, inference_agent):
        super().__init__(
            agent_id="data",
            agent_name="Data Agent",
            primary_role="synthesis",
            context_store=context_store,
            inference_agent=inference_agent,
        )
        self.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    async def _execute_task(self, prompt: str, task_id: str) -> str:
        prompt_lower = prompt.lower()

        wants_publish = any(kw in prompt_lower for kw in ["publish", "post", "share", "send"])

        # Synthesise first regardless
        synthesis = await self._synthesise(prompt, task_id)

        if wants_publish:
            approved = await self.request_approval(task_id, "publish")
            if not approved:
                return f"[data] Synthesis complete but publishing rejected by human.\n\n{synthesis}"
            self._save_synthesis(task_id, synthesis)
            self.context.audit_action(self.agent_id, "published", {"task_id": task_id, "preview": synthesis[:120]})
            return f"[data] Synthesis published.\n\n{synthesis}"

        self._save_synthesis(task_id, synthesis)
        return synthesis

    # ------------------------------------------------------------------
    # Tools
    # ------------------------------------------------------------------

    async def _synthesise(self, prompt: str, task_id: str) -> str:
        """Run synthesis inference with a structured prompt."""
        # Pull recent context from Researcher Agent to enrich synthesis
        recent = self.context.get_agent_context("researcher", limit=5)
        context_block = ""
        if recent:
            findings = [json.loads(r["content"]).get("finding", "") for r in recent if r.get("content")]
            if findings:
                context_block = "\n\nContext from recent research:\n" + "\n---\n".join(findings[:3])

        synth_prompt = (
            f"You are a data synthesis specialist.\n\n"
            f"Task: {prompt}"
            f"{context_block}\n\n"
            f"Produce a concise, structured synthesis with:\n"
            f"- Executive summary (2-3 sentences)\n"
            f"- Key themes (bullet points)\n"
            f"- Actionable insights\n"
            f"- Confidence level (high/medium/low)"
        )
        response = await self.inference.infer(prompt=synth_prompt, task_type="complex")
        return response.content

    def _save_synthesis(self, task_id: str, content: str):
        """Persist synthesis to disk as markdown."""
        filename = self.OUTPUT_DIR / f"{task_id[:8]}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        filename.write_text(f"# Synthesis\n\n{content}\n")
        self.context.audit_action(self.agent_id, "synthesis_saved", {"file": str(filename)})

    async def synthesise_findings(self, findings: list[str], topic: str) -> str:
        """Directly synthesise a list of text findings on a topic."""
        joined = "\n\n---\n\n".join(findings)
        prompt = (
            f"Synthesise these findings about '{topic}' into a single coherent report:\n\n{joined}"
        )
        response = await self.inference.infer(prompt=prompt, task_type="complex")
        return response.content

    def list_saved_syntheses(self) -> list[str]:
        """List all saved synthesis files."""
        return sorted(str(p) for p in self.OUTPUT_DIR.glob("*.md"))
