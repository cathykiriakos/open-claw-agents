"""__main__.py — Open Claw CLI.

Usage:
    python -m openclaw research "local AI inference tools"
    python -m openclaw data "synthesise recent AI findings"
    python -m openclaw execute "list all python files"
    python -m openclaw calendar "block 2 hours tomorrow for deep work"
    python -m openclaw pipeline "research AI trends then synthesise"
    python -m openclaw pipeline "research AI trends" --publish
    python -m openclaw approve <approval_id>
    python -m openclaw status
    python -m openclaw history [--agent researcher]
"""

from __future__ import annotations

import argparse
import asyncio
import sys

sys.path.insert(0, ".")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="python -m openclaw",
        description="Open Claw — local AI agent system",
    )
    sub = p.add_subparsers(dest="command", required=True)

    # --- research ---
    r = sub.add_parser("research", help="Run the Researcher Agent")
    r.add_argument("topic", nargs="+", help="Research topic")

    # --- data ---
    d = sub.add_parser("data", help="Run the Data Agent (synthesis)")
    d.add_argument("task", nargs="+", help="Synthesis task")
    d.add_argument("--publish", action="store_true", help="Publish result to Slack + file")

    # --- execute ---
    e = sub.add_parser("execute", help="Run the Executor Agent")
    e.add_argument("task", nargs="+", help="Execution task")

    # --- calendar ---
    c = sub.add_parser("calendar", help="Run the Calendar Agent")
    c.add_argument("task", nargs="+", help="Scheduling task")

    # --- pipeline ---
    pl = sub.add_parser("pipeline", help="Run a multi-agent pipeline")
    pl.add_argument("task", nargs="+", help="Pipeline task or topic")
    pl.add_argument("--publish", action="store_true", help="Publish final output")

    # --- approve ---
    ap = sub.add_parser("approve", help="Approve a pending action")
    ap.add_argument("approval_id", help="Approval ID shown in the agent output")
    ap.add_argument("--reject", action="store_true", help="Reject instead of approve")
    ap.add_argument("--note", default="", help="Optional note")

    # --- status ---
    sub.add_parser("status", help="Show pending tasks and approvals")

    # --- history ---
    hist = sub.add_parser("history", help="Show recent audit log")
    hist.add_argument("--agent", default=None, help="Filter by agent ID")
    hist.add_argument("--limit", type=int, default=20)

    return p


async def cmd_research(args):
    from agents.context_store import ContextStore
    from agents.inference_agent import OpenClawInferenceAgent
    from agents.researcher import ResearcherAgent
    import config

    store = ContextStore()
    agent = ResearcherAgent(store, OpenClawInferenceAgent("researcher", config.OLLAMA_URL))
    topic = " ".join(args.topic)
    print(f"[openclaw] Researching: {topic}\n")
    result = await agent.research(topic)
    print(result)


async def cmd_data(args):
    from agents.context_store import ContextStore
    from agents.inference_agent import OpenClawInferenceAgent
    from agents.data import DataAgent
    import config

    store = ContextStore()
    agent = DataAgent(store, OpenClawInferenceAgent("data", config.OLLAMA_URL))
    task = " ".join(args.task)

    if args.publish:
        task_id = store.create_task("data", "synthesis", task)
        result = await agent._execute_task(task + " and publish", task_id)
    else:
        result = await agent.synthesise_findings([task], topic=task)

    print(result)


async def cmd_execute(args):
    from agents.context_store import ContextStore
    from agents.inference_agent import OpenClawInferenceAgent
    from agents.executor import ExecutorAgent
    import config

    store = ContextStore()
    agent = ExecutorAgent(store, OpenClawInferenceAgent("executor", config.OLLAMA_URL))
    task = " ".join(args.task)
    task_id = store.create_task("executor", "execution", task)
    print(f"[openclaw] Executing: {task}\n")
    result = await agent._execute_task(task, task_id)
    print(result)


async def cmd_calendar(args):
    from agents.context_store import ContextStore
    from agents.inference_agent import OpenClawInferenceAgent
    from agents.calendar import CalendarAgent
    import config

    store = ContextStore()
    agent = CalendarAgent(store, OpenClawInferenceAgent("calendar", config.OLLAMA_URL))
    task = " ".join(args.task)
    print(f"[openclaw] Calendar: {task}\n")
    result = await agent.process_task(task, task_type="scheduling")
    print(result)


async def cmd_pipeline(args):
    from pipeline import Pipeline

    p = Pipeline()
    task = " ".join(args.task)
    print(f"[openclaw] Pipeline: {task}\n")

    if args.publish:
        result = await p.run(task + " and publish")
    else:
        result = await p.run(task)

    print(f"\n{'─'*50}")
    print(result.final_output)
    print(f"\n{result.summary()}")


def cmd_approve(args):
    from agents.context_store import ContextStore

    store = ContextStore()
    store.respond_to_approval(
        approval_id=args.approval_id,
        approved=not args.reject,
        response=args.note,
    )
    action = "REJECTED" if args.reject else "APPROVED"
    print(f"[openclaw] {action}: {args.approval_id}")


def cmd_status(args):
    from agents.context_store import ContextStore

    store = ContextStore()

    pending_approvals = store.get_pending_approvals()
    pending_tasks = store.get_pending_tasks()
    cost = store.get_daily_cost_summary()

    print("\n=== Open Claw Status ===\n")

    print(f"Pending approvals: {len(pending_approvals)}")
    for a in pending_approvals:
        print(f"  [{a['id'][:8]}] {a['agent_id']} — {a['action_type']}")
        print(f"    approve: python -m openclaw approve {a['id']}")

    print(f"\nPending tasks: {len(pending_tasks)}")
    for t in pending_tasks[:10]:
        print(f"  [{t['id'][:8]}] {t['agent_id']} — {t['prompt'][:60]}")

    print(f"\nToday's inference: {cost.get('inference_count', 0)} calls, ${cost.get('total_cost') or 0:.4f}")
    print()


def cmd_history(args):
    from agents.context_store import ContextStore

    store = ContextStore()
    logs = store.get_audit_log(args.agent or "researcher", limit=args.limit) if args.agent else []

    if not args.agent:
        # Show all agents
        import sqlite3
        with sqlite3.connect(store.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM audit_log ORDER BY timestamp DESC LIMIT ?", (args.limit,)
            ).fetchall()
        logs = [dict(r) for r in rows]

    print(f"\n=== Audit Log ({len(logs)} entries) ===\n")
    for entry in logs:
        print(f"  {entry.get('timestamp','')[:19]}  [{entry.get('agent_id','')}]  {entry.get('action','')}")


def main():
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "approve":
        cmd_approve(args)
    elif args.command == "status":
        cmd_status(args)
    elif args.command == "history":
        cmd_history(args)
    else:
        handlers = {
            "research": cmd_research,
            "data": cmd_data,
            "execute": cmd_execute,
            "calendar": cmd_calendar,
            "pipeline": cmd_pipeline,
        }
        asyncio.run(handlers[args.command](args))


if __name__ == "__main__":
    main()
