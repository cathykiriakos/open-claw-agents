# Phase 3: gitagent Manifest Design & Agent Versioning
**Duration:** 1-2 weeks  
**Priority:** Define repeatable, versionable agent specifications  
**Success Criteria:** 4 agent manifests + base template, stored in git with branch-based versioning

---

## Architecture: Branch-Based Versioning + Template Composition

```
┌─────────────────────────────────────────────────────────────┐
│          OPEN CLAW AGENT REPOSITORY (Git)                  │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  main branch (PRODUCTION)                                   │
│  ├─ agents/researcher.agent.yml (v1.2.0)                  │
│  ├─ agents/data.agent.yml (v1.2.0)                        │
│  ├─ agents/executor.agent.yml (v1.2.0)                    │
│  ├─ agents/calendar.agent.yml (v1.2.0)                    │
│  ├─ templates/base-agent.yml                              │
│  ├─ tools/                                                 │
│  │  ├─ inference-tools.yml (shared)                       │
│  │  ├─ git-tools.yml (shared)                             │
│  │  └─ data-tools.yml (shared)                            │
│  └─ .tags (git tags: v1.2.0, v1.2.1, etc.)               │
│                                                              │
│  develop branch (STAGING)                                   │
│  ├─ agents/*.yml (new features being tested)              │
│  └─ (pull requests before merge to main)                   │
│                                                              │
│  feature branches (EXPERIMENTS)                             │
│  ├─ feature/add-vector-search                             │
│  ├─ feature/improve-researcher-accuracy                   │
│  └─ (experiment freely, merge if successful)               │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Phase 3A: Base Template & Shared Tools (Days 1-3)

### File Structure

```
open-claw/
├── agents/
│   ├── researcher.agent.yml
│   ├── data.agent.yml
│   ├── executor.agent.yml
│   └── calendar.agent.yml
├── templates/
│   └── base-agent.yml           # Template all agents extend
├── tools/
│   ├── inference-tools.yml       # Shared inference routing
│   ├── git-tools.yml             # Git operations
│   ├── data-tools.yml            # Data/synthesis tools
│   ├── search-tools.yml          # Search/research tools
│   └── calendar-tools.yml        # Calendar/scheduling tools
├── roles/
│   ├── researcher-role.yml       # Role definition
│   ├── data-role.yml
│   ├── executor-role.yml
│   └── calendar-role.yml
├── approval-gates.yml            # Shared approval rules
├── .gitignore
├── README.md                      # Agent documentation
└── VERSION                        # Current version (v1.0.0)
```

### Base Agent Template

```yaml
# File: templates/base-agent.yml
# All agents extend this template and override specific fields

