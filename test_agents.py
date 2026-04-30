"""test_agents.py — Smoke-test all agents, pipeline, and manifest loader.

Run from repo root with Ollama running:
    python test_agents.py
"""

import asyncio
import sys

sys.path.insert(0, ".")

import config
from agents.context_store import ContextStore
from agents.inference_agent import OpenClawInferenceAgent
from agents.researcher import ResearcherAgent
from agents.data import DataAgent
from agents.executor import ExecutorAgent
from agents.calendar import CalendarAgent
from pipeline import Pipeline
from manifest_loader import ManifestLoader


def make_store_and_agents():
    store = ContextStore("data/agent_context.db")
    url = config.OLLAMA_URL
    return (
        store,
        ResearcherAgent(store, OpenClawInferenceAgent("researcher", url)),
        DataAgent(store,       OpenClawInferenceAgent("data",       url)),
        ExecutorAgent(store,   OpenClawInferenceAgent("executor",   url), working_dir="."),
        CalendarAgent(store,   OpenClawInferenceAgent("calendar",   url)),
    )


async def test_researcher(agent: ResearcherAgent):
    print("\n── Researcher ──────────────────────────────")
    result = await agent.research("local AI inference tools 2025")
    print(result[:400])
    print("✓ researcher done")


async def test_data(agent: DataAgent):
    print("\n── Data Agent ──────────────────────────────")
    result = await agent.synthesise_findings(
        findings=[
            "Ollama makes running local LLMs simple on consumer hardware.",
            "Gemma 7B achieves near-GPT-3.5 quality on many tasks.",
            "Local inference costs $0 per token vs cloud APIs.",
        ],
        topic="local AI inference economics",
    )
    print(result[:400])
    print("✓ data done")


async def test_executor(agent: ExecutorAgent):
    print("\n── Executor ────────────────────────────────")
    explanation, output = await agent.explain_and_run(
        "list the Python files in the current directory", task_id=None
    )
    print(f"Plan   : {explanation}")
    print(f"Output : {output[:200]}")
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


async def test_pipeline():
    print("\n── Pipeline ────────────────────────────────")
    p = Pipeline()
    result = await p.research_and_synthesise("open source AI frameworks 2025")
    print(result.final_output[:300])
    print(result.summary())
    print("✓ pipeline done")


def test_manifest_loader():
    print("\n── Manifest Loader ─────────────────────────")
    loader = ManifestLoader()
    loader.print_summary()
    print("✓ manifest loader done")


async def main():
    print("=== Open Claw Agent Test ===")
    print(f"Ollama URL: {config.OLLAMA_URL}")

    _, researcher, data, executor, calendar = make_store_and_agents()

    # Verify Ollama is reachable
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
    await test_pipeline()
    test_manifest_loader()

    print("\n=== All tests passed ===")
    print("\nCLI examples to try on your Mac Studio:")
    print("  python -m openclaw research 'open source LLM tools 2025'")
    print("  python -m openclaw pipeline 'research local AI trends then synthesise'")
    print("  python -m openclaw calendar 'block 2 hours tomorrow morning for deep work'")
    print("  python -m openclaw status")


if __name__ == "__main__":
    asyncio.run(main())
