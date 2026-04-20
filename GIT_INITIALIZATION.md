# Git Initialization: Connect Open Claw to GitHub
**Goal:** Initialize local git repo, create GitHub repo, and push your agent code  
**Visibility:** Public (open-source, shareable)  
**Location:** cathykiriakos/open-claw-agents (personal GitHub)

---

## Step 1: Initialize Git Locally

```bash
# Navigate to your Open Claw agents directory
cd ~/open-claw-agents

# Initialize git
git init

# Verify initialization
git status
# Expected output:
# On branch master
# No commits yet
# Untracked files:
#   (use "git add <file>..." to include in what will be committed)
#           agents/
#           templates/
#           tools/
#           .gitignore
#           README.md
```

---

## Step 2: Create .gitignore

```bash
# Create .gitignore for Open Claw project
cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# SQLite databases (local, not versioned)
*.db
*.sqlite
*.sqlite3
data/*.db

# Logs
*.log
logs/

# Environment variables
.env
.env.local
.env.*.local

# IDE
.vscode/
.idea/
*.swp
*.swo
*~
.DS_Store

# Zed (personal settings, not version-controlled)
# NOTE: .zed/ IS version-controlled, but personal editor state is not
# ~/.Library/Application Support/Zed/ is NOT tracked

# OS
.DS_Store
Thumbs.db

# Node (if using any node tools)
node_modules/
npm-debug.log

# Optional: Temporary files
*.tmp
*.temp
EOF

git add .gitignore
git commit -m "chore: add .gitignore"
```

---

## Step 3: Create Initial Commit

```bash
# Add all files to staging (except what's in .gitignore)
git add agents/ templates/ tools/ .zed/ README.md

# Create initial commit
git commit -m "Initial commit: Open Claw agent infrastructure

- Phase 1: Inference router with quality-first routing
- Phase 2: 4-agent system (Researcher, Data, Executor, Calendar)
- Phase 3: Git-versioned agent manifests with templates
- Phase 4: 4-week implementation sprint plan

This is the foundation for a local-first agentic AI ecosystem
running on Ollama + Claude API (cloud fallback).

Co-Authored-By: Claude Haiku 4.5 <noreply@anthropic.com>"

# Verify commit
git log --oneline
# Expected:
# <hash> Initial commit: Open Claw agent infrastructure
```

---

## Step 4: Create GitHub Repository

### Option A: Via GitHub Web UI (Easiest)

1. Go to **https://github.com/new**
2. Fill in:
   - **Repository name:** `open-claw-agents`
   - **Description:** "Local-first agentic AI ecosystem: Ollama-powered agents with Claude fallback"
   - **Visibility:** Public
   - **Initialize repository:** ☐ (uncheck — you already have local repo)
   - Skip README, .gitignore, license (you already have these)

3. Click **Create repository**

4. You'll see a page with instructions. Copy the commands:
   ```
   git remote add origin https://github.com/cathykiriakos/open-claw-agents.git
   git branch -M main
   git push -u origin main
   ```

### Option B: Via GitHub CLI (If Installed)

```bash
# Check if gh CLI is installed
gh --version

# If not installed:
# brew install gh
# gh auth login (follow prompts to authenticate)

# Create repo
gh repo create open-claw-agents \
  --public \
  --source=. \
  --remote=origin \
  --push \
  --description "Local-first agentic AI ecosystem: Ollama-powered agents with Claude fallback"
```

---

## Step 5: Connect Local to GitHub

```bash
# Navigate to your repo
cd ~/open-claw-agents

# Add GitHub as remote (from Step 4)
git remote add origin https://github.com/cathykiriakos/open-claw-agents.git

# Rename main branch to 'main' (instead of 'master')
git branch -M main

# Push initial commit to GitHub
git push -u origin main

# Verify it worked
git remote -v
# Expected output:
# origin  https://github.com/cathykiriakos/open-claw-agents.git (fetch)
# origin  https://github.com/cathykiriakos/open-claw-agents.git (push)

# Check GitHub
# Go to https://github.com/cathykiriakos/open-claw-agents
# You should see all your files pushed!
```

---

## Step 6: Create Develop Branch

```bash
# Create develop branch for staging (used in Phase 3)
git checkout -b develop

# Push develop to GitHub
git push -u origin develop

# Verify both branches exist
git branch -a
# Expected output:
# * develop
#   main
#   remotes/origin/develop
#   remotes/origin/main

# Configure default branch (optional, makes develop the default for PRs)
# Go to GitHub repo → Settings → Branches → Default branch → Select "develop"
```

---

## Step 7: Update Zed Settings in Git

