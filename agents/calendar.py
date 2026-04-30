"""agents/calendar.py — Calendar Agent implementation."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from agents.base_agent import OpenClawAgent


class CalendarAgent(OpenClawAgent):
    """
    Manages scheduling, time blocks, tasks, and reminders.

    PRIMARY:  Scheduling — create events, block focus time, manage tasks
    FLEX:     Can research before scheduling; can hand off to ExecutorAgent
    STORAGE:  Uses SQLite (same DB as agent context) for local task/reminder store
    """

    def __init__(self, context_store, inference_agent):
        super().__init__(
            agent_id="calendar",
            agent_name="Calendar Agent",
            primary_role="scheduling",
            context_store=context_store,
            inference_agent=inference_agent,
        )
        self._init_calendar_tables()

    def _init_calendar_tables(self):
        """Create calendar-specific tables if they don't exist."""
        with sqlite3.connect(self.context.db_path) as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS cal_events (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    start_dt TEXT NOT NULL,
                    end_dt TEXT NOT NULL,
                    description TEXT,
                    event_type TEXT DEFAULT 'event',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS cal_tasks (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    due_date TEXT,
                    priority TEXT DEFAULT 'medium',
                    status TEXT DEFAULT 'pending',
                    tags TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS cal_reminders (
                    id TEXT PRIMARY KEY,
                    message TEXT NOT NULL,
                    remind_at TEXT NOT NULL,
                    channel TEXT DEFAULT 'notification',
                    fired INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            conn.commit()

    async def _execute_task(self, prompt: str, task_id: str) -> str:
        prompt_lower = prompt.lower()

        # Route to the right tool based on intent
        if any(kw in prompt_lower for kw in ["remind", "reminder"]):
            return await self._handle_reminder_request(prompt, task_id)

        if any(kw in prompt_lower for kw in ["task", "todo", "to-do"]):
            return await self._handle_task_request(prompt, task_id)

        if any(kw in prompt_lower for kw in ["block", "focus", "deep work"]):
            return await self._handle_time_block(prompt, task_id)

        if any(kw in prompt_lower for kw in ["schedule", "meeting", "event", "calendar"]):
            return await self._handle_event_request(prompt, task_id)

        # Generic: use Gemma to parse intent and respond
        response = await self.inference.infer(
            prompt=(
                f"You are a calendar assistant. Help with this scheduling request: {prompt}\n\n"
                f"Today is {datetime.now().strftime('%A, %B %d %Y')}.\n"
                f"Provide a clear, actionable response."
            ),
            task_type="simple",
        )
        return response.content

    # ------------------------------------------------------------------
    # Tools
    # ------------------------------------------------------------------

    async def _handle_event_request(self, prompt: str, task_id: str) -> str:
        """Use Gemma to parse an event request, then create it."""
        parse_prompt = (
            f"Extract event details from this request. Today is {datetime.now().strftime('%Y-%m-%d')}.\n"
            f"Request: {prompt}\n\n"
            f"Respond in JSON with keys: title, start_dt (ISO 8601), end_dt (ISO 8601), description.\n"
            f"If a field is unknown, use null."
        )
        resp = await self.inference.infer(prompt=parse_prompt, task_type="simple")

        try:
            # Extract JSON from the response
            text = resp.content
            start = text.find("{")
            end = text.rfind("}") + 1
            details = json.loads(text[start:end]) if start != -1 else {}
        except (json.JSONDecodeError, ValueError):
            details = {}

        if details.get("title") and details.get("start_dt"):
            event_id = self.create_event(
                title=details["title"],
                start_dt=details["start_dt"],
                end_dt=details.get("end_dt") or details["start_dt"],
                description=details.get("description") or "",
            )
            self.context.audit_action(self.agent_id, "event_created", {"event_id": event_id, "title": details["title"]})
            return f"[calendar] Event created: '{details['title']}' on {details['start_dt']}"

        return f"[calendar] Could not parse event details. Raw response:\n{resp.content}"

    async def _handle_task_request(self, prompt: str, task_id: str) -> str:
        parse_prompt = (
            f"Extract task details from: '{prompt}'\n"
            f"Respond in JSON with keys: title, due_date (YYYY-MM-DD or null), priority (low/medium/high)."
        )
        resp = await self.inference.infer(prompt=parse_prompt, task_type="simple")
        try:
            text = resp.content
            details = json.loads(text[text.find("{"):text.rfind("}") + 1])
        except (json.JSONDecodeError, ValueError):
            details = {"title": prompt, "due_date": None, "priority": "medium"}

        task_id_cal = self.create_task(
            title=details.get("title", prompt),
            due_date=details.get("due_date"),
            priority=details.get("priority", "medium"),
        )
        return f"[calendar] Task created: '{details.get('title', prompt)}' (priority: {details.get('priority', 'medium')})"

    async def _handle_time_block(self, prompt: str, task_id: str) -> str:
        parse_prompt = (
            f"Parse this time block request. Today is {datetime.now().strftime('%Y-%m-%d')}.\n"
            f"Request: {prompt}\n"
            f"Respond in JSON: title, start_dt (ISO 8601), end_dt (ISO 8601)."
        )
        resp = await self.inference.infer(prompt=parse_prompt, task_type="simple")
        try:
            text = resp.content
            details = json.loads(text[text.find("{"):text.rfind("}") + 1])
        except (json.JSONDecodeError, ValueError):
            details = {}

        if details.get("title") and details.get("start_dt"):
            event_id = self.create_event(
                title=f"[FOCUS] {details['title']}",
                start_dt=details["start_dt"],
                end_dt=details.get("end_dt") or details["start_dt"],
                event_type="focus_block",
            )
            return f"[calendar] Focus block created: '{details['title']}' at {details['start_dt']}"

        return f"[calendar] Could not parse time block. Raw: {resp.content}"

    async def _handle_reminder_request(self, prompt: str, task_id: str) -> str:
        parse_prompt = (
            f"Parse this reminder. Today is {datetime.now().strftime('%Y-%m-%d %H:%M')}.\n"
            f"Request: {prompt}\n"
            f"Respond in JSON: message, remind_at (ISO 8601 datetime)."
        )
        resp = await self.inference.infer(prompt=parse_prompt, task_type="simple")
        try:
            text = resp.content
            details = json.loads(text[text.find("{"):text.rfind("}") + 1])
        except (json.JSONDecodeError, ValueError):
            details = {}

        if details.get("message") and details.get("remind_at"):
            reminder_id = self.set_reminder(
                message=details["message"],
                remind_at=details["remind_at"],
            )
            return f"[calendar] Reminder set: '{details['message']}' at {details['remind_at']}"

        return f"[calendar] Could not parse reminder. Raw: {resp.content}"

    # ------------------------------------------------------------------
    # Direct CRUD methods (usable without going through process_task)
    # ------------------------------------------------------------------

    def create_event(self, title: str, start_dt: str, end_dt: str,
                     description: str = "", event_type: str = "event") -> str:
        import uuid
        event_id = str(uuid.uuid4())
        with sqlite3.connect(self.context.db_path) as conn:
            conn.execute(
                "INSERT INTO cal_events (id, title, start_dt, end_dt, description, event_type) VALUES (?,?,?,?,?,?)",
                (event_id, title, start_dt, end_dt, description, event_type),
            )
            conn.commit()
        return event_id

    def create_task(self, title: str, due_date: Optional[str] = None,
                    priority: str = "medium", tags: Optional[list] = None) -> str:
        import uuid
        task_id = str(uuid.uuid4())
        with sqlite3.connect(self.context.db_path) as conn:
            conn.execute(
                "INSERT INTO cal_tasks (id, title, due_date, priority, tags) VALUES (?,?,?,?,?)",
                (task_id, title, due_date, priority, json.dumps(tags or [])),
            )
            conn.commit()
        return task_id

    def set_reminder(self, message: str, remind_at: str, channel: str = "notification") -> str:
        import uuid
        reminder_id = str(uuid.uuid4())
        with sqlite3.connect(self.context.db_path) as conn:
            conn.execute(
                "INSERT INTO cal_reminders (id, message, remind_at, channel) VALUES (?,?,?,?)",
                (reminder_id, message, remind_at, channel),
            )
            conn.commit()
        return reminder_id

    def list_upcoming_events(self, days: int = 7) -> list[dict]:
        now = datetime.now().isoformat()
        cutoff = (datetime.now() + timedelta(days=days)).isoformat()
        with sqlite3.connect(self.context.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM cal_events WHERE start_dt >= ? AND start_dt <= ? ORDER BY start_dt",
                (now, cutoff),
            ).fetchall()
        return [dict(r) for r in rows]

    def list_pending_tasks(self) -> list[dict]:
        with sqlite3.connect(self.context.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM cal_tasks WHERE status = 'pending' ORDER BY due_date, priority"
            ).fetchall()
        return [dict(r) for r in rows]

    def complete_task(self, task_id: str):
        with sqlite3.connect(self.context.db_path) as conn:
            conn.execute("UPDATE cal_tasks SET status = 'completed' WHERE id = ?", (task_id,))
            conn.commit()
