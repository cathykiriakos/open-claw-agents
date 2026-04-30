"""agents/data.py — Data Agent implementation."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

import config
from agents.base_agent import OpenClawAgent
from tools_lib.publish import PublishTools


class DataAgent(OpenClawAgent):
    """
    Synthesises findings across sources and publishes insights.

    PRIMARY:  Synthesis — combine research findings into structured reports
    FLEX:     Can run searches; can schedule publications via CalendarAgent
    APPROVAL: Any publish action requires human sign-off
    """

    def __init__(self, context_store, inference_agent):
        super().__init__(
            agent_id="data",
            agent_name="Data Agent",
            primary_role="synthesis",
            context_store=context_store,
            inference_agent=inference_agent,
        )
        self.publisher = PublishTools(slack_webhook_url=config.SLACK_WEBHOOK_URL)
        Path("data/syntheses").mkdir(parents=True, exist_ok=True)

    async def _execute_task(self, prompt: str, task_id: str) -> str:
        wants_publish = any(
            kw in prompt.lower() for kw in ["publish", "post", "share", "send to slack"]
        )

        synthesis = await self._synthesise(prompt, task_id)

        if wants_publish:
            approved = await self.request_approval(task_id, "publish")
            if not approved:
                return f"[data] Synthesis complete — publishing rejected.\n\n{synthesis}"
            await self.publisher.publish(synthesis, title=f"Research Synthesis — {datetime.now().strftime('%Y-%m-%d')}")
            self.context.audit_action(self.agent_id, "published", {"preview": synthesis[:120]})
            return f"[data] Published.\n\n{synthesis}"

        self._save_synthesis(task_id, synthesis)
        return synthesis

    # ------------------------------------------------------------------
    # Core synthesis flow
    # ------------------------------------------------------------------

    async def _synthesise(self, prompt: str, task_id: str) -> str:
        # Pull Researcher's recent findings to enrich synthesis
        recent_context = self.context.get_agent_context("researcher", limit=5)
        findings_block = ""
        if recent_context:
            snippets = []
            for r in recent_context:
                try:
                    data = json.loads(r.get("content", "{}"))
                    if data.get("finding"):
                        snippets.append(data["finding"][:600])
                except (json.JSONDecodeError, AttributeError):
                    pass
            if snippets:
                findings_block = "\n\nContext from recent Researcher findings:\n" + "\n---\n".join(snippets[:3])

        synth_prompt = (
            f"You are a data synthesis specialist.\n\n"
            f"Task: {prompt}"
            f"{findings_block}\n\n"
            f"Produce a structured synthesis:\n"
            f"- Executive summary (2-3 sentences)\n"
            f"- Key themes (bullet points)\n"
            f"- Actionable insights\n"
            f"- Confidence level: high / medium / low"
        )
        response = await self.inference.infer(prompt=synth_prompt, task_type="complex")
        return response.content

    def _save_synthesis(self, task_id: str, content: str):
        filename = (
            Path("data/syntheses")
            / f"{task_id[:8]}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        )
        filename.write_text(f"# Synthesis\n\n{content}\n")
        self.context.audit_action(self.agent_id, "synthesis_saved", {"file": str(filename)})

    # ------------------------------------------------------------------
    # Direct synthesis methods
    # ------------------------------------------------------------------

    async def synthesise_findings(self, findings: list[str], topic: str) -> str:
        """Synthesise a list of text findings on a topic."""
        joined = "\n\n---\n\n".join(findings)
        prompt = (
            f"Synthesise these findings about '{topic}' into a single coherent report:\n\n{joined}"
        )
        response = await self.inference.infer(prompt=prompt, task_type="complex")
        return response.content

    async def publish(self, content: str, title: str = "Open Claw Report") -> dict:
        """Publish directly (bypasses approval gate — use for programmatic calls)."""
        return await self.publisher.publish(content, title=title)

    def list_saved_syntheses(self) -> list[str]:
        return sorted(str(p) for p in Path("data/syntheses").glob("*.md"))
