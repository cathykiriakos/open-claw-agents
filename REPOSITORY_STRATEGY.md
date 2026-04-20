# Open Claw Repository Strategy
**Date:** April 20, 2026  
**User Priority:** Local AI Agent Infrastructure  
**Deployment Flexibility:** Local-only + Local+Cloud hybrid  
**Implementation Approach:** Heavy customization for repeatable patterns  

---

## Executive Summary

You maintain **87 repositories** across AI/agent frameworks, data tools, and infrastructure. For Open Claw, **13 forks** are strategically relevant. This document prioritizes them, maps implementation details, and explains the architectural rationale.

---

## TIER 1: Foundation (Must-Have for Agent Infrastructure)

### 1. **claude-code-local** ⭐⭐⭐
**GitHub:** https://github.com/cathykiriakos/claude-code-local  
**What it is:** Runs Claude Code with local AI on Apple Silicon (122B models at inference speed without cloud costs)

**Why it matters for Open Claw:**
- Your Mac Studio M4 Max can run large models locally
- Zero cloud dependency = privacy + cost efficiency
- Native integration with Claude's agentic capabilities

**Implementation Strategy:**
```
Phase 1: Local Setup (Week 1)
├── Configure Ollama on Mac Studio
├── Download Gemma 2B / 7B / 13B (choose based on latency tolerance)
├── Integrate into claude-code-local fork
└── Benchmark inference speed & token cost

Phase 2: Customization for Open Claw (Week 2-3)
├── Create Open Claw agent wrapper that uses local inference
├── Add fallback to cloud Claude (for complex reasoning when needed)
├── Implement cost tracking (local vs. cloud decision logic)
└── Build configuration layer for switching models/providers

Phase 3: Integration (Week 4)
├── Connect to agent orchestration (see PraisonAI below)
├── Wire up to your coding agents (gitagent)
└── Test hybrid local+cloud workflows
```

**Key customization pattern:**
```python
# Reusable pattern for Open Claw
class OpenClawAgent:
    def __init__(self, model_config):
        self.local_model = model_config.get('local_model')  # Ollama
        self.cloud_fallback = model_config.get('cloud_model')  # Claude API
        self.cost_threshold = model_config.get('max_local_cost')
    
    def infer(self, prompt, complexity='auto'):
        if complexity == 'auto':
            complexity = self.estimate_complexity(prompt)
        
        if complexity in ['simple', 'moderate'] and self.local_model:
            return self.local_model.infer(prompt)  # Local, free
        else:
            return self.cloud_fallback.infer(prompt)  # Cloud, tracked
```

**Implementation Impact:**
- ✅ Enables 90%+ cost reduction on routine agentic tasks
- ✅ Keeps sensitive data local
- ✅ Basis for all other agents

---

### 2. **PraisonAI** ⭐⭐⭐
**GitHub:** https://github.com/cathykiriakos/PraisonAI  
**What it is:** Multi-agent AI automation platform; orchestrates agents with tools, memory, and hierarchical task delegation

**Why it matters for Open Claw:**
- You need a **control plane** for your 4 functional agent types (R&D, Calendar, Coding, Data)
- Handles agent-to-agent communication
- Built-in tool framework (perfect for integrating your other repos)

**Implementation Strategy:**
```
Phase 1: Agent Framework (Week 1-2)
├── Define Open Claw agent taxonomy:
│   ├── R&D Agent (researches entrepreneurial ideas)
│   ├── Data Agent (synthesizes AI/news for Booth)
│   ├── Calendar Agent (manages personal + work time)
│   └── Coding Agent (executes dev tasks)
├── Customize PraisonAI agents for each type
└── Build agent memory layer (persistent context)

Phase 2: Tool Integration (Week 3)
├── Integrate claude-code-local as backend executor
├── Connect to last30days-skill (data synthesis)
├── Add calendar APIs (Google Calendar, Notion)
├── Wire up email/chat (Slack, email for Booth communication)

Phase 3: Orchestration (Week 4)
├── Build hierarchical task decomposition (complex tasks → sub-agents)
├── Implement agent cooperation (agents delegate to each other)
├── Add human-in-the-loop checkpoints
└── Build monitoring & audit log
```