agent:
  # Identity (overridden per agent)
  id: "{{AGENT_ID}}"              # researcher, data, executor, calendar
  name: "{{AGENT_NAME}}"
  primary_role: "{{PRIMARY_ROLE}}" # research, synthesis, execution, scheduling
  
  # Description for clarity
  description: "{{DESCRIPTION}}"
  
  # ========================================================================
  # Inference Configuration
  # ========================================================================
  
  inference:
    # Default decision logic (inherited, can be overridden)
    routing_strategy: "quality-first"  # Prefer Claude for quality
    
    models:
      local:
        provider: "ollama"
        instances:
          - model: "gemma:7b"
            name: "fast"
            purpose: "simple, fast tasks"
            latency_target_ms: 2000
          - model: "gemma:13b"
            name: "smart"
            purpose: "complex reasoning"
            latency_target_ms: 5000
      
      cloud:
        provider: "claude"
        model: "claude-opus-4-6"
        fallback: true               # Use if local fails
        cost_threshold_usd: 2.0       # Alert if exceeds this
    
    # Task classification (simple → local, complex → claude)
    task_types:
      simple:
        keywords: ["list", "retrieve", "summarize", "extract", "format"]
        router: "local"
        model: "gemma:7b"
      
      complex:
        keywords: ["analyze", "reason", "decide", "recommend"]
        router: "cloud"
        model: "claude-opus-4-6"
      
      proven:
        router: "local"               # Use cached proven tasks
        model: "gemma:13b"
        quality_threshold: 0.85       # Mark as proven if ≥85% quality
  
  # ========================================================================
  # Tools (Extended by each agent)
  # ========================================================================
  
  tools:
    # Include shared tools by reference
    inference:
      $ref: "tools/inference-tools.yml"
    
    # Role-specific tools (overridden per agent)
    role_specific: []
  
  # ========================================================================
  # Agent Memory & Context
  # ========================================================================
  
  memory:
    backend: "sqlite"               # Local, portable
    database_path: "/open-claw/data/agent_context.db"
    context_retention: "30d"         # Keep context for 30 days
    
    # What to remember (can override per agent)
    remember:
      - task_history: true           # Remember completed tasks
      - conversation_history: true   # Remember conversations
      - quality_assessments: true    # Remember quality validation results
      - cost_tracking: true          # Remember inference costs
  
  # ========================================================================
  # Approval Gates
  # ========================================================================
  
  approval_gates:
    $ref: "approval-gates.yml"      # Use shared approval rules
    # Can override specific gates per agent if needed
  
  # ========================================================================
  # Capabilities & Constraints
  # ========================================================================
  
  capabilities:
    primary_role: "{{PRIMARY_ROLE}}"
    can_research: false              # Overridden per agent
    can_synthesize: false
    can_execute: false
    can_schedule: false
    can_handoff: true                # All agents can handoff
  
  # ========================================================================
  # Configuration & Behavior
  # ========================================================================
  
  config:
    max_parallel_tasks: 1            # Only one task at a time
    task_timeout_seconds: 3600       # 1 hour timeout
    verbose_logging: false           # Set to true for debugging
    
    # Operational constraints
    cost_limit_daily_usd: 10.0       # Daily budget
    cost_limit_monthly_usd: 200.0    # Monthly budget
    
    quality_validation: false        # Validate local outputs? (expensive)
    quality_validation_frequency: "manual"  # Only validate on demand
  
  # ========================================================================
  # Integration Points
  # ========================================================================
  
  integrations:
    slack: false                     # Can post to Slack?
    twitter: false                   # Can post to Twitter?
    email: false                     # Can send emails?
    google_calendar: false           # Can access calendar?
    git: false                        # Can execute git commands?
    
    # Override per agent if needed
  
  # ========================================================================
  # Metadata
  # ========================================================================
  
  metadata:
    version: "1.0.0"                 # Manifest version
    created_at: "{{CREATED_AT}}"
    last_updated: "{{LAST_UPDATED}}"
    maintainer: "cathy"
    tags: ["openclaw", "agent"]
    stability: "production"          # production, staging, experimental
```

### Shared Inference Tools

```yaml
# File: tools/inference-tools.yml
# Shared across all agents

tools:
  inference:
    infer:
      description: "Run inference on a prompt"
      input:
        prompt: { type: "string", required: true }
        task_type: { type: "string", enum: ["simple", "complex", "proven"], default: "simple" }
        max_tokens: { type: "integer", default: 500 }
        temperature: { type: "float", default: 0.7 }
      output: { type: "string" }
      cost_estimate: "free if local, $0.01-$0.10 if Claude"
    
    validate_quality:
      description: "Compare local output to Claude (ground truth)"
      input:
        prompt: { type: "string" }
        local_output: { type: "string" }
      output: 
        quality_score: { type: "float", min: 0, max: 1 }
        comparison: { type: "string" }
      cost_estimate: "$0.05 per validation (uses Claude)"
    
    route_task:
      description: "Determine whether to use local or Claude for a task"
      input:
        prompt: { type: "string" }
        task_type: { type: "string" }
      output:
        router_decision: { type: "string", enum: ["local", "claude", "proven"] }
        reasoning: { type: "string" }
        cost_estimate: { type: "float" }
      cost_estimate: "free"
  
  cost_tracking:
    log_inference:
      description: "Log inference cost for tracking"
      input:
        model_used: { type: "string" }
        provider: { type: "string", enum: ["local", "claude"] }
        tokens_input: { type: "integer" }
        tokens_output: { type: "integer" }
        cost_usd: { type: "float" }
      cost_estimate: "free"
    
    get_cost_summary:
      description: "Get daily/monthly cost summary"
      output: { type: "object", fields: ["total_cost", "by_agent", "by_provider"] }
      cost_estimate: "free"
  
  observability:
    log_action:
      description: "Log an action to audit trail"
      input:
        action: { type: "string" }
        details: { type: "object" }
      cost_estimate: "free"
    
    get_audit_log:
      description: "Retrieve audit log for an agent"
      input:
        agent_id: { type: "string" }
        limit: { type: "integer", default: 100 }
      output: { type: "array" }
      cost_estimate: "free"
```

### Shared Approval Gates

```yaml
# File: approval-gates.yml
# Centralized approval rules (can override per agent)

