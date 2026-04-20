# Phase 4: 4-Week Implementation Sprint Plan
**Timeline:** 4 weeks (28 days)  
**Capacity:** 10-20 hours/week  
**Checkpoints:** Weekly Sunday reviews + extensive testing per phase  
**Success Criteria:** All 4 phases complete + agents deployed locally

---

## Overview: The Journey

```
WEEK 1: Phase 1 (claude-code-local)
  └─ Local inference working on Mac Studio
  └─ Testing: Ollama setup validated, latency benchmarked
  └─ Sunday: Review metrics, decide model selection

WEEK 2: Phase 2 (PraisonAI)
  └─ 4 agents defined + SQLite context store
  └─ Testing: SQLite schema validated, agents can create tasks
  └─ Sunday: Review agent handoff logic, approval gates

WEEK 3: Phase 3 (gitagent)
  └─ Agent manifests in git (base template + 4 agents)
  └─ Testing: Manifests load correctly, git versioning works
  └─ Sunday: Review manifest structure, plan customizations

WEEK 4: Integration & Production
  └─ All phases connected: Phase 1 → Phase 2 → Phase 3
  └─ Testing: End-to-end workflows (researcher → data → executor)
  └─ Sunday: Retrospective, production deployment readiness

SUCCESS: Local agent ecosystem running on Mac Studio
```

---

## Week 1: Phase 1 - Local Inference Setup

### Daily Breakdown

**Monday-Tuesday: Ollama Setup (5 hours)**
```
Goal: Get Ollama running with Gemma models on Mac Studio

Day 1 (Monday):
  - [ ] Install Ollama (if not already done)
  - [ ] Verify Mac Studio GPU recognition (check top during inference)
  - [ ] Pull gemma:7b model (~30-45 min)
  - [ ] Test inference: simple prompt → measure latency
  - [ ] Goal: Gemma 7B responding in < 3s per inference

Day 2 (Tuesday):
  - [ ] Pull gemma:13b model (~1 hour)
  - [ ] Compare latency: 7B vs 13B
  - [ ] Set up ~/.ollama/Modelfile for optimization
  - [ ] Create ollama-optimized variant (gemma:7b-openclaw)
  - [ ] Record baseline performance metrics

Deliverable: Both models running, latency baseline established
```

**Wednesday-Thursday: Inference Router (6 hours)**
```
Goal: Build and test the inference routing layer

Day 3 (Wednesday):
  - [ ] Create /open-claw/inference/ directory structure
  - [ ] Implement router.py (quality-first routing logic)
  - [ ] Implement InferenceMetrics class (cost tracking, latency logging)
  - [ ] Write tests: test_simple_task_routes_to_local()
  - [ ] Goal: Simple router test passing

Day 4 (Thursday):
  - [ ] Implement QualityValidator class (compare local to Claude)
  - [ ] Implement ProvenTaskCache (mark tasks as validated)
  - [ ] Write tests: test_complex_task_routes_to_claude()
  - [ ] Write integration test: end-to-end inference call
  - [ ] Goal: Router tests 100% passing

Deliverable: Inference router working, tests passing
```

**Friday-Saturday: Integration Testing (4-5 hours)**
```
Goal: Validate inference router at scale

Day 5 (Friday):
  - [ ] Manual testing: Run 10 diverse prompts through router
  - [ ] Collect metrics: token counts, latency, costs
  - [ ] Validate: Simple tasks go local, complex tasks go Claude
  - [ ] Review metrics output

Day 6 (Saturday):
  - [ ] Stress test: 20 rapid inferences
  - [ ] Check error handling: what happens if Ollama crashes?
  - [ ] Verify fallback to Claude works
  - [ ] Document any issues found

Deliverable: Router validated at scale, fallback tested
```

### Sunday Review (1 hour)

```markdown
## Week 1 Sunday Review - Phase 1 Complete ✓

**What worked:**
- Ollama setup smooth
- Router logic sound
- Latency expectations met (7B: 2-3s, 13B: 5-8s)

**Metrics established:**
- Gemma 7B: ~2000ms latency, < 300 tokens/inference
- Gemma 13B: ~6000ms latency, < 500 tokens/inference
- Local cost: $0.00
- Claude fallback: $0.01-0.05 per inference

**Next week preview:**
- Build 4 agents on top of this router
- Agent roles will use this for ALL inferences
- Need to tune router for agent-specific patterns

**Decision point:**
- Are latencies acceptable? (YES/NO)
  - If NO: explore quantized models (Q4, Q3)
  - If YES: proceed to Phase 2
```