**Key customization pattern:**
```python
# Reusable PraisonAI agent for Open Claw
class OpenClawAgentRole(Agent):
    def __init__(self, role_name, tools, memory_backend):
        self.role = role_name  # 'researcher', 'executor', 'scheduler', etc.
        self.tools = tools
        self.memory = memory_backend  # Persistent context
        self.config = self.load_role_config(role_name)
    
    def configure_for_openClaw(self):
        # Each role gets consistent setup across agents
        self.add_fallback_strategy()  # Local → Cloud
        self.add_audit_logging()
        self.add_human_approval_gates()
        return self

# Then spawn multiple agents:
researcher = OpenClawAgentRole('researcher', tools=[search, analyze], memory=postgres)
executor = OpenClawAgentRole('executor', tools=[git, bash, docker], memory=postgres)
```

**Implementation Impact:**
- ✅ Central control plane for all agents
- ✅ Agent specialization without code duplication
- ✅ Audit trail for Booth oversight

---

### 3. **gitagent** ⭐⭐⭐
**GitHub:** https://github.com/cathykiriakos/gitagent  
**What it is:** Framework-agnostic, git-native standard for defining AI agents. Agents are defined as git repos with a manifest.

**Why it matters for Open Claw:**
- **Repeatable, versioned agent definitions** — your coding agents become reproducible
- **Git-native = natural audit trail** — every agent change is a commit
- **Framework-agnostic = mix local + Claude + other models**
- **Perfect for your "repeatable and configurable" goal**

**Implementation Strategy:**
```
Phase 1: Agent Manifest Standard (Week 1)
├── Define Open Claw agent manifest schema (YAML/JSON)
├── Examples:
│   ├── researcher.agent.yml (R&D agent)
│   ├── data_synthesizer.agent.yml (Booth data)
│   ├── scheduler.agent.yml (Calendar)
│   └── executor.agent.yml (Coding)
└── Store all agent definitions in git

Phase 2: Git-Native Versioning (Week 2-3)
├── Version your agents in git (main branch = production)
├── Create branches for experimental agents
├── Use git tags for stable releases
├── Implement rollback via git checkout
└── Track agent evolution in git log

Phase 3: Integration (Week 3-4)
├── Connect gitagent to PraisonAI (PraisonAI reads agent manifests)
├── Wire up CI/CD for agent validation
├── Build agent marketplace (share agents across your 4 domains)
└── Enable agent composition (combine existing agents into workflows)
```

**Key customization pattern:**
```yaml
# researcher.agent.yml (stored in git)
agent:
  name: "R&D Researcher"
  version: "1.0.0"
  purpose: "Research entrepreneurial opportunities"
  
  model:
    provider: "local"  # Ollama
    fallback_provider: "claude"  # Cloud fallback
    model_name: "gemma:13b"
  
  tools:
    - type: "search"
      config: { sources: ["arxiv", "twitter", "substack"] }
    - type: "analyze"
      config: { output_format: "markdown" }
    - type: "summarize"
      config: { max_tokens: 500 }
  
  memory:
    backend: "postgres"
    context_window: "16k"
    persistence_ttl: "30d"
  
  approval_gates:
    - type: "human_review"
      trigger: "before_publishing"
    - type: "cost_check"
      trigger: "if_exceeds_budget"
  
  output:
    format: "markdown"
    destination: "obsidian_vault"

# Commit this, track versions, enable rollback
```

**Implementation Impact:**
- ✅ Agents become first-class infrastructure (versioned, auditable, reproducible)
- ✅ Enables your "repeatable and configurable" requirement
- ✅ Easy to share/document agent designs

---

## TIER 2: Enablers (Extend Tier 1)

### 4. **Dify** ⭐⭐
**GitHub:** https://github.com/cathykiriakos/Dify  
**What it is:** Production-ready platform for agentic workflow development. UI + backend for no-code agent building.

**Why it matters:**
- Visual workflow builder (faster than code for non-technical tasks)
- Pre-built integrations (databases, APIs, webhooks)
- Complement to gitagent (Dify provides UI, gitagent provides versioning)

**Implementation Strategy:**
```
Self-host Dify on your Mac Studio as alternative to code-first agents
├── Use for quick R&D prototyping (test ideas without coding)
├── Export workflows as YAML → commit to gitagent
└── Example: "Build a data synthesis workflow in Dify UI, then version in git"
```

---

### 5. **agent-skills** ⭐⭐
**GitHub:** https://github.com/cathykiriakos/agent-skills  
**What it is:** Production-grade engineering capabilities for AI coding agents (bash, git, docker, etc.)

