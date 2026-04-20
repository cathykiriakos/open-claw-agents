# Phase 2: PraisonAI Customization & Agent Role Design
**Duration:** 2-3 weeks  
**Priority:** Multi-agent orchestration for 4 functional roles  
**Success Criteria:** 4 agents working, handing off tasks, logging to SQLite, approval gates enforcing cost/git/publishing controls

---

## Agent Role Architecture

### Overview: Hybrid Specialization Model

You'll have **4 primary agents** + **1 optional manager agent**:

```
┌────────────────────────────────────────────────────────────┐
│                  OPEN CLAW AGENT SYSTEM                    │
├────────────────────────────────────────────────────────────┤
│                                                             │
│  Manager Agent (Optional, orchestrates all)                │
│  └─ Routes tasks to specialists                            │
│  └─ Monitors cost, logs all actions                        │
│  └─ Triggers human approvals as needed                     │
│                                                             │
│  ┌─────────────┬─────────────┬─────────────┬──────────┐  │
│  │ Researcher  │ Data Agent  │   Executor  │ Calendar │  │
│  │   Agent     │             │    Agent    │  Agent   │  │
│  ├─────────────┼─────────────┼─────────────┼──────────┤  │
│  │PRIMARY:     │PRIMARY:     │PRIMARY:     │PRIMARY:  │  │
│  │Investigate  │Synthesize   │Code/CLI     │Schedule  │  │
│  │ideas,      │findings     │execution    │tasks     │  │
│  │trends,      │across       │Create tools │Calendar  │  │
│  │opportunities│sources      │Deploy code  │mgmt      │  │
│  │             │Share        │Testing      │          │  │
│  │FLEX:        │findings     │             │FLEX:     │  │
│  │Can query    │             │FLEX:        │Can draft │  │
│  │data agents, │FLEX:        │Can research │research  │  │
│  │exec tasks   │Can exec     │Can schedule │Can exec  │  │
│  │             │tasks        │tasks        │tasks     │  │
│  └─────────────┴─────────────┴─────────────┴──────────┘  │
│                                                             │
│  Shared Layer (All agents use)                            │
│  ├─ SQLite context store (agent memory)                   │
│  ├─ Approval gate system (cost, git, publishing)          │
│  ├─ Inference router from Phase 1 (local vs. Claude)      │
│  └─ Task logger (audit trail, git history)                │
│                                                             │
└────────────────────────────────────────────────────────────┘
```

---

## Phase 2A: SQLite Context Store Design (Days 1-3)

### Database Schema

Your agents will store context, conversations, approvals, and audit logs in SQLite for instant access and git-friendly versioning.