Since your `.zed/` settings are already in the repo, commit them:

```bash
# Make sure .zed/ is tracked
git add .zed/

# Commit Zed settings
git commit -m "chore: add Zed configuration for reproducible development

- Settings: theme, keybindings, formatting
- Extensions: Python, Prettier, SQLTools, Git Editor
- Symlink instructions in .zed/README.md"

# Push to both branches
git push origin main
git push origin develop
```

---

## Step 8: Verify Setup

```bash
# Check local status
git status
# Expected: "On branch main" / "On branch develop" with nothing to commit

# Check remote status
git remote -v
# Expected: origin pointing to your GitHub repo

# Check branches
git branch -a
# Expected: main and develop visible locally and on remote

# Check GitHub
# Go to https://github.com/cathykiriakos/open-claw-agents
# Verify you see:
# - Branches: main, develop
# - Files: agents/, templates/, tools/, .zed/, README.md
# - Commits: your initial commit
```

---

## Now You Have Two Branches

```
GitHub: cathykiriakos/open-claw-agents

main branch (PRODUCTION)
├── Your initial commit with agent infrastructure
└── (Will tag v1.0.0, v1.0.1, etc. here)

develop branch (STAGING)
├── Your initial commit (same as main, for now)
└── (Feature branches will branch from here)
```

---

## Workflow Going Forward

### For Phase 1B Development

```bash
# You're on develop (or switch to it)
git checkout develop

# Create a feature branch for Phase 1B
git checkout -b feature/phase-1-inference-router

# Make changes:
# - Create /open-claw/inference/router.py
# - Create tests/test_inference_router.py
# - etc.

# Commit changes
git add open-claw/inference/
git commit -m "feat: implement inference router with quality-first routing

- Route simple tasks to Gemma 7B (local)
- Route complex tasks to Claude API
- Implement proven task cache
- Add cost tracking and observability"

# Push feature branch
git push origin feature/phase-1-inference-router

# When Phase 1B is done:
# 1. On GitHub, create PR from feature/phase-1-inference-router → develop
# 2. Review your own code (make sure tests pass)
# 3. Merge to develop
# 4. Delete feature branch
```

### At End of Week 4 (Production Release)

```bash
# All phases complete, tested on develop
# Merge to main for production release

git checkout main
git pull origin main
git merge develop
git tag v1.0.0
git push origin main --tags

# Now your agents are "released" and can be deployed
```

---

## Useful Git Commands for Your Workflow

```bash
# Check which branch you're on
git branch

# Switch branches
git checkout develop
git checkout main

# See commit history
git log --oneline

# See what changed since last commit
git diff

# Undo uncommitted changes (careful!)
git restore <file>

# See status
git status

# Push to GitHub
git push origin <branch-name>

# Pull latest from GitHub
git pull origin <branch-name>

# Create a tag (for releases)
git tag v1.0.0
git push origin v1.0.0
```

---

## Your Repository Structure (After Setup)

```
cathykiriakos/open-claw-agents (GitHub)

├── main
│   ├── Initial commit
│   └── Tags: v1.0.0, v1.0.1, etc. (releases)
│
├── develop
│   ├── Initial commit
│   └── Feature branches merged here before main
│
├── Folders
│   ├── agents/
│   ├── templates/
│   ├── tools/
│   ├── .zed/
│   ├── README.md
│   └── .gitignore
│
└── Settings
    ├── Default branch: develop (or main, your choice)
    └── Visibility: Public
```

---

## Troubleshooting

### "fatal: not a git repository"

```bash
# You're in wrong directory
cd ~/open-claw-agents
git status  # Should work now
```

### "remote origin already exists"

```bash
# If you created remote twice
git remote remove origin
git remote add origin https://github.com/cathykiriakos/open-claw-agents.git
```

### Can't push to GitHub

```bash
# Make sure you're authenticated
gh auth status
# If not logged in:
gh auth login

# Or use SSH instead of HTTPS
git remote set-url origin git@github.com:cathykiriakos/open-claw-agents.git
```

### Want to change repository to private later?

```bash
# Go to GitHub → Settings → Change repository visibility → Private
# That's it! Local git doesn't care about GitHub visibility.
```

---

## Next Steps

1. **Initialize git locally** (Steps 1-3)
2. **Create GitHub repo** (Step 4)
3. **Connect local to GitHub** (Step 5)
4. **Create develop branch** (Step 6)
5. **Verify setup** (Step 8)

Then you're ready for **Phase 1B** with full version control! 🎉

```bash
# Your repo is now ready
cd ~/open-claw-agents
git status
# On branch develop
# nothing to commit, working tree clean
```

Ready to build!
