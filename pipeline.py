"""pipeline.py — Multi-agent pipeline orchestration for Open Claw.

Chains agents together so output from one becomes input to the next.

Usage:
    from pipeline import Pipeline
    p = Pipeline()
    await p.run("research AI inference trends then synthesise and publish")
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

import config
from agents.context_store import ContextStore
from agents.inference_agent import OpenClawInferenceAgent
from agents.researcher import ResearcherAgent
from agents.data import DataAgent
from agents.executor import ExecutorAgent
from agents.calendar import CalendarAgent


@dataclass
class PipelineResult:
    steps: list[dict] = field(default_factory=list)
    final_output: str = ""
    started_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: Optional[str] = None
    success: bool = False

    def add_step(self, agent: str, task: str, output: str, latency_ms: float = 0):
        self.steps.append({
            "agent": agent,
            "task": task,
            "output_preview": output[:200],
            "latency_ms": round(latency_ms, 1),
        })

    def finish(self, output: str, success: bool = True):
        self.final_output = output
        self.completed_at = datetime.now().isoformat()
        self.success = success

    def summary(self) -> str:
        lines = [f"Pipeline {'✓' if self.success else '✗'} — {len(self.steps)} steps"]
        for i, s in enumerate(self.steps, 1):
            lines.append(f"  {i}. [{s['agent']}] {s['task'][:60]} ({s['latency_ms']}ms)")
        return "\n".join(lines)


class Pipeline:
    """Orchestrates multi-agent workflows."""

    # Intent keywords → which agent handles it
    AGENT_KEYWORDS = {
        "researcher": {"research", "investigate", "trend", "find", "look up", "search", "explore"},
        "data":       {"synthesise", "synthesize", "summarise", "summarize", "publish", "report", "combine"},
        "executor":   {"execute", "run", "deploy", "commit", "push", "build", "test", "script"},
        "calendar":   {"schedule", "block", "remind", "task", "meeting", "event", "calendar"},
    }

    def __init__(self, db_path: str = "data/agent_context.db"):
        store = ContextStore(db_path)
        ollama_url = config.OLLAMA_URL

        self.researcher = ResearcherAgent(store, OpenClawInferenceAgent("researcher", ollama_url))
        self.data       = DataAgent(store,       OpenClawInferenceAgent("data",       ollama_url))
        self.executor   = ExecutorAgent(store,   OpenClawInferenceAgent("executor",   ollama_url))
        self.calendar   = CalendarAgent(store,   OpenClawInferenceAgent("calendar",   ollama_url))
        self.store      = store

    # ------------------------------------------------------------------
    # Preset pipelines
    # ------------------------------------------------------------------

    async def research_and_synthesise(self, topic: str, publish: bool = False) -> PipelineResult:
        """Researcher → Data Agent pipeline."""
        result = PipelineResult()

        # Step 1: Research
        print(f"[pipeline] Step 1: Research — '{topic}'")
        t0 = datetime.now()
        findings = await self.researcher.research(topic)
        ms = (datetime.now() - t0).total_seconds() * 1000
        result.add_step("researcher", f"research: {topic}", findings, ms)
        print(f"[pipeline] Research complete ({ms:.0f}ms)")

        # Step 2: Synthesise
        print("[pipeline] Step 2: Synthesise")
        t0 = datetime.now()
        synthesis = await self.data.synthesise_findings([findings], topic)
        ms = (datetime.now() - t0).total_seconds() * 1000
        result.add_step("data", f"synthesise: {topic}", synthesis, ms)
        print(f"[pipeline] Synthesis complete ({ms:.0f}ms)")

        # Step 3 (optional): Publish
        if publish:
            print("[pipeline] Step 3: Publish")
            pub_result = await self.data.publish(synthesis, title=f"Research: {topic}")
            result.add_step("data", "publish", str(pub_result), 0)

        result.finish(synthesis)
        print(f"\n{result.summary()}")
        return result

    async def research_and_schedule(self, topic: str, schedule_prompt: str) -> PipelineResult:
        """Research a topic then schedule follow-up work."""
        result = PipelineResult()

        t0 = datetime.now()
        findings = await self.researcher.research(topic)
        ms = (datetime.now() - t0).total_seconds() * 1000
        result.add_step("researcher", f"research: {topic}", findings, ms)

        combined_prompt = f"{schedule_prompt}\n\nContext: Research on '{topic}' just completed."
        task_id = self.store.create_task("calendar", "scheduling", combined_prompt)
        t0 = datetime.now()
        cal_result = await self.calendar._execute_task(combined_prompt, task_id)
        ms = (datetime.now() - t0).total_seconds() * 1000
        result.add_step("calendar", schedule_prompt, cal_result, ms)

        result.finish(cal_result)
        print(f"\n{result.summary()}")
        return result

    async def full_pipeline(self, topic: str, publish: bool = False) -> PipelineResult:
        """Research → Synthesise → (optionally Publish) → Schedule review."""
        result = await self.research_and_synthesise(topic, publish=publish)

        # Auto-schedule a review task
        review_task = f"Review Open Claw research report on '{topic}', high priority"
        self.calendar.create_task(title=review_task, priority="high")
        result.add_step("calendar", "create review task", review_task, 0)

        print(f"\n{result.summary()}")
        return result

    # ------------------------------------------------------------------
    # Natural language routing
    # ------------------------------------------------------------------

    async def run(self, prompt: str) -> PipelineResult:
        """Route a free-text prompt to the right preset pipeline."""
        prompt_lower = prompt.lower()

        wants_publish = any(kw in prompt_lower for kw in ["publish", "post", "share"])
        wants_research = any(kw in prompt_lower for kw in self.AGENT_KEYWORDS["researcher"])
        wants_synthesis = any(kw in prompt_lower for kw in self.AGENT_KEYWORDS["data"])
        wants_calendar = any(kw in prompt_lower for kw in self.AGENT_KEYWORDS["calendar"])
        wants_execute = any(kw in prompt_lower for kw in self.AGENT_KEYWORDS["executor"])

        # Research + synthesis combo
        if wants_research and (wants_synthesis or wants_publish):
            topic = self._extract_topic(prompt)
            return await self.research_and_synthesise(topic, publish=wants_publish)

        # Research only
        if wants_research:
            topic = self._extract_topic(prompt)
            result = PipelineResult()
            t0 = datetime.now()
            output = await self.researcher.research(topic)
            ms = (datetime.now() - t0).total_seconds() * 1000
            result.add_step("researcher", topic, output, ms)
            result.finish(output)
            return result

        # Calendar only
        if wants_calendar:
            result = PipelineResult()
            task_id = self.store.create_task("calendar", "scheduling", prompt)
            t0 = datetime.now()
            output = await self.calendar._execute_task(prompt, task_id)
            ms = (datetime.now() - t0).total_seconds() * 1000
            result.add_step("calendar", prompt, output, ms)
            result.finish(output)
            return result

        # Executor
        if wants_execute:
            result = PipelineResult()
            task_id = self.store.create_task("executor", "execution", prompt)
            t0 = datetime.now()
            output = await self.executor._execute_task(prompt, task_id)
            ms = (datetime.now() - t0).total_seconds() * 1000
            result.add_step("executor", prompt, output, ms)
            result.finish(output)
            return result

        # Default: researcher
        topic = self._extract_topic(prompt)
        return await self.run(f"research {topic}")

    def _extract_topic(self, prompt: str) -> str:
        """Strip routing keywords to get the core topic."""
        stop_words = {
            "research", "investigate", "find", "look", "up", "search",
            "synthesise", "synthesize", "summarise", "summarize",
            "publish", "post", "share", "then", "and", "also",
        }
        words = [w for w in prompt.split() if w.lower() not in stop_words]
        return " ".join(words) if words else prompt