```sql
-- File: /open-claw/data/agent_context.sql

-- ============================================================================
-- Agent Memory & Context
-- ============================================================================

CREATE TABLE agents (
    id TEXT PRIMARY KEY,  -- 'researcher', 'data', 'executor', 'calendar'
    name TEXT NOT NULL,
    role TEXT NOT NULL,   -- Primary specialization
    status TEXT,          -- 'idle', 'working', 'waiting_approval'
    last_task_id TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE agent_context (
    id TEXT PRIMARY KEY,
    agent_id TEXT NOT NULL,
    context_type TEXT,   -- 'conversation', 'memory', 'task_history'
    content TEXT,        -- JSON: {key: value} pairs
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(agent_id) REFERENCES agents(id)
);

-- Query recent context for agent:
-- SELECT content FROM agent_context 
-- WHERE agent_id = 'researcher' 
-- ORDER BY created_at DESC LIMIT 10;

-- ============================================================================
-- Task & Workflow Tracking
-- ============================================================================

CREATE TABLE tasks (
    id TEXT PRIMARY KEY,          -- UUID
    agent_id TEXT NOT NULL,
    parent_task_id TEXT,          -- If part of larger workflow
    task_type TEXT,               -- 'research', 'synthesis', 'execution', 'scheduling'
    prompt TEXT,
    status TEXT,                  -- 'pending', 'in_progress', 'waiting_approval', 'completed', 'failed'
    result TEXT,
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    FOREIGN KEY(agent_id) REFERENCES agents(id)
);

-- Query all pending tasks:
-- SELECT * FROM tasks WHERE status = 'pending' ORDER BY assigned_at;

CREATE TABLE task_dependencies (
    dependent_task_id TEXT NOT NULL,
    prerequisite_task_id TEXT NOT NULL,
    PRIMARY KEY(dependent_task_id, prerequisite_task_id),
    FOREIGN KEY(dependent_task_id) REFERENCES tasks(id),
    FOREIGN KEY(prerequisite_task_id) REFERENCES tasks(id)
);

-- ============================================================================
-- Agent Communication & Handoffs
-- ============================================================================

CREATE TABLE handoffs (
    id TEXT PRIMARY KEY,
    from_agent_id TEXT NOT NULL,
    to_agent_id TEXT NOT NULL,
    task_id TEXT NOT NULL,
    reason TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(from_agent_id) REFERENCES agents(id),
    FOREIGN KEY(to_agent_id) REFERENCES agents(id),
    FOREIGN KEY(task_id) REFERENCES tasks(id)
);

-- Get handoff history:
-- SELECT * FROM handoffs WHERE task_id = '...' ORDER BY timestamp;

-- ============================================================================
-- Approval Gate System
-- ============================================================================

CREATE TABLE approval_requests (
    id TEXT PRIMARY KEY,
    task_id TEXT NOT NULL,
    agent_id TEXT NOT NULL,
    action_type TEXT,        -- 'git_push', 'destructive_op', 'publish', 'cost_threshold'
    cost_usd REAL,
    required_approval TEXT,   -- 'human', 'none'
    status TEXT,              -- 'pending', 'approved', 'rejected', 'expired'
    human_response TEXT,
    human_responded_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(task_id) REFERENCES tasks(id),
    FOREIGN KEY(agent_id) REFERENCES agents(id)
);

-- Get pending approvals:
-- SELECT * FROM approval_requests WHERE status = 'pending' ORDER BY created_at;

-- ============================================================================
-- Cost Tracking
-- ============================================================================

CREATE TABLE inference_costs (
    id TEXT PRIMARY KEY,
    agent_id TEXT NOT NULL,
    task_id TEXT NOT NULL,
    model_used TEXT,          -- 'gemma:7b', 'claude'
    provider TEXT,            -- 'local', 'claude'
    tokens_input INTEGER,
    tokens_output INTEGER,
    cost_usd REAL,
    latency_ms REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(agent_id) REFERENCES agents(id),
    FOREIGN KEY(task_id) REFERENCES tasks(id)
);

-- Daily cost summary:
-- SELECT 
--   agent_id, 
--   COUNT(*) as inference_count,
--   SUM(cost_usd) as total_cost,
--   AVG(latency_ms) as avg_latency
-- FROM inference_costs
-- WHERE DATE(created_at) = DATE('now')
-- GROUP BY agent_id;

-- ============================================================================
-- Audit & Versioning
-- ============================================================================

CREATE TABLE audit_log (
    id TEXT PRIMARY KEY,
    agent_id TEXT,
    action TEXT,              -- 'task_created', 'approval_requested', 'git_push', 'publish'
    details TEXT,             -- JSON
    git_commit_sha TEXT,      -- If action is git-related
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(agent_id) REFERENCES agents(id)
);

-- Get audit trail for an agent:
-- SELECT * FROM audit_log WHERE agent_id = 'executor' ORDER BY timestamp DESC;

-- ============================================================================
-- Initialize agents
-- ============================================================================

INSERT INTO agents (id, name, role) VALUES
    ('researcher', 'Researcher Agent', 'research'),
    ('data', 'Data Agent', 'synthesis'),
    ('executor', 'Executor Agent', 'execution'),
    ('calendar', 'Calendar Agent', 'scheduling');
```

### Python Wrapper