**Why it matters:**
- Your **Coding Agent** (in PraisonAI) needs reliable tools to execute
- Pre-built safety guardrails (e.g., sandboxing, approval gates)
- Reduces build time on your executor agent

**Implementation Strategy:**
```
Use agent-skills as the toolkit for your Coding Agent
├── Safety: All actions logged, reviewable before execution
├── Integration: Wire into PraisonAI executor role
└── Customization: Add approval gates for destructive ops (git push, rm -rf)
```

---

### 6. **rtk** ⭐⭐
**GitHub:** https://github.com/cathykiriakos/rtk  
**What it is:** CLI proxy reducing LLM token consumption by 60-90% on common dev commands.

**Why it matters:**
- Dramatically reduces cost of your local agents
- Useful for both Ollama (faster inference) and Claude API (cheaper calls)

**Implementation Strategy:**
```
Integrate rtk into your Coding Agent's bash tool
├── When agent runs 'git diff', 'ls', etc., rtk compresses output
├── Agent gets context, you save 70% tokens
└── Essential for cost optimization on local setup
```

**Implementation Impact:**
- ✅ Reduces inference cost by 60-90%
- ✅ Faster agent responses

---

## TIER 3: Data & Research (For Booth R&D)

### 7. **last30days-skill** ⭐⭐
**GitHub:** https://github.com/cathykiriakos/last30days-skill  
**What it is:** Research tool that synthesizes information across Reddit, X (Twitter), YouTube, Hacker News.

**Why it matters for Open Claw:**
- Your **Data Agent** needs sources for "AI Related Data and News"
- Covers 4 major channels (Reddit, X, YouTube, HN)
- Synthesizes across sources (not just scraping)

**Implementation Strategy:**
```
Phase 1: Skill Setup (1-2 days)
├── Configure Reddit, X, YouTube, HN credentials
├── Deploy as a PraisonAI tool for your Data Agent
└── Set up daily scheduled runs

Phase 2: Integration (2-3 days)
├── Data Agent polls last30days-skill daily
├── Synthesizes findings into Booth-ready briefing
├── Routes to Notion/Slack for consumption
└── Archives in your Obsidian vault

Phase 3: Customization (1 week)
├── Add filtering for "entrepreneurship" + "AI" topics
├── Build Booth-specific taxonomy (what topics matter?)
├── Create auto-summary (1-2 page briefing)
└── Enable manual filtering workflow (you curate findings)
```

**Implementation Pattern:**
```python
class BoothDataAgent:
    def gather_insights(self):
        sources = {
            'reddit': self.tools['last30days_reddit'](),
            'twitter': self.tools['last30days_twitter'](),
            'youtube': self.tools['last30days_youtube'](),
            'hackernews': self.tools['last30days_hn']()
        }
        
        raw_findings = [item for source in sources.values() for item in source]
        
        # Synthesize across sources
        synthesis = self.tools['analyze'](raw_findings)
        
        # Filter for Booth relevance
        booth_insights = self.filter_by_tags(['entrepreneurship', 'ai-trends', 'data'])
        
        return booth_insights  # → Publish to Notion/Slack
```

---

### 8. **Agent-Reach** ⭐
**GitHub:** https://github.com/cathykiriakos/Agent-Reach  
**What it is:** Extends agents with internet visibility across multiple platforms (Slack, Twitter, Discord, email).

**Why it matters:**
- Your agents can broadcast findings (Twitter for personal brand, Slack for team)
- Closes the loop: research → synthesis → distribution

**Implementation Strategy:**
```
Add to Booth Data Agent
├── Synthesize insights
├── Auto-post summaries to your Twitter
├── Send summaries to Slack for team visibility
└── Archive in Notion
```

---

## TIER 4: Knowledge & Tools (Nice-to-Have)

### 9. **claude-obsidian** ⭐
**GitHub:** https://github.com/cathykiriakos/claude-obsidian  
**What it is:** Claude paired with Obsidian as a persistent knowledge companion.

**Why it matters:**
- Centralizes your research findings, agent outputs, and personal knowledge
- Obsidian vault = queryable, versionable knowledge base