### Phase 1 Testing Checklist

```
PHASE 1 DONE WHEN:
☐ Ollama installed and running
☐ Gemma 7B + 13B models available
☐ Inference router code complete
☐ Router tests: 100% passing
☐ Cost tracking: logging to JSON file
☐ Quality validation: comparing local to Claude
☐ Proven task cache: persisting to disk
☐ Fallback logic: tested (local fail → Claude)
☐ Daily metrics: summarized correctly
☐ Documentation: added to repo
☐ Code review: checked for issues

BLOCKERS TO RESOLVE:
- [ ] If latency > 10s: investigate GPU issues
- [ ] If costs unclear: validate OpenAI API pricing
```

---

## Week 2: Phase 2 - Agent Roles & PraisonAI

### Daily Breakdown

**Monday-Tuesday: SQLite Schema (4 hours)**
```
Goal: Build agent memory backend

Day 1 (Monday):
  - [ ] Create /open-claw/data/ directory
  - [ ] Write agent_context.sql (schema)
  - [ ] Create ContextStore class (SQLite wrapper)
  - [ ] Implement: create_task(), get_pending_tasks()
  - [ ] Goal: SQLite database ready, schema tested

Day 2 (Tuesday):
  - [ ] Implement: get_agent_context(), save_agent_context()
  - [ ] Implement: approval gates (request/respond)
  - [ ] Implement: cost tracking (log_inference_cost)
  - [ ] Write unit tests: test_task_creation, test_approval_flow
  - [ ] Goal: ContextStore 100% tested

Deliverable: SQLite backend ready for agents
```

**Wednesday: Base Agent Class (3 hours)**
```
Goal: Create base class all agents inherit from

Day 3 (Wednesday):
  - [ ] Create /open-claw/agents/ directory
  - [ ] Write base_agent.py (OpenClawAgent class)
  - [ ] Implement: process_task(), approval gates, cost checks
  - [ ] Implement: handoff_to_agent() logic
  - [ ] Write tests: test_task_processing, test_approval_required()
  - [ ] Goal: Base agent logic working

Deliverable: Base agent class with tests passing
```

**Thursday-Friday: 4 Agent Implementations (6 hours)**
```
Goal: Build Researcher, Data, Executor, Calendar agents

Day 4 (Thursday):
  - [ ] Implement ResearcherAgent (research-focused)
  - [ ] Implement DataAgent (synthesis-focused)
  - [ ] Write tests: test_researcher_task, test_data_synthesis
  - [ ] Goal: 2 agents working with tests passing

Day 5 (Friday):
  - [ ] Implement ExecutorAgent (execution with approval gates)
  - [ ] Implement CalendarAgent (scheduling)
  - [ ] Write tests: test_executor_approval, test_calendar_task
  - [ ] Goal: 4 agents working, all tests passing

Deliverable: 4 agents implemented and tested
```

**Saturday: Integration Testing (3 hours)**
```
Goal: Test agent interactions

Day 6 (Saturday):
  - [ ] Test agent handoff: Researcher → Data
  - [ ] Test approval flow: Executor git operation requires approval
  - [ ] Test cost tracking: each agent logs costs
  - [ ] Verify SQLite persists across agent calls
  - [ ] Goal: End-to-end agent workflow tested

Deliverable: Agent integration validated
```

### Sunday Review (1 hour)

```markdown
## Week 2 Sunday Review - Phase 2 Complete ✓

**What worked:**
- SQLite backend solid
- 4 agents working independently
- Approval gates blocking as expected

**Metrics:**
- Agent task creation: ~10ms
- Context store reads: < 5ms
- Approval flow: waiting for human on cost/git gates

**Issues encountered:**
- [ ] (List any bugs found)

**Next week:**
- Put agent configs in git
- Design base template
- Test manifest loading

**Blockers?**
- [ ] Any approval gates not working?
- [ ] Cost tracking accurate?
```

### Phase 2 Testing Checklist