```python
# File: /open-claw/agents/context_store.py

import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

class ContextStore:
    """SQLite-backed memory for all agents"""
    
    def __init__(self, db_path: str = '/open-claw/data/agent_context.db'):
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        """Create schema if it doesn't exist"""
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript(open('/open-claw/data/agent_context.sql').read())
            conn.commit()
    
    def get_agent_context(self, agent_id: str, limit: int = 10) -> List[Dict]:
        """Get recent context for an agent"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                '''
                SELECT content, created_at FROM agent_context
                WHERE agent_id = ?
                ORDER BY created_at DESC
                LIMIT ?
                ''',
                (agent_id, limit)
            ).fetchall()
            return [dict(row) for row in rows]
    
    def save_agent_context(self, agent_id: str, content: Dict, context_type: str = 'memory'):
        """Store context for an agent"""
        import uuid
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                '''
                INSERT INTO agent_context (id, agent_id, context_type, content)
                VALUES (?, ?, ?, ?)
                ''',
                (str(uuid.uuid4()), agent_id, context_type, json.dumps(content))
            )
            conn.commit()
    
    def create_task(
        self, 
        agent_id: str, 
        task_type: str, 
        prompt: str,
        parent_task_id: Optional[str] = None
    ) -> str:
        """Create a new task for an agent"""
        import uuid
        task_id = str(uuid.uuid4())
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                '''
                INSERT INTO tasks (id, agent_id, parent_task_id, task_type, prompt, status)
                VALUES (?, ?, ?, ?, ?, 'pending')
                ''',
                (task_id, agent_id, parent_task_id, task_type, prompt)
            )
            conn.commit()
        return task_id
    
    def update_task_status(self, task_id: str, status: str, result: Optional[str] = None):
        """Update task status"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                '''
                UPDATE tasks SET status = ?, result = ?, completed_at = ?
                WHERE id = ?
                ''',
                (status, result, datetime.now().isoformat() if status == 'completed' else None, task_id)
            )
            conn.commit()
    
    def get_pending_tasks(self, agent_id: Optional[str] = None) -> List[Dict]:
        """Get all pending tasks (optionally filtered by agent)"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            if agent_id:
                rows = conn.execute(
                    'SELECT * FROM tasks WHERE status = "pending" AND agent_id = ? ORDER BY assigned_at',
                    (agent_id,)
                ).fetchall()
            else:
                rows = conn.execute(
                    'SELECT * FROM tasks WHERE status = "pending" ORDER BY assigned_at'
                ).fetchall()
            return [dict(row) for row in rows]
    
    def get_pending_approvals(self) -> List[Dict]:
        """Get all pending approval requests"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                'SELECT * FROM approval_requests WHERE status = "pending" ORDER BY created_at'
            ).fetchall()
            return [dict(row) for row in rows]
    
    def request_approval(
        self, 
        task_id: str, 
        agent_id: str, 
        action_type: str,
        cost_usd: float = 0.0
    ) -> str:
        """Request human approval for an action"""
        import uuid
        approval_id = str(uuid.uuid4())
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                '''
                INSERT INTO approval_requests (id, task_id, agent_id, action_type, cost_usd, required_approval, status)
                VALUES (?, ?, ?, ?, ?, 'human', 'pending')
                ''',
                (approval_id, task_id, agent_id, action_type, cost_usd)
            )
            conn.commit()
        return approval_id
    
    def respond_to_approval(self, approval_id: str, approved: bool, response: str = ''):
        """Human approves or rejects an action"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                '''
                UPDATE approval_requests 
                SET status = ?, human_response = ?, human_responded_at = ?
                WHERE id = ?
                ''',
                ('approved' if approved else 'rejected', response, datetime.now().isoformat(), approval_id)
            )
            conn.commit()
    
    def log_inference_cost(
        self,
        agent_id: str,
        task_id: str,
        model_used: str,
        provider: str,
        tokens_input: int,
        tokens_output: int,
        cost_usd: float,
        latency_ms: float
    ):
        """Log inference cost for tracking"""
        import uuid
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                '''
                INSERT INTO inference_costs 
                (id, agent_id, task_id, model_used, provider, tokens_input, tokens_output, cost_usd, latency_ms)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''',
                (str(uuid.uuid4()), agent_id, task_id, model_used, provider, tokens_input, tokens_output, cost_usd, latency_ms)
            )
            conn.commit()
    
    def get_daily_cost_summary(self, agent_id: Optional[str] = None) -> Dict:
        """Get cost summary for today"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            if agent_id:
                row = conn.execute(
                    '''
                    SELECT 
                        COUNT(*) as inference_count,
                        SUM(cost_usd) as total_cost,
                        AVG(latency_ms) as avg_latency
                    FROM inference_costs
                    WHERE DATE(created_at) = DATE('now') AND agent_id = ?
                    ''',
                    (agent_id,)
                ).fetchone()
            else:
                row = conn.execute(
                    '''
                    SELECT 
                        COUNT(*) as inference_count,
                        SUM(cost_usd) as total_cost,
                        AVG(latency_ms) as avg_latency
                    FROM inference_costs
                    WHERE DATE(created_at) = DATE('now')
                    '''
                ).fetchone()
            
            return dict(row) if row else {}
    
    def audit_action(self, agent_id: str, action: str, details: Dict, git_commit_sha: Optional[str] = None):
        """Log an action to audit trail"""
        import uuid
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                '''
                INSERT INTO audit_log (id, agent_id, action, details, git_commit_sha)
                VALUES (?, ?, ?, ?, ?)
                ''',
                (str(uuid.uuid4()), agent_id, action, json.dumps(details), git_commit_sha)
            )
            conn.commit()
```