**Implementation Strategy:**
```
Phase 1: Vault Setup
├── Create Open Claw Obsidian vault in git
├── Structure: /research, /agents, /calendar, /archive
└── Sync to iCloud/local

Phase 2: Agent Integration
├── Data Agent → outputs summaries to /research
├── Coding Agent → documents decisions in /agents
├── Calendar Agent → logs schedule changes
└── All agents read from vault for context

Phase 3: Knowledge Synthesis
├── Use Claude in Obsidian to ask questions across vault
├── Example: "Show me all entrepreneurship insights from the last 30 days"
└── Connect to Booth briefing (vault is source of truth)
```

---

### 10. **AppFlowy** ⭐
**GitHub:** https://github.com/cathykiriakos/AppFlowy  
**What it is:** Open-source Notion alternative for organizing data, tasks, and databases.

**Why it matters:**
- Decentralized alternative to Notion (your data stays local)
- Good for **Calendar Agent** to manage tasks/events
- Self-hostable on Mac Studio

**Implementation Strategy:**
```
Optional: Use as Notion replacement for task management
├── Create database schemas for:
│   ├── Entrepreneurial projects (R&D)
│   ├── Booth research topics
│   ├── Calendar events & todos
│   └── Agent execution logs
└── Sync to git (optional) for version control
```

---

## TIER 5: Reference/Inspiration

### 11. **gstack** ⭐
**GitHub:** https://github.com/cathykiriakos/gstack  
**What it is:** Curated Claude Code setup with 23 specialized tools.

**Use:** Reference architecture; cherry-pick tool definitions for your agents.

---

### 12. **OpenBB** & **timesfm**
**Use:** Specialized for financial/time-series analysis. Useful if R&D focus includes market research.

---

## Integration Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                    OPEN CLAW ECOSYSTEM                         │
├────────────────────────────────────────────────────────────────┤
│                                                                 │
│  PraisonAI (Orchestration Layer)                              │
│  ├─ Researcher Agent (last30days + OpenBB)                    │
│  ├─ Data Agent (last30days + Agent-Reach)                     │
│  ├─ Calendar Agent (AppFlowy + APIs)                          │
│  └─ Executor Agent (agent-skills + rtk)                       │
│                                                                 │
│  ↓↓↓ (All agents use this stack)                             │
│                                                                 │
│  Local Inference Layer                                         │
│  ├─ claude-code-local (Ollama + Gemma)                        │
│  └─ Fallback: Claude API (for complex tasks)                  │
│                                                                 │
│  Versioning & Git-Native                                       │
│  ├─ gitagent (all agents as git repos)                        │
│  └─ Dify (UI builder → export to git)                         │
│                                                                 │
│  Knowledge & Output                                            │
│  ├─ Obsidian vault (research findings, agent docs)            │
│  ├─ Notion/AppFlowy (tasks, calendar)                         │
│  └─ Slack/Twitter (distribution via Agent-Reach)              │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

---

## Implementation Sequencing

**Week 1: Foundation**
- Set up claude-code-local (Ollama + Mac Studio)
- Deploy local model (Gemma 7B)
- Test inference speed & latency

**Week 2-3: Orchestration**
- Customize PraisonAI for 4 agent roles
- Implement gitagent agent manifests
- Wire up agent-skills + rtk

**Week 4: Data Layer**
- Integrate last30days-skill
- Connect to claude-obsidian vault
- Build Booth data synthesis pipeline

**Week 5+: Extensibility**
- Add Agent-Reach (distribution)
- Integrate AppFlowy (tasks)
- Build agent marketplace (share patterns)

---

## Key Customization Principles for Open Claw

**Principle 1: Repeatable Configuration**
- Every agent defined as YAML manifest (gitagent)
- Easy to spawn variations (researcher-v1, researcher-v2, etc.)
- Configuration = code (enable copy-paste cloning)

**Principle 2: Cost Optimization**
- Local-first decision logic (use Ollama for simple tasks)
- Cloud fallback for complex reasoning (use Claude API)
- Track costs, enable budget alerts

**Principle 3: Audit & Oversight**
- All agent actions logged (git commits, execution logs)
- Human-in-the-loop checkpoints for sensitive tasks
- Reproducible workflows (rerun any agent with git sha)

**Principle 4: Modular Integration**
- Agents as pluggable roles (add/remove without breaking orchestration)
- Tools as composable units (mix-and-match across agents)
- Knowledge base as source of truth (Obsidian vault queried by all)

---

## Next Steps

1. **Validate Architecture** — Does this map to your vision?
2. **Prioritize Implementation** — Start with Tier 1, then Tier 2?
3. **Detail Phase 1** — Ready to dive into claude-code-local setup?