```
PHASE 2 DONE WHEN:
☐ SQLite schema complete
☐ ContextStore class: 100% tested
☐ Base agent class: working with tests
☐ 4 agents: each can process tasks
☐ Approval gates: cost, git, publishing gates working
☐ Handoff system: agents can hand off to each other
☐ Cost tracking: SQLite logging per agent
☐ Integration: end-to-end agent workflow tested
☐ Documentation: agent architecture documented

BLOCKERS TO RESOLVE:
- [ ] If approval gates stuck: debug wait logic
- [ ] If handoff fails: check task dependencies
```

---

## Week 3: Phase 3 - Agent Manifests & Git Versioning

### Daily Breakdown

**Monday: Base Template (3 hours)**
```
Goal: Create reusable agent template

Day 1 (Monday):
  - [ ] Create /open-claw/templates/ directory
  - [ ] Write base-agent.yml template
  - [ ] Create /open-claw/tools/ for shared tools
  - [ ] Write inference-tools.yml (shared)
  - [ ] Write approval-gates.yml (shared)
  - [ ] Goal: Template structure clear

Deliverable: Base template + shared tools defined
```

**Tuesday-Wednesday: Agent Manifests (4 hours)**
```
Goal: Define 4 agent YAML manifests

Day 2 (Tuesday):
  - [ ] Write researcher.agent.yml
  - [ ] Write data.agent.yml
  - [ ] Write executor.agent.yml
  - [ ] Goal: 4 manifests covering all agents

Day 3 (Wednesday):
  - [ ] Write calendar.agent.yml
  - [ ] Create AgentManifestLoader (Python code to load YAMLs)
  - [ ] Write tests: test_manifest_load, test_manifest_override
  - [ ] Goal: All manifests loading with correct overrides

Deliverable: 4 agent manifests + loader working
```

**Thursday: Git Setup (2 hours)**
```
Goal: Initialize git repo with proper structure

Day 4 (Thursday):
  - [ ] Create ~/open-claw-agents git repo
  - [ ] Add agents/ directory with all YAMLs
  - [ ] Add templates/ directory with base template
  - [ ] Add tools/ directory with shared tools
  - [ ] Create .gitignore
  - [ ] Initial commit: "Initial agent manifests"
  - [ ] Goal: All files in git

Deliverable: Git repo initialized with all manifests
```

**Friday: Git Workflow Testing (3 hours)**
```
Goal: Test branch-based versioning

Day 5 (Friday):
  - [ ] Create develop branch
  - [ ] Create feature/improve-researcher branch
  - [ ] Make a test change to researcher.agent.yml
  - [ ] Create (pretend) PR to develop
  - [ ] Merge back to develop, then main
  - [ ] Create git tag v1.0.0
  - [ ] Goal: Git workflow validated

Deliverable: Branch workflow tested, v1.0.0 tagged
```

**Saturday: Integration (2 hours)**
```
Goal: Connect git manifests to running agents

Day 6 (Saturday):
  - [ ] Update OpenClawAgent to load from YAML manifests
  - [ ] Test: Load researcher agent from git manifest
  - [ ] Verify: git version tracked in agent metadata
  - [ ] Goal: Agents running from git manifests

Deliverable: Agents loading from git-versioned manifests
```

### Sunday Review (1 hour)

```markdown
## Week 3 Sunday Review - Phase 3 Complete ✓

**What worked:**
- Template + override pattern clean
- Git workflow intuitive
- Manifest loading seamless

**Metrics:**
- Template reduces duplication: 50% less YAML per agent
- Git tags enable easy rollback
- Manifest load time: < 100ms

**Next week:**
- Connect all 3 phases: inference → agents → manifests
- End-to-end test: researcher → data synthesis → executor
- Production deployment checks

**Any issues?**
- [ ] Manifest override logic working correctly?
```

### Phase 3 Testing Checklist

```
PHASE 3 DONE WHEN:
☐ Base template created
☐ Shared tools defined
☐ 4 agent manifests created
☐ AgentManifestLoader working
☐ Git repo initialized with all files
☐ Branch-based workflow tested
☐ Git tags created (v1.0.0)
☐ Agents load from git manifests
☐ Manifest changes tracked in git
☐ Documentation: manifest schema documented

BLOCKERS TO RESOLVE:
- [ ] If manifest load fails: debug YAML parsing
- [ ] If git workflow confusing: create git guide
```