---

## Phase 2B: Agent Role Definitions (Days 4-7)

### Base Agent Class

```python
# File: /open-claw/agents/base_agent.py

from typing import Optional, Dict, Any
from agents.context_store import ContextStore
from agents.inference_agent import OpenClawInferenceAgent
from abc import ABC, abstractmethod

class OpenClawAgent(ABC):
    """Base class for all Open Claw agents (Researcher, Data, Executor, Calendar)"""
    
    def __init__(
        self, 
        agent_id: str,
        agent_name: str,
        primary_role: str,
        context_store: ContextStore,
        inference_agent: OpenClawInferenceAgent,
        cost_threshold_usd: float = 2.0  # Approve if inference exceeds this
    ):
        self.agent_id = agent_id
        self.agent_name = agent_name
        self.primary_role = primary_role
        self.context = context_store
        self.inference = inference_agent
        self.cost_threshold = cost_threshold_usd
        self.current_task_id: Optional[str] = None
    
    async def process_task(self, prompt: str, task_type: str = 'default') -> str:
        """Execute a task with approval gates + cost tracking"""
        
        # 1. Create task record
        task_id = self.context.create_task(
            agent_id=self.agent_id,
            task_type=task_type,
            prompt=prompt
        )
        self.current_task_id = task_id
        
        # 2. Execute task
        try:
            result = await self._execute_task(prompt, task_id)
            
            # 3. Update task status
            self.context.update_task_status(task_id, 'completed', result)
            
            return result
        
        except Exception as e:
            self.context.update_task_status(task_id, 'failed', str(e))
            raise
    
    async def _execute_task(self, prompt: str, task_id: str) -> str:
        """Subclasses override this with role-specific logic"""
        
        # Default: use inference router
        response = await self.inference.infer(
            prompt=prompt,
            task_type='complex',  # Default to Claude-quality
            validate_quality=False
        )
        
        # Log the inference
        # (This would need the response object from inference, so we'd refactor)
        
        return response
    
    async def handoff_to_agent(
        self, 
        target_agent_id: str, 
        task_id: str,
        reason: str
    ):
        """Hand off task to another agent"""
        
        with self.context.db_connection() as conn:
            conn.execute(
                '''
                INSERT INTO handoffs (id, from_agent_id, to_agent_id, task_id, reason)
                VALUES (?, ?, ?, ?, ?)
                ''',
                (uuid.uuid4(), self.agent_id, target_agent_id, task_id, reason)
            )
        
        # Log audit trail
        self.context.audit_action(
            self.agent_id,
            'task_handoff',
            {'target': target_agent_id, 'reason': reason}
        )
    
    def check_approval_required(self, action_type: str, cost_usd: float = 0.0) -> bool:
        """Determine if action requires human approval"""
        
        # Approval gates: cost, git, publishing
        approval_gates = {
            'git_push': True,           # Always require approval
            'destructive_op': True,     # rm, delete, clear
            'publish': True,            # Social media, email
            'cost_threshold': cost_usd > self.cost_threshold  # If > budget
        }
        
        return approval_gates.get(action_type, False)
    
    async def request_approval_and_wait(
        self, 
        task_id: str,
        action_type: str,
        cost_usd: float = 0.0,
        timeout_seconds: int = 3600
    ) -> bool:
        """Request human approval and wait for response"""
        
        import asyncio
        import time
        
        approval_id = self.context.request_approval(
            task_id=task_id,
            agent_id=self.agent_id,
            action_type=action_type,
            cost_usd=cost_usd
        )
        
        # Poll for approval (would be better with webhooks/signals)
        start_time = time.time()
        while time.time() - start_time < timeout_seconds:
            approval = self.context.get_approval(approval_id)
            if approval['status'] != 'pending':
                return approval['status'] == 'approved'
            await asyncio.sleep(5)  # Check every 5 seconds
        
        return False  # Timeout = rejection
```

