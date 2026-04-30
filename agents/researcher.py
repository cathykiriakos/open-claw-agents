"""agents/researcher.py — Researcher Agent implementation."""

from __future__ import annotations

import json
from typing import Optional

import config
from agents.base_agent import OpenClawAgent
from tools_lib.search import SearchTools, SearchResult


class ResearcherAgent(OpenClawAgent):
    """
    Investigates trends, opportunities, and entrepreneurial ideas.

    PRIMARY:  Research — queries HN, Reddit, YouTube, DuckDuckGo; synthesises via Gemma
    FLEX:     Light synthesis; hands off heavy synthesis to DataAgent
              Hands off code work to ExecutorAgent
    """

    def __init__(self, context_store, inference_agent):
        super().__init__(
            agent_id="researcher",
            agent_name="Researcher Agent",
            primary_role="research",
            context_store=context_store,
            inference_agent=inference_agent,
        )
        self.search = SearchTools(youtube_api_key=config.YOUTUBE_API_KEY)

    async def _execute_task(self, prompt: str, task_id: str) -> str:
        prompt_lower = prompt.lower()

        # Flex: heavy synthesis/publishing → hand off to Data Agent
        if any(kw in prompt_lower for kw in ["synthesize", "publish", "post to slack", "post to twitter"]):
            await self.handoff_to("data", task_id, "Task requires synthesis/publishing expertise")
            return f"[researcher] Handed off task {task_id} to Data Agent."

        # Flex: code/deployment → hand off to Executor
        if any(kw in prompt_lower for kw in ["execute", "deploy", "git push", "run script"]):
            await self.handoff_to("executor", task_id, "Task requires code execution")
            return f"[researcher] Handed off task {task_id} to Executor Agent."

        # Primary: search + synthesise
        return await self.research(prompt, task_id)

    # ------------------------------------------------------------------
    # Core research flow
    # ------------------------------------------------------------------

    async def research(self, topic: str, task_id: Optional[str] = None) -> str:
        """Search all sources, then synthesise findings via Gemma."""
        print(f"[researcher] Searching: {topic}")
        results = await self.search.search_all(topic, limit_per_source=6)

        if results:
            sources_block = self.search.format_for_prompt(results)
            synthesis_prompt = (
                f"You are a research analyst specialising in entrepreneurship and technology.\n\n"
                f"Topic: {topic}\n\n"
                f"Search results from HN, Reddit, and web:\n{sources_block}\n\n"
                f"Provide a structured analysis:\n"
                f"1. Key findings (3-5 bullet points)\n"
                f"2. Emerging trends\n"
                f"3. Opportunities and risks\n"
                f"4. Recommended next steps\n\n"
                f"Be concise and factual."
            )
        else:
            print("[researcher] No search results — running inference from training knowledge.")
            synthesis_prompt = (
                f"You are a research analyst. Research this topic from your knowledge:\n\n"
                f"Topic: {topic}\n\n"
                f"Provide: key findings, trends, opportunities/risks, next steps."
            )

        response = await self.inference.infer(prompt=synthesis_prompt, task_type="complex")
        content = response.content

        if task_id:
            self.context.save_agent_context(
                self.agent_id,
                {
                    "task_id": task_id,
                    "query": topic,
                    "sources_found": len(results),
                    "finding": content,
                },
                context_type="research_finding",
            )

        return content

    # ------------------------------------------------------------------
    # Targeted source methods (callable directly)
    # ------------------------------------------------------------------

    async def search_hackernews(self, query: str, limit: int = 10) -> list[SearchResult]:
        return await self.search.search_hackernews(query, limit)

    async def search_reddit(self, query: str, subreddit: str = "all", limit: int = 10) -> list[SearchResult]:
        return await self.search.search_reddit(query, subreddit=subreddit, limit=limit)

    async def search_youtube(self, query: str, limit: int = 10) -> list[SearchResult]:
        if not config.YOUTUBE_API_KEY:
            print("[researcher] YouTube search requires YOUTUBE_API_KEY in .env")
            return []
        return await self.search.search_youtube(query, limit)

    def get_recent_findings(self, limit: int = 5) -> list[dict]:
        return self.context.get_agent_context(self.agent_id, limit=limit)