approval_gates:
  # Gate 1: Cost threshold
  cost_threshold:
    enabled: true
    condition: "inference_cost_usd > cost_threshold"
    cost_threshold_default: 2.0     # Alert if single inference > $2
    action: "require_human_approval"
    timeout_seconds: 3600           # Wait 1 hour for approval
    severity: "warning"
  
  # Gate 2: Git operations
  git_operations:
    enabled: true
    operations: ["push", "commit", "merge", "force-push", "reset --hard"]
    action: "require_human_approval"
    timeout_seconds: 3600
    severity: "critical"            # Don't proceed without approval
  
  # Gate 3: Destructive operations
  destructive_operations:
    enabled: true
    operations: ["rm", "delete", "clear", "truncate", "drop"]
    action: "require_human_approval"
    timeout_seconds: 3600
    severity: "critical"
  
  # Gate 4: External publishing
  external_publishing:
    enabled: true
    channels: ["twitter", "slack", "email", "webhook"]
    action: "require_human_approval"
    timeout_seconds: 3600
    severity: "critical"

# Override examples (per agent in their YAML):
# 
# approval_gates:
#   cost_threshold:
#     cost_threshold_default: 5.0   # Researcher can spend more on research
#   
#   git_operations:
#     severity: "warning"           # Non-blocking for executor (executor does git)
```

---

## Phase 3B: Individual Agent Manifests (Days 4-7)

### 1. Researcher Agent

```yaml
# File: agents/researcher.agent.yml

agent:
  # Inherit base template
  extends: ../templates/base-agent.yml
  
  # Identity
  id: "researcher"
  name: "Researcher Agent"
  primary_role: "research"
  description: "Investigates trends, opportunities, and entrepreneurial ideas"
  
  # ========================================================================
  # Role-Specific Overrides
  # ========================================================================
  
  capabilities:
    primary_role: "research"
    can_research: true              # Specializes in research
    can_synthesize: true            # Can flex into synthesis
    can_execute: false
    can_schedule: false
  
  tools:
    # Inherit inference tools
    inference:
      $ref: "../tools/inference-tools.yml"
    
    # Role-specific research tools
    research:
      $ref: "../tools/search-tools.yml"
    
    # Flex: synthesize and execute
    synthesis:
      $ref: "../tools/data-tools.yml"
    
    handoff:
      hand_off_to_data:
        description: "Hand off research to Data Agent for synthesis"
        target_agent: "data"
        reason_template: "Task requires synthesis expertise"
      
      hand_off_to_executor:
        description: "Hand off task to Executor for code work"
        target_agent: "executor"
        reason_template: "Task requires code execution"
  
  # Override inference config (researcher can spend more on complex research)
  inference:
    models:
      cloud:
        cost_threshold_usd: 5.0      # Higher threshold for research
  
  # Override approval gates
  approval_gates:
    cost_threshold:
      cost_threshold_default: 5.0    # Researcher can spend up to $5/call
  
  # Operational config
  config:
    cost_limit_daily_usd: 20.0       # $20 daily for research
    cost_limit_monthly_usd: 400.0    # $400 monthly
    verbose_logging: true           # Debug research workflows
  
  # Integrations: researcher publishes findings
  integrations:
    twitter: true                   # Post research findings
    slack: true                     # Share in Slack
  
  # Metadata
  metadata:
    version: "1.0.0"
    tags: ["openclaw", "researcher", "production"]
    stability: "production"
```

### 2. Data Agent

```yaml
# File: agents/data.agent.yml

agent:
  extends: ../templates/base-agent.yml
  
  id: "data"
  name: "Data Agent"
  primary_role: "synthesis"
  description: "Synthesizes findings across sources (Reddit, X, YouTube, HN) and publishes insights"
  
  capabilities:
    primary_role: "synthesis"
    can_research: true              # Can flex: run searches
    can_synthesize: true
    can_execute: false
    can_schedule: true              # Can flex: schedule publications
  
  tools:
    inference:
      $ref: "../tools/inference-tools.yml"
    
    synthesis:
      $ref: "../tools/data-tools.yml"
    
    research:                        # Flex: can search
      $ref: "../tools/search-tools.yml"
    
    publishing:
      publish_to_slack:
        description: "Publish synthesis to Slack"
        channel: "#ai-research"
        approval_required: true
      
      publish_to_twitter:
        description: "Post thread to Twitter"
        format: "markdown → twitter thread"
        approval_required: true
  
  # Data synthesis is straightforward, use local more
  inference:
    routing_strategy: "cost-optimized"  # Local-first for synthesis
  
  config:
    cost_limit_daily_usd: 10.0       # Lower: synthesis is local-friendly
    cost_limit_monthly_usd: 200.0
    quality_validation: true        # Validate syntheses against Claude
    quality_validation_frequency: "always"  # Every synthesis gets QA
  
  integrations:
    slack: true
    twitter: true
    email: true
  
  metadata:
    version: "1.0.0"
    tags: ["openclaw", "data", "synthesis", "production"]
    stability: "production"