### Specific Agent Implementations

#### 1. Researcher Agent

```python
# File: /open-claw/agents/researcher_agent.py

from agents.base_agent import OpenClawAgent
import json

class ResearcherAgent(OpenClawAgent):
    """
    Specializes in investigating trends, opportunities, entrepreneurial ideas.
    Uses last30days-skill to gather sources.
    
    PRIMARY: Research
    FLEX: Can execute searches, query data agent
    """
    
    def __init__(self, context_store, inference_agent, **kwargs):
        super().__init__(
            agent_id='researcher',
            agent_name='Researcher Agent',
            primary_role='research',
            context_store=context_store,
            inference_agent=inference_agent,
            **kwargs
        )
        self.tools = {
            'search': self._search_tool,
            'synthesize': self._synthesize_tool,
            'handoff_to_data': self._handoff_to_data,
            'handoff_to_executor': self._handoff_to_executor
        }
    
    async def _execute_task(self, prompt: str, task_id: str) -> str:
        """Research-specific execution"""
        
        # 1. Determine if this is a research task or needs flexing
        is_pure_research = any(kw in prompt.lower() for kw in [
            'research', 'investigate', 'trend', 'opportunity', 'idea', 'analysis'
        ])
        
        if not is_pure_research:
            # Flex: might be a data synthesis task → handoff
            if 'synthesize' in prompt.lower() or 'summarize' in prompt.lower():
                await self.handoff_to_agent('data', task_id, 'Task requires synthesis expertise')
                # Return handoff confirmation
                return f"Handed off task {task_id} to Data Agent for synthesis"
            
            # Flex: might be execution → handoff
            if 'execute' in prompt.lower() or 'deploy' in prompt.lower():
                await self.handoff_to_agent('executor', task_id, 'Task requires execution')
                return f"Handed off task {task_id} to Executor Agent"
        
        # 2. Execute research using inference
        result = await self.inference.infer(
            prompt=prompt,
            task_type='complex',  # Research is complex
            validate_quality=True  # Validate against gold standard
        )
        
        # 3. Store in context
        self.context.save_agent_context(
            self.agent_id,
            {
                'task_id': task_id,
                'prompt': prompt,
                'result': result,
                'role': 'researcher'
            },
            context_type='research_finding'
        )
        
        return result
    
    async def _search_tool(self, query: str) -> str:
        """Search for information (would integrate with last30days-skill)"""
        return f"Searching for: {query}"
    
    async def _synthesize_tool(self, findings: list) -> str:
        """Synthesize research findings"""
        prompt = f"Synthesize these findings: {json.dumps(findings)}"
        return await self.inference.infer(prompt, task_type='complex')
    
    async def _handoff_to_data(self, task_id: str):
        """Handoff to Data Agent for synthesis"""
        await self.handoff_to_agent('data', task_id, 'Requires data synthesis')
    
    async def _handoff_to_executor(self, task_id: str):
        """Handoff to Executor Agent"""
        await self.handoff_to_agent('executor', task_id, 'Requires execution')
```

