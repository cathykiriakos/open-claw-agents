"""agents/researcher.py — Researcher Agent implementation."""

from __future__ import annotations

import json
from typing import Optional

from agents.base_agent import OpenClawAgent


class ResearcherAgent(OpenClawAgent):
    """
    Investigates trends, opportunities, and entrepreneurial ideas.

    PRIMARY:  Research — web/Reddit/HN/YouTube queries synthesised via Gemma
    FLEX:     Can do light synthesis; hands off heavy synthesis to DataAgent
              Can hand off code work to ExecutorAgent
    """

    def __init__(self, context_store, inference_agent):
        super().__init__(
            agent_id="researcher",
            agent_name="Researcher Agent",
            primary_role="research",
            context_store=context_store,
            inference_agent=inference_agent,
        )

    async def _execute_task(self, prompt: str, task_id: str) -> str:
        prompt_lower = prompt.lower()

        # Flex: heavy synthesis → hand off to Data Agent
        if any(kw in prompt_lower for kw in ["synthesize", "publish", "post to slack", "post to twitter"]):
            await self.handoff_to("data", task_id, "Task requires synthesis/publishing expertise")
            return f"[researcher] Handed off task {task_id} to Data Agent for synthesis."

        # Flex: code/deployment work → hand off to Executor
        if any(kw in prompt_lower for kw in ["execute", "deploy", "git push", "run script"]):
            await self.handoff_to("executor", task_id, "Task requires code execution")
            return f"[researcher] Handed off task {task_id} to Executor Agent."

        # Primary: research — build an enriched prompt and run inference
        research_prompt = self._build_research_prompt(prompt)
        response = await self.inference.infer(prompt=research_prompt, task_type="complex")

        # Persist the finding so other agents can reference it
        self.context.save_agent_context(
            self.agent_id,
            {"task_id": task_id, "query": prompt, "finding": response.content},
            context_type="research_finding",
        )

        return response.content

    # ------------------------------------------------------------------
    # Tools
    # ------------------------------------------------------------------

    def _build_research_prompt(self, topic: str) -> str:
        """Wrap the raw topic in a structured research prompt."""
        return (
            f"You are a research analyst specialising in entrepreneurship and technology trends.\n\n"
            f"Research task: {topic}\n\n"
            f"Provide a structured analysis covering:\n"
            f"1. Key findings and current state\n"
            f"2. Emerging trends\n"
            f"3. Opportunities and risks\n"
            f"4. Recommended next steps\n\n"
            f"Be concise, factual, and actionable."
        )

    async def search_hackernews(self, query: str, limit: int = 10) -> list[dict]:
        """Query the Algolia HN API (free, no key needed)."""
        import httpx

        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                "https://hn.algolia.com/api/v1/search",
                params={"query": query, "hitsPerPage": limit, "tags": "story"},
            )
            resp.raise_for_status()
            hits = resp.json().get("hits", [])
        return [
            {"title": h.get("title"), "url": h.get("url"), "points": h.get("points", 0)}
            for h in hits
        ]

    async def research_with_hn(self, topic: str, task_id: Optional[str] = None) -> str:
        """Fetch HN stories then synthesise findings via Gemma."""
        stories = await self.search_hackernews(topic)
        stories_text = "\n".join(
            f"- {s['title']} ({s['points']} pts) — {s['url']}" for s in stories
        )
        synthesis_prompt = (
            f"Based on these recent Hacker News stories about '{topic}':\n\n"
            f"{stories_text}\n\n"
            f"Summarise the key themes, opportunities, and any risks in 3-5 bullet points."
        )
        response = await self.inference.infer(prompt=synthesis_prompt, task_type="complex")

        if task_id:
            self.context.save_agent_context(
                self.agent_id,
                {"task_id": task_id, "source": "hackernews", "query": topic, "finding": response.content},
                context_type="research_finding",
            )

        return response.content

    def get_recent_findings(self, limit: int = 5) -> list[dict]:
        """Retrieve the most recent research findings from context."""
        return self.context.get_agent_context(self.agent_id, limit=limit)
