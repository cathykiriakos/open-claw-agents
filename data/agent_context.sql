-- data/agent_context.sql
-- SQLite schema for Open Claw agent memory, tasks, approvals, costs, and audit log

-- ============================================================================
-- Agent Registry
-- ============================================================================

CREATE TABLE IF NOT EXISTS agents (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    role TEXT NOT NULL,
    status TEXT DEFAULT 'idle',
    last_task_id TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- Agent Memory & Context
-- ============================================================================

CREATE TABLE IF NOT EXISTS agent_context (
    id TEXT PRIMARY KEY,
    agent_id TEXT NOT NULL,
    context_type TEXT,
    content TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(agent_id) REFERENCES agents(id)
);

-- ============================================================================
-- Task & Workflow Tracking
-- ============================================================================

CREATE TABLE IF NOT EXISTS tasks (
    id TEXT PRIMARY KEY,
    agent_id TEXT NOT NULL,
    parent_task_id TEXT,
    task_type TEXT,
    prompt TEXT,
    status TEXT DEFAULT 'pending',
    result TEXT,
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    FOREIGN KEY(agent_id) REFERENCES agents(id)
);

CREATE TABLE IF NOT EXISTS task_dependencies (
    dependent_task_id TEXT NOT NULL,
    prerequisite_task_id TEXT NOT NULL,
    PRIMARY KEY(dependent_task_id, prerequisite_task_id),
    FOREIGN KEY(dependent_task_id) REFERENCES tasks(id),
    FOREIGN KEY(prerequisite_task_id) REFERENCES tasks(id)
);

-- ============================================================================
-- Agent Handoffs
-- ============================================================================

CREATE TABLE IF NOT EXISTS handoffs (
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

-- ============================================================================
-- Approval Gate System
-- ============================================================================

CREATE TABLE IF NOT EXISTS approval_requests (
    id TEXT PRIMARY KEY,
    task_id TEXT NOT NULL,
    agent_id TEXT NOT NULL,
    action_type TEXT,
    cost_usd REAL DEFAULT 0.0,
    required_approval TEXT DEFAULT 'human',
    status TEXT DEFAULT 'pending',
    human_response TEXT,
    human_responded_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(task_id) REFERENCES tasks(id),
    FOREIGN KEY(agent_id) REFERENCES agents(id)
);

-- ============================================================================
-- Cost Tracking
-- ============================================================================

CREATE TABLE IF NOT EXISTS inference_costs (
    id TEXT PRIMARY KEY,
    agent_id TEXT NOT NULL,
    task_id TEXT NOT NULL,
    model_used TEXT,
    provider TEXT,
    tokens_input INTEGER DEFAULT 0,
    tokens_output INTEGER DEFAULT 0,
    cost_usd REAL DEFAULT 0.0,
    latency_ms REAL DEFAULT 0.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(agent_id) REFERENCES agents(id),
    FOREIGN KEY(task_id) REFERENCES tasks(id)
);

-- ============================================================================
-- Audit Log
-- ============================================================================

CREATE TABLE IF NOT EXISTS audit_log (
    id TEXT PRIMARY KEY,
    agent_id TEXT,
    action TEXT,
    details TEXT,
    git_commit_sha TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(agent_id) REFERENCES agents(id)
);

-- ============================================================================
-- Seed: register the four agents
-- ============================================================================

INSERT OR IGNORE INTO agents (id, name, role) VALUES
    ('researcher', 'Researcher Agent', 'research'),
    ('data',       'Data Agent',       'synthesis'),
    ('executor',   'Executor Agent',   'execution'),
    ('calendar',   'Calendar Agent',   'scheduling');