#### 2. Data Agent

```python
# File: /open-claw/agents/data_agent.py

class DataAgent(OpenClawAgent):
    """
    Synthesizes findings across sources (Reddit, X, YouTube, HN).
    Aggregates insights. Publishes summaries.
    
    PRIMARY: Data synthesis
    FLEX: Can research, can publish
    """
    
    def __init__(self, context_store, inference_agent, **kwargs):
        super().__init__(
            agent_id='data',
            agent_name='Data Agent',
            primary_role='synthesis',
            context_store=context_store,
            inference_agent=inference_agent,
            **kwargs
        )
    
    async def _execute_task(self, prompt: str, task_id: str) -> str:
        """Synthesis-specific execution"""
        
        # Check if task involves publishing (requires approval)
        if 'publish' in prompt.lower() or 'post' in prompt.lower() or 'share' in prompt.lower():
            
            # Synthesize first
            synthesis_result = await self.inference.infer(
                prompt=prompt,
                task_type='complex'
            )
            
            # Request approval before publishing
            approval_needed = await self.request_approval_and_wait(
                task_id=task_id,
                action_type='publish',
                cost_usd=0.0  # Publishing is free
            )
            
            if not approval_needed:
                return "Publishing rejected by human"
            
            # Publish (if approved)
            await self._publish(synthesis_result)
            
            return f"Published: {synthesis_result[:100]}..."
        
        # Regular synthesis (no approval needed)
        result = await self.inference.infer(prompt, task_type='complex')
        return result
    
    async def _publish(self, content: str):
        """Publish content (Twitter, Slack, etc.)"""
        # Would integrate with Agent-Reach
        self.context.audit_action(
            self.agent_id,
            'publish',
            {'content_preview': content[:100]}
        )
```

#### 3. Executor Agent

```python
# File: /open-claw/agents/executor_agent.py

class ExecutorAgent(OpenClawAgent):
    """
    Executes code, runs CLI commands, deploys, tests.
    Uses agent-skills for safe execution.
    
    PRIMARY: Code execution
    FLEX: Can research, can schedule
    
    REQUIRES APPROVAL: git push, rm, destructive operations
    """
    
    def __init__(self, context_store, inference_agent, **kwargs):
        super().__init__(
            agent_id='executor',
            agent_name='Executor Agent',
            primary_role='execution',
            context_store=context_store,
            inference_agent=inference_agent,
            **kwargs
        )
    
    async def _execute_task(self, prompt: str, task_id: str) -> str:
        """Execution-specific logic with approval gates"""
        
        # Determine if task is destructive or involves git
        is_destructive = any(op in prompt.lower() for op in ['rm ', 'delete', 'remove', 'clear', 'drop'])
        is_git_operation = any(op in prompt.lower() for op in ['git push', 'git commit', 'git merge'])
        
        if is_destructive or is_git_operation:
            # Request approval
            approval_type = 'git_push' if is_git_operation else 'destructive_op'
            
            approval_granted = await self.request_approval_and_wait(
                task_id=task_id,
                action_type=approval_type
            )
            
            if not approval_granted:
                return f"Action rejected: {approval_type}"
        
        # Execute
        result = await self.inference.infer(
            prompt=prompt,
            task_type='complex'
        )
        
        # Audit log
        self.context.audit_action(
            self.agent_id,
            'code_execution',
            {'prompt': prompt, 'result': result[:100]}
        )
        
        return result
```

#### 4. Calendar Agent

