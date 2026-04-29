# Open Claw Agents

Multi-agent system running on Mac Studio. Four specialised agents (Researcher, Data, Executor, Calendar) with local-first inference via Ollama, Claude API fallback, SQLite memory, and human approval gates.

## Architecture

```
Request → Inference Router
           ├─ Simple tasks  → Gemma 7B  (local, free)
           ├─ Complex tasks → Claude API (quality-first)
           └─ Proven tasks  → Gemma 13B (cached, free)
                ↓
        4 Agent Roles (YAML manifests + Python classes)
           ├─ Researcher  — trends, opportunities, web research
           ├─ Data        — synthesis, publishing (Slack/Twitter)
           ├─ Executor    — code, CLI, git operations
           └─ Calendar    — scheduling, time blocks, reminders
                ↓
        SQLite (memory, tasks, costs, audit log)
        Approval Gates (cost / git / destructive / publish)
```

## Quick Start (Mac Studio)

```bash
# 1. Install Ollama + pull models + set up Python venv
bash setup_mac.sh

# 2. Set your Anthropic API key
echo "ANTHROPIC_API_KEY=sk-ant-..." > .env

# 3. Activate venv
source .venv/bin/activate

# 4. Verify the inference router
python - <<'EOF'
import asyncio, os
from inference.router import InferenceRouter, InferenceRequest

async def test():
    router = InferenceRouter(os.environ["ANTHROPIC_API_KEY"])
    req = InferenceRequest(task_id="test-1", prompt="List 3 cities in France.", task_type="simple")
    resp = await router.infer(req)
    print(f"Model : {resp.model_used}")
    print(f"Cost  : ${resp.cost_usd:.4f}")
    print(f"Output: {resp.content[:120]}")

asyncio.run(test())
EOF
```

## Repository Structure

```
open-claw-agents/
├── agents/
│   ├── researcher.agent.yml   # Researcher manifest
│   ├── data.agent.yml         # Data Agent manifest
│   ├── executor.agent.yml     # Executor manifest
│   ├── calendar.agent.yml     # Calendar manifest
│   ├── base_agent.py          # Abstract base class
│   ├── context_store.py       # SQLite memory layer
│   └── inference_agent.py     # Inference wrapper
├── inference/
│   └── router.py              # Quality-first routing logic
├── templates/
│   └── base-agent.yml         # YAML template all agents extend
├── tools/
│   ├── inference-tools.yml
│   ├── git-tools.yml
│   ├── data-tools.yml
│   ├── search-tools.yml
│   └── calendar-tools.yml
├── data/
│   └── agent_context.sql      # SQLite schema
├── approval-gates.yml          # Centralised approval rules
├── requirements.txt
├── setup_mac.sh               # One-shot Mac Studio setup
└── VERSION
```

## Approval Gates

Actions that require human confirmation before proceeding:

| Gate | Trigger | Severity |
|------|---------|----------|
| `cost_threshold` | Single inference > $2 | Warning |
| `git_operations` | commit / push / merge | Critical |
| `destructive_operations` | rm / delete / drop | Critical |
| `external_publishing` | Slack / Twitter / email | Critical |

## Git Workflow

```
main     — production agents (tagged releases)
develop  — staging / testing
feature/* — experiments (merge to develop when ready)
```

## Phase Docs

Full implementation details live in the `PHASE_*.md` files:

- `PHASE_1_CLAUDE_CODE_LOCAL.md` — inference router
- `PHASE_2_PRAISONAI_CUSTOMIZATION.md` — agent roles + SQLite
- `PHASE_3_GITAGENT_MANIFESTS.md` — YAML manifests + git workflow
- `PHASE_4_IMPLEMENTATION_SPRINT.md` — 4-week sprint plan