---

## Week 4: Integration & Production

### Daily Breakdown

**Monday: End-to-End Testing (4 hours)**
```
Goal: Test full workflow: inference → agents → manifests

Day 1 (Monday):
  - [ ] Create test workflow:
    1. ResearcherAgent infers topic
    2. DataAgent synthesizes findings
    3. ExecutorAgent publishes (with approval gate)
  - [ ] Execute workflow manually
  - [ ] Collect metrics: total cost, total latency
  - [ ] Goal: Full workflow working

Deliverable: End-to-end test passing
```

**Tuesday: Approval Gates Under Load (3 hours)**
```
Goal: Test approval system at scale

Day 2 (Tuesday):
  - [ ] ExecutorAgent attempts 5 git pushes
    - First 2: should be blocked (awaiting approval)
    - After approval: should proceed
  - [ ] Cost threshold: try operation > $2 threshold
  - [ ] Verify: approval requests logged correctly
  - [ ] Goal: Approval gates working under load

Deliverable: Approval system validated
```

**Wednesday: Cost Optimization Review (3 hours)**
```
Goal: Review cost data and optimize

Day 3 (Wednesday):
  - [ ] Review daily cost summary for Week 2-3
  - [ ] Which agent spends most? (Should be executor on Claude)
  - [ ] Which tasks are proven (cached)? (Should reduce costs)
  - [ ] Adjust cost thresholds if needed
  - [ ] Goal: Cost profile understood

Deliverable: Cost optimizations identified
```

**Thursday: Performance Tuning (3 hours)**
```
Goal: Optimize latency and efficiency

Day 4 (Thursday):
  - [ ] Profile: Which operations are slow?
  - [ ] Optimize: SQLite queries with indexes?
  - [ ] Cache: Proven tasks reducing API calls?
  - [ ] Benchmark: Compare Week 1 vs Week 4 metrics
  - [ ] Goal: 10% latency improvement identified

Deliverable: Performance optimizations in place
```

**Friday: Documentation & Handoff (4 hours)**
```
Goal: Document system for future reference

Day 5 (Friday):
  - [ ] Create README.md: How to run the system
  - [ ] Document agent roles: What each agent does
  - [ ] Document approval gates: How to approve actions
  - [ ] Create troubleshooting guide: Common issues
  - [ ] Goal: System fully documented

Deliverable: Complete documentation
```

**Saturday: Production Readiness (3 hours)**
```
Goal: Final checks before production

Day 6 (Saturday):
  - [ ] Backup database schema to git
  - [ ] Create fresh database (test clean state)
  - [ ] Run all agents from scratch
  - [ ] Verify: All data persists, no loss
  - [ ] Goal: System production-ready

Deliverable: Production readiness validated
```

### Sunday Retrospective (2 hours)

```markdown
## Week 4 Sunday Retrospective

### What Went Well
- [ ] Phase 1: inference routing solid
- [ ] Phase 2: agent architecture clean
- [ ] Phase 3: git workflow intuitive
- [ ] Phase 4: end-to-end integration smooth

### What Was Challenging
- [ ] (List any hard parts)

### Metrics (Full 4-Week Sprint)
- Weeks 1-4 costs: $XX (track all Claude API calls)
- Proven tasks cached: XXX (avoid revalidation)
- Agent execution success rate: XX%
- Approval gate accuracy: XX%

### What's Next (If Continuing)
- [ ] Vector search for researcher agent
- [ ] Multi-agent coordination (manager agent)
- [ ] Advanced scheduling (calendar conflicts)
- [ ] Historical analysis (analyze trends over time)

### Production Deployment
- [ ] Ready to deploy? YES/NO
- [ ] If YES: merge develop → main, tag v1.0.0
- [ ] If NO: what's blocking?

---

**🎉 Congratulations! Your Open Claw agent ecosystem is live.**
```

### Phase 4 Testing Checklist

