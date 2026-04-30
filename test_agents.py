"""test_agents.py — Smoke-test all 4 Open Claw agents against local Ollama.

Run from repo root with Ollama running:
    python test_agents.py
"""

import asyncio
import sys

sys.path.insert(0, ".")

from agents.context_store import ContextStore
from agents.inference_agent import OpenClawInferenceAgent
from agents.researcher import ResearcherAgent
from agents.data import DataAgent
from agents.executor import ExecutorAgent
from agents.calendar import CalendarAgent


def make_agents():
    store = ContextStore("data/agent_context.db")
    return (
        ResearcherAgent(store, OpenClawInferenceAgent("researcher")),
        DataAgent(store, OpenClawInferenceAgent("data")),
        ExecutorAgent(store, OpenClawInferenceAgent("executor"), working_dir="."),
        CalendarAgent(store, OpenClawInferenceAgent("calendar")),
    )


async def test_researcher(agent: ResearcherAgent):
    print("\n── Researcher ──────────────────────────────")
    result = await agent.process_task(
        "Research the current landscape of local AI inference tools in 2025",
        task_type="research",
    )
    print(result[:400])
    print("✓ researcher done")


async def test_data(agent: DataAgent):
    print("\n── Data Agent ──────────────────────────────")
    result = await agent.synthesise_findings(
        findings=[
            "Ollama makes running local LLMs simple on consumer hardware.",
            "Gemma 7B achieves near-GPT-3.5 quality on many tasks.",
            "Local inference costs $0 per token vs $0.002 for cloud APIs.",
        ],
        topic="local AI inference economics",
    )
    print(result[:400])
    print("✓ data done")


async def test_executor(agent: ExecutorAgent):
    print("\n── Executor ────────────────────────────────")
    explanation, output = await agent.explain_and_run("list the files in the current directory", task_id=None)
    print(f"Explanation : {explanation}")
    print(f"Output      : {output[:200]}")
    print("✓ executor done")


async def test_calendar(agent: CalendarAgent):
    print("\n── Calendar ────────────────────────────────")
    result = await agent.process_task(
        "Create a task: review Open Claw agent output, due tomorrow, high priority",
        task_type="task",
    )
    print(result)
    tasks = agent.list_pending_tasks()
    print(f"Pending tasks in DB: {len(tasks)}")
    print("✓ calendar done")


async def main():
    print("=== Open Claw Agent Test ===")
    print("Connecting to Ollama at localhost:11434 ...")

    researcher, data, executor, calendar = make_agents()

    # Verify Ollama is reachable first
    models = await researcher.inference.router.available_models()
    if not models:
        print("\nERROR: No Ollama models found. Make sure Ollama is running and gemma:7b is pulled.")
        print("  ollama serve &")
        print("  ollama pull gemma:7b")
        sys.exit(1)

    print(f"Models available: {models}\n")

    await test_researcher(researcher)
    await test_data(data)
    await test_executor(executor)
    await test_calendar(calendar)

    print("\n=== All agents OK ===")


if __name__ == "__main__":
    asyncio.run(main())