```

### 3. Executor Agent

```yaml
# File: agents/executor.agent.yml

agent:
  extends: ../templates/base-agent.yml
  
  id: "executor"
  name: "Executor Agent"
  primary_role: "execution"
  description: "Executes code, runs CLI commands, manages deployments"
  
  capabilities:
    primary_role: "execution"
    can_research: false
    can_synthesize: false
    can_execute: true
    can_schedule: false
  
  tools:
    inference:
      $ref: "../tools/inference-tools.yml"
    
    execution:
      $ref: "../tools/git-tools.yml"
    
    code_tools:
      bash:
        description: "Execute bash commands (sandboxed)"
        approval_required_for: ["destructive", "system-wide"]
      
      git:
        description: "Execute git commands"
        approval_required_for: ["push", "reset --hard", "force-push"]
      
      docker:
        description: "Manage Docker containers"
        approval_required_for: ["stop", "rm", "prune"]
  
  # Executor uses complex reasoning often (pay for quality)
  inference:
    models:
      cloud:
        cost_threshold_usd: 1.0      # Lower threshold: executor is cost-sensitive
  
  # Override approval gates: executor does git, so make it "warning" not "critical"
  approval_gates:
    git_operations:
      enabled: true
      severity: "warning"           # Non-blocking (executor does this a lot)
      timeout_seconds: 600          # Shorter timeout for frequent ops
    
    destructive_operations:
      enabled: true
      severity: "critical"          # Block dangerous ops
  
  config:
    cost_limit_daily_usd: 15.0
    cost_limit_monthly_usd: 300.0
    task_timeout_seconds: 1800      # 30 min timeout for long-running tasks
  
  metadata:
    version: "1.0.0"
    tags: ["openclaw", "executor", "production"]
    stability: "production"
```

### 4. Calendar Agent

```yaml
# File: agents/calendar.agent.yml

agent:
  extends: ../templates/base-agent.yml
  
  id: "calendar"
  name: "Calendar Agent"
  primary_role: "scheduling"
  description: "Manages personal and work calendar, tasks, and time blocks"
  
  capabilities:
    primary_role: "scheduling"
    can_research: true              # Can flex: research before scheduling
    can_synthesize: false
    can_execute: true              # Can flex: execute time-bound tasks
    can_schedule: true
  
  tools:
    inference:
      $ref: "../tools/inference-tools.yml"
    
    scheduling:
      $ref: "../tools/calendar-tools.yml"
    
    calendar_integrations:
      google_calendar:
        description: "Read/write to Google Calendar"
        scopes: ["calendar.events", "calendar.settings"]
      
      notion:
        description: "Sync calendar to Notion"
      
      create_event:
        description: "Create calendar event"
        approval_required: false    # No approval needed for calendar ops
      
      block_time:
        description: "Block time for focused work"
        approval_required: false
      
      create_task:
        description: "Create a task in task management"
        approval_required: false
  
  # Calendar ops are simple, use local heavily
  inference:
    routing_strategy: "cost-optimized"  # Local-first
    models:
      simple:
        keywords: ["create", "schedule", "block", "remind"]
        router: "local"
        model: "gemma:7b"
  
  config:
    cost_limit_daily_usd: 5.0        # Very low: mostly local
    cost_limit_monthly_usd: 100.0
  
  integrations:
    google_calendar: true
    email: true
    slack: true
  
  metadata:
    version: "1.0.0"
    tags: ["openclaw", "calendar", "scheduler", "production"]
    stability: "production"
```

---

## Phase 3C: Git Workflow & Versioning (Days 8-10)

### Repository Setup

```bash
# Initialize git repo
mkdir -p ~/open-claw-agents
cd ~/open-claw-agents
git init

# Create branch structure
git checkout -b develop
git push -u origin develop

# Create main (will merge to after testing)
git checkout -b main

# .gitignore
cat > .gitignore << 'EOF'
*.pyc
__pycache__/
.DS_Store
*.log
data/
.env
EOF

git add .gitignore
git commit -m "Initial commit: .gitignore"
```

### Git Workflow: How to Use This

```bash
# ========================================================================
# PRODUCTION AGENTS (main branch)
# ========================================================================

# View production agents
git checkout main
cat agents/researcher.agent.yml

# Deploy a tested version to production
git tag v1.0.0
git push origin main --tags