```
PHASE 4 DONE WHEN:
☐ End-to-end workflow tested (inference → agents → manifests)
☐ Approval gates working at scale
☐ Cost tracking: accurate and optimized
☐ Performance: baseline established, improvements measured
☐ Documentation: complete and clear
☐ Database: clean and production-ready
☐ Code: all tests passing
☐ Git: all changes committed, tagged v1.0.0
☐ Runbook: how to operate system documented

PRODUCTION SIGN-OFF:
☐ All phases complete
☐ All tests passing
☐ Documentation done
☐ Metrics baseline established
☐ Ready for deployment
```

---

## Summary: 4-Week Sprint Schedule

```
WEEK 1 (10-15 hours)
  └─ Phase 1: Local inference router
  └─ Deliverable: Ollama + router + fallback working

WEEK 2 (10-15 hours)
  └─ Phase 2: 4 agents + SQLite backend
  └─ Deliverable: Agents creating tasks, handoff working

WEEK 3 (10-15 hours)
  └─ Phase 3: Agent manifests in git
  └─ Deliverable: Agents loading from git-versioned YAMLs

WEEK 4 (10-15 hours)
  └─ Integration: End-to-end workflows + production readiness
  └─ Deliverable: Full system live, documented, metrics baseline

TOTAL: 40-60 hours over 4 weeks
       = 10-15 hours per week (medium capacity ✓)
       = Realistic, sustainable pace
```

---

## Sunday Review Ritual

Every Sunday at [YOUR TIME], you'll:

1. **Review metrics** (15 min)
   - Cost spent this week
   - Inference latency averages
   - Approval gates triggered
   - Failed operations

2. **Assess blockers** (15 min)
   - What didn't work?
   - What's blocking next phase?
   - Any design changes needed?

3. **Plan next week** (15 min)
   - What's the focus?
   - Realistic time commitment?
   - What's the one thing that must be done?

4. **Document learnings** (15 min)
   - What surprised you?
   - What would you do differently?
   - Any improvements for next sprint?

---

## How to Track Progress

### Daily Log Template

Create `/open-claw/SPRINT_LOG.md`:

```markdown
# Sprint Log

## Week 1 - Phase 1

### Monday
- [x] Install Ollama
- [x] Pull gemma:7b (45 min)
- [ ] Complete by end of day

Time spent: 2.5 hours
Blockers: None

### Tuesday
- [x] Pull gemma:13b
- [x] Compare latency (7B: 2.3s, 13B: 6.1s)
- [ ] Complete router.py

Time spent: 2 hours
Blockers: None

... continue for each day
```

### Weekly Summary Template

```markdown
## Week 1 Summary

| Metric | Value |
|--------|-------|
| Hours spent | 11 |
| Tasks completed | 6/6 |
| Tests passing | 12/12 |
| Blockers | 0 |
| Learnings | - Ollama very stable<br/>- 13B slower than expected<br/>- May need Q4 variant |

**Ready for Week 2?** YES ✓
```

---

## Go Live Checklist (End of Week 4)

Before marking the sprint complete:

```
BEFORE PRODUCTION:

Code Quality
☐ All tests passing (Unit + integration)
☐ No console errors or warnings
☐ Code reviewed (self-review counts)

Operational
☐ Cost tracking: know what each agent costs
☐ Approval gates: confirm blocking gates work
☐ Fallback: local→cloud escalation tested
☐ Database: backup ready, restore tested

Documentation
☐ README: how to run agents
☐ Runbook: how to debug common issues
☐ Architecture diagram: document design
☐ Metrics baseline: what's "normal"?

Deployment
☐ Git: all code committed and tagged
☐ Branch: main is production-ready
☐ Tag: v1.0.0 created
☐ Rollback: can revert to v0.9.x if needed

GO LIVE SIGN-OFF
☐ Ready to deploy? _________________ (your initials)
☐ Date: _________________ (today's date)
```

---

## Next Steps After Week 4

**If all phases complete successfully:**
1. Merge develop → main, create v1.0.0 tag
2. Run agents daily (they'll improve with each task)
3. Monitor costs (fine-tune approval gates as needed)
4. Track quality of local vs. cloud inferences
5. Consider Phase 2 improvements:
   - Vector search for researcher
   - Manager agent for orchestration
   - Advanced scheduling for calendar agent

**If blockers emerge:**
1. Document the blocker
2. Create a follow-up task
3. Adjust timeline if needed
4. Don't let perfect be enemy of good

---

**You're ready to build. Start Week 1 on Monday. 🚀**