```python
# File: /open-claw/agents/calendar_agent.py

class CalendarAgent(OpenClawAgent):
    """
    Manages personal + work calendar, tasks, scheduling.
    
    PRIMARY: Calendar management
    FLEX: Can research, can execute
    """
    
    def __init__(self, context_store, inference_agent, **kwargs):
        super().__init__(
            agent_id='calendar',
            agent_name='Calendar Agent',
            primary_role='scheduling',
            context_store=context_store,
            inference_agent=inference_agent,
            **kwargs
        )
    
    async def _execute_task(self, prompt: str, task_id: str) -> str:
        """Calendar-specific execution"""
        
        # Parse task type
        task_types = {
            'schedule': 'create_event',
            'block': 'create_block',
            'task': 'create_task',
            'reminder': 'set_reminder'
        }
        
        detected_type = next(
            (v for k, v in task_types.items() if k in prompt.lower()),
            'generic'
        )
        
        # Execute
        result = await self.inference.infer(
            prompt=prompt,
            task_type='simple'  # Calendar ops are straightforward
        )
        
        return result
```

---

## Phase 2C: Agent Orchestration & Manager (Optional) (Days 8-10)

### Manager Agent (Optional Coordinator)

```python
# File: /open-claw/agents/manager_agent.py

class ManagerAgent(OpenClawAgent):
    """
    Optional coordinator that oversees all agents.
    Routes complex tasks to specialists.
    Monitors costs and approvals.
    
    This is optional—you can run without it if agents are independent enough.
    """
    
    def __init__(self, context_store, inference_agent, worker_agents: Dict):
        super().__init__(
            agent_id='manager',
            agent_name='Manager Agent',
            primary_role='orchestration',
            context_store=context_store,
            inference_agent=inference_agent
        )
        self.workers = worker_agents  # {'researcher': agent, 'data': agent, ...}
    
    async def delegate_task(self, prompt: str) -> str:
        """
        Analyze task and delegate to appropriate specialist(s)
        """
        
        # Classify task
        classification_prompt = f"""
        Analyze this task and classify it:
        - researcher (investigation, trends, opportunities)
        - data (synthesis, aggregation, analysis)
        - executor (code, CLI, deployment)
        - calendar (scheduling, time management)
        - multi (requires multiple agents)
        
        Task: {prompt}
        
        Respond ONLY with the classification.
        """
        
        classification = await self.inference.infer(classification_prompt, task_type='simple')
        
        if classification.lower() == 'multi':
            # Complex workflow: orchestrate multiple agents
            result = await self._orchestrate_multi_agent_workflow(prompt)
        else:
            # Delegate to specialist
            agent = self.workers.get(classification.lower())
            if agent:
                result = await agent.process_task(prompt)
            else:
                result = "Could not classify task"
        
        return result
    
    async def _orchestrate_multi_agent_workflow(self, prompt: str) -> str:
        """Handle multi-agent workflows"""
        # Example: research → synthesize → execute
        # Would decompose prompt into sub-tasks and coordinate
        pass
```

---

## Phase 2 Deliverables

✅ **SQLite Context Store** — Persistent memory for all agents (context, tasks, approvals, costs, audit log)  
✅ **4 Agent Role Implementations** — Researcher, Data, Executor, Calendar (hybrid specialization)  
✅ **Approval Gate System** — Cost, git, publishing gates enforced  
✅ **Cost Tracking** — Daily summaries by agent  
✅ **Audit Trail** — All agent actions logged  
✅ **Optional Manager Agent** — For task routing/orchestration (optional)  

---

## Phase 2 Success Metrics

- ✅ Agents can create tasks, update status, track context
- ✅ Approval gates block git/publish/expensive ops
- ✅ Cost tracking shows daily spend per agent
- ✅ Agents can handoff to each other
- ✅ Audit log captures all actions
- ✅ SQLite database backing up cleanly to git

---

## Next: Phase 3 Clarification

Ready to move to **Phase 3: gitagent Manifest Design**?

I'll need to clarify:
1. **Manifest format** — Should each agent's config be a single YAML file or modular?
2. **Versioning strategy** — How do you version agent behavior? (git tags? branches?)
3. **Agent composition** — Can agents be composed from base + overrides? (DRY principle)
4. **Distribution** — Do you want to share agent definitions across projects?

Proceed to Phase 3?
