"""agents/context_store.py — SQLite-backed memory for all Open Claw agents."""

from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


SCHEMA_PATH = Path(__file__).parent.parent / "data" / "agent_context.sql"


class ContextStore:
    def __init__(self, db_path: str = "data/agent_context.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        schema = SCHEMA_PATH.read_text()
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript(schema)
            conn.commit()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    # -------------------------------------------------------------------------
    # Agent Context
    # -------------------------------------------------------------------------

    def get_agent_context(self, agent_id: str, limit: int = 10) -> List[Dict]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT content, created_at FROM agent_context "
                "WHERE agent_id = ? ORDER BY created_at DESC LIMIT ?",
                (agent_id, limit),
            ).fetchall()
        return [dict(r) for r in rows]

    def save_agent_context(
        self, agent_id: str, content: Dict, context_type: str = "memory"
    ):
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO agent_context (id, agent_id, context_type, content) "
                "VALUES (?, ?, ?, ?)",
                (str(uuid.uuid4()), agent_id, context_type, json.dumps(content)),
            )
            conn.commit()

    # -------------------------------------------------------------------------
    # Task Management
    # -------------------------------------------------------------------------

    def create_task(
        self,
        agent_id: str,
        task_type: str,
        prompt: str,
        parent_task_id: Optional[str] = None,
    ) -> str:
        task_id = str(uuid.uuid4())
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO tasks (id, agent_id, parent_task_id, task_type, prompt, status) "
                "VALUES (?, ?, ?, ?, ?, 'pending')",
                (task_id, agent_id, parent_task_id, task_type, prompt),
            )
            conn.commit()
        return task_id

    def update_task_status(
        self, task_id: str, status: str, result: Optional[str] = None
    ):
        completed_at = datetime.now().isoformat() if status == "completed" else None
        with self._connect() as conn:
            conn.execute(
                "UPDATE tasks SET status = ?, result = ?, completed_at = ? WHERE id = ?",
                (status, result, completed_at, task_id),
            )
            conn.commit()

    def get_pending_tasks(self, agent_id: Optional[str] = None) -> List[Dict]:
        with self._connect() as conn:
            if agent_id:
                rows = conn.execute(
                    "SELECT * FROM tasks WHERE status = 'pending' AND agent_id = ? "
                    "ORDER BY assigned_at",
                    (agent_id,),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM tasks WHERE status = 'pending' ORDER BY assigned_at"
                ).fetchall()
        return [dict(r) for r in rows]

    # -------------------------------------------------------------------------
    # Approval Gates
    # -------------------------------------------------------------------------

    def request_approval(
        self,
        task_id: str,
        agent_id: str,
        action_type: str,
        cost_usd: float = 0.0,
    ) -> str:
        approval_id = str(uuid.uuid4())
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO approval_requests "
                "(id, task_id, agent_id, action_type, cost_usd, required_approval, status) "
                "VALUES (?, ?, ?, ?, ?, 'human', 'pending')",
                (approval_id, task_id, agent_id, action_type, cost_usd),
            )
            conn.commit()
        return approval_id

    def respond_to_approval(
        self, approval_id: str, approved: bool, response: str = ""
    ):
        with self._connect() as conn:
            conn.execute(
                "UPDATE approval_requests "
                "SET status = ?, human_response = ?, human_responded_at = ? "
                "WHERE id = ?",
                (
                    "approved" if approved else "rejected",
                    response,
                    datetime.now().isoformat(),
                    approval_id,
                ),
            )
            conn.commit()

    def get_pending_approvals(self) -> List[Dict]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM approval_requests WHERE status = 'pending' "
                "ORDER BY created_at"
            ).fetchall()
        return [dict(r) for r in rows]

    # -------------------------------------------------------------------------
    # Cost Tracking
    # -------------------------------------------------------------------------

    def log_inference_cost(
        self,
        agent_id: str,
        task_id: str,
        model_used: str,
        provider: str,
        tokens_input: int,
        tokens_output: int,
        cost_usd: float,
        latency_ms: float,
    ):
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO inference_costs "
                "(id, agent_id, task_id, model_used, provider, "
                "tokens_input, tokens_output, cost_usd, latency_ms) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    str(uuid.uuid4()),
                    agent_id,
                    task_id,
                    model_used,
                    provider,
                    tokens_input,
                    tokens_output,
                    cost_usd,
                    latency_ms,
                ),
            )
            conn.commit()

    def get_daily_cost_summary(self, agent_id: Optional[str] = None) -> Dict:
        with self._connect() as conn:
            if agent_id:
                row = conn.execute(
                    "SELECT COUNT(*) as inference_count, "
                    "SUM(cost_usd) as total_cost, AVG(latency_ms) as avg_latency "
                    "FROM inference_costs "
                    "WHERE DATE(created_at) = DATE('now') AND agent_id = ?",
                    (agent_id,),
                ).fetchone()
            else:
                row = conn.execute(
                    "SELECT COUNT(*) as inference_count, "
                    "SUM(cost_usd) as total_cost, AVG(latency_ms) as avg_latency "
                    "FROM inference_costs WHERE DATE(created_at) = DATE('now')"
                ).fetchone()
        return dict(row) if row else {}

    # -------------------------------------------------------------------------
    # Audit Log
    # -------------------------------------------------------------------------

    def audit_action(
        self,
        agent_id: str,
        action: str,
        details: Dict,
        git_commit_sha: Optional[str] = None,
    ):
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO audit_log (id, agent_id, action, details, git_commit_sha) "
                "VALUES (?, ?, ?, ?, ?)",
                (
                    str(uuid.uuid4()),
                    agent_id,
                    action,
                    json.dumps(details),
                    git_commit_sha,
                ),
            )
            conn.commit()

    def get_audit_log(self, agent_id: str, limit: int = 100) -> List[Dict]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM audit_log WHERE agent_id = ? "
                "ORDER BY timestamp DESC LIMIT ?",
                (agent_id, limit),
            ).fetchall()
        return [dict(r) for r in rows]

    # -------------------------------------------------------------------------
    # Handoffs
    # -------------------------------------------------------------------------

    def record_handoff(
        self, from_agent_id: str, to_agent_id: str, task_id: str, reason: str
    ):
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO handoffs (id, from_agent_id, to_agent_id, task_id, reason) "
                "VALUES (?, ?, ?, ?, ?)",
                (str(uuid.uuid4()), from_agent_id, to_agent_id, task_id, reason),
            )
            conn.commit()