# ========================================================================
# STAGING & DEVELOPMENT (develop branch)
# ========================================================================

# Create a feature branch to experiment
git checkout develop
git pull origin develop
git checkout -b feature/add-vector-search

# Make changes to agent manifests
# e.g., edit agents/researcher.agent.yml to add vector search capability

# Test changes locally (would run agents with new config)
# ...testing...

# Create PR back to develop
git add agents/researcher.agent.yml
git commit -m "feat: add vector search to researcher agent

- Adds semantic search tool to research workflow
- Improves finding discovery for entrepreneurship research
- Tested locally on 10 sample queries
"

git push origin feature/add-vector-search

# On GitHub/GitLab: create PR to develop
# Review your own changes
# If good: merge to develop
# If needs work: iterate

# Once develop is stable, merge to main
git checkout main
git pull origin develop
git merge develop

# Tag the release
git tag v1.0.1
git push origin main --tags

# ========================================================================
# ROLLBACK: If something breaks
# ========================================================================

# Revert to previous version
git checkout v1.0.0  # or git tag -l to list versions

# Revert a commit
git revert <commit-sha>

# Reset to previous version (destructive, use carefully)
git reset --hard v1.0.0
```

### Manifest Versioning in Code

```python
# File: /open-claw/agents/loader.py
# Load agent manifests from git with version tracking

import yaml
import subprocess
from typing import Dict

class AgentManifestLoader:
    def __init__(self, repo_path: str = '/open-claw-agents'):
        self.repo_path = repo_path
    
    def load_agent(self, agent_id: str) -> Dict:
        """Load agent manifest with git metadata"""
        
        manifest_path = f"{self.repo_path}/agents/{agent_id}.agent.yml"
        
        with open(manifest_path, 'r') as f:
            manifest = yaml.safe_load(f)
        
        # Get git metadata
        git_info = self._get_git_info(manifest_path)
        manifest['_git'] = git_info
        
        return manifest
    
    def _get_git_info(self, file_path: str) -> Dict:
        """Get git version info for a file"""
        try:
            # Get last commit SHA
            sha = subprocess.check_output(
                ['git', 'rev-parse', 'HEAD'],
                cwd=self.repo_path,
                text=True
            ).strip()
            
            # Get last commit message
            message = subprocess.check_output(
                ['git', 'log', '-1', '--pretty=%B', file_path],
                cwd=self.repo_path,
                text=True
            ).strip()
            
            # Get current tag
            try:
                tag = subprocess.check_output(
                    ['git', 'describe', '--tags', '--exact-match'],
                    cwd=self.repo_path,
                    text=True
                ).strip()
            except:
                tag = 'untagged'
            
            return {
                'commit_sha': sha,
                'last_change': message,
                'tag': tag,
                'timestamp': subprocess.check_output(
                    ['git', 'log', '-1', '--format=%ai', file_path],
                    cwd=self.repo_path,
                    text=True
                ).strip()
            }
        except Exception as e:
            return {'error': str(e)}

# Usage:
loader = AgentManifestLoader()
researcher_manifest = loader.load_agent('researcher')
print(f"Running researcher agent from commit {researcher_manifest['_git']['commit_sha']}")
print(f"Last change: {researcher_manifest['_git']['last_change']}")
```

---

## Phase 3 Deliverables

✅ **Base Agent Template** — All agents extend this, reducing duplication  
✅ **Shared Tools & Approval Gates** — Centralized, referenced across agents  
✅ **4 Agent Manifests** — Researcher, Data, Executor, Calendar (YAML)  
✅ **Branch-Based Versioning** — main = prod, develop = staging, features for experiments  
✅ **Git Integration** — Load manifests with version tracking  
✅ **Manifest Loader** — Python code to load and version agents  

---

## Phase 3 Success Metrics

- ✅ All agent configs in git
- ✅ No duplication (shared tools + base template)
- ✅ Easy to experiment (feature branches)
- ✅ Easy to rollback (git tags)
- ✅ Version tracked in code (agents know their git commit/tag)
- ✅ Can spawn new agents from template without code duplication

---

## Next: Phase 4 - Implementation Sprint Planning

Ready to create a **detailed 4-week sprint plan** that sequences all of this work?

I'll map out:
1. **Week-by-week tasks** (what you're building each week)
2. **Daily standup format** (how to track progress)
3. **Milestones** (working agents by end of week, etc.)
4. **Integration points** (when Phase 1 → Phase 2 → Phase 3 connect)
5. **Testing checkpoints** (how to validate each phase works)

Proceed to Phase 4?
