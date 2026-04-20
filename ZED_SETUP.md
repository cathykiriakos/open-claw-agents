# Zed Setup for Open Claw
**Profile:** OpenClaw (separate from personal)  
**Purpose:** Isolated, reproducible development environment for agent work  
**Version Control:** Settings tracked in git for repeatability

---

## Step 1: Create Separate Zed Profile

### On macOS

```bash
# Zed profiles are stored in ~/Library/Application Support/Zed
# Create a new profile directory for OpenClaw

# 1. Open Zed (you'll be in default profile)
open -a Zed

# 2. In Zed, open Command Palette (Cmd+Shift+P)
# 3. Search: "Profiles: Create Profile"
# 4. Name it: "OpenClaw"

# Alternatively, create manually:
mkdir -p ~/Library/Application\ Support/Zed/profiles/OpenClaw

# Verify it was created:
ls -la ~/Library/Application\ Support/Zed/profiles/
```

### Launch with OpenClaw Profile

```bash
# Create an alias in ~/.zshrc for quick switching

cat >> ~/.zshrc << 'EOF'
# Zed profiles
alias zed-openclaw='open -a Zed --args --profile OpenClaw'
alias zed-personal='open -a Zed --args --profile Default'
EOF

source ~/.zshrc

# Test it
zed-openclaw  # Opens Zed in OpenClaw profile
```

---

## Step 2: Version Control Zed Settings

### Create .zed Directory in Git Repo

```bash
# In your open-claw-agents repo:
cd ~/open-claw-agents

# Create .zed directory for version-controlled settings
mkdir -p .zed

# Create settings files
```

### Settings Structure

```
open-claw-agents/
├── .zed/
│   ├── settings.json          # Editor settings (theme, keybindings, etc.)
│   ├── extensions.json        # List of recommended extensions
│   └── README.md              # How to use these settings
├── agents/
├── templates/
├── tools/
└── .gitignore
```

---

## Step 3: Create Version-Controlled Settings

### .zed/settings.json

```json
{
  "theme": "Catppuccin Mocha",
  "buffer_font_size": 12,
  "ui_font_size": 14,
  
  "editor": {
    "tab_size": 2,
    "soft_wrap": "preferred",
    "show_copilot_suggestions": false,
    "show_whitespace": "all",
    "indent_size": 2
  },
  
  "git": {
    "git_gutter": "tracked_changes"
  },
  
  "languages": {
    "Python": {
      "tab_size": 4,
      "formatter": "black"
    },
    "YAML": {
      "tab_size": 2
    },
    "JSON": {
      "tab_size": 2
    }
  },
  
  "format_on_save": "on",
  
  "lsp": {
    "pylance": {
      "settings": {
        "python.linting.enabled": true,
        "python.linting.pylintEnabled": true,
        "python.formatting.provider": "black"
      }
    }
  }
}
```

### .zed/extensions.json

```json
{
  "description": "Recommended extensions for Open Claw development",
  "extensions": [
    "python",
    "copilot",
    "prettier",
    "sqltools",
    "git-editor",
    "markdownlint"
  ],
  "installation_instructions": "Install via Extensions > + > Search for each above"
}
```

### .zed/keybindings.json (Optional)

```json
{
  "context": "Editor",
  "bindings": {
    "cmd-shift-f": "editor::format",
    "cmd-k cmd-t": "editor::new_terminal",
    "cmd-b": "editor::toggle_sidebar"
  }
}
```

### .zed/README.md

```markdown
# Zed Configuration for Open Claw

## Setup Instructions

### 1. Create Open Claw Profile
```bash
alias zed-openclaw='open -a Zed --args --profile OpenClaw'
zed-openclaw  # Opens OpenClaw profile
```

### 2. Link Settings to Zed Profile
```bash
# Create symlink from repo settings to Zed profile directory
ln -s $(pwd)/.zed/settings.json \
  ~/Library/Application\ Support/Zed/profiles/OpenClaw/settings.json

ln -s $(pwd)/.zed/keybindings.json \
  ~/Library/Application\ Support/Zed/profiles/OpenClaw/keybindings.json
```

### 3. Install Extensions
Open Extensions in Zed and search for each in `extensions.json`:
- Python
- Copilot (optional, for code suggestions)
- Prettier (code formatting)
- Git Editor

### 4. Done
When you open `zed-openclaw`, it will use these version-controlled settings.

## Notes

- **Settings are symlinked:** If you update `.zed/settings.json` in git, restart Zed to reload
- **Personal profile untouched:** `zed-personal` uses your default settings
- **Reproducible:** New machine? Just run the symlink commands above and settings are loaded

## Updating Settings

If you change settings in Zed (OpenClaw profile):
1. Edit manually in `.zed/settings.json` (or let Zed update it)
2. Commit to git: `git add .zed/ && git commit -m "chore: update Zed settings"`
3. This keeps all developers/machines in sync
```

---

## Step 4: Symlink Settings to Zed

```bash
# In open-claw-agents repo directory:

# Create symlinks from version-controlled settings to Zed profile
ln -s $(pwd)/.zed/settings.json \
  ~/Library/Application\ Support/Zed/profiles/OpenClaw/settings.json

ln -s $(pwd)/.zed/keybindings.json \
  ~/Library/Application\ Support/Zed/profiles/OpenClaw/keybindings.json

# Verify symlinks created
ls -la ~/Library/Application\ Support/Zed/profiles/OpenClaw/

# Expected output:
# settings.json -> /Users/cathy/open-claw-agents/.zed/settings.json
# keybindings.json -> /Users/cathy/open-claw-agents/.zed/keybindings.json
```

---

## Step 5: Test Setup

```bash
# Launch OpenClaw profile
zed-openclaw

# Verify:
# 1. Theme is set (should see Catppuccin Mocha)
# 2. Settings work (e.g., whitespace visible)
# 3. Terminal opens (Cmd+K Cmd+T)
# 4. Code formats on save (edit a Python file, save with Cmd+S)

# Once verified, add to git:
cd ~/open-claw-agents
git add .zed/
git commit -m "chore: add Zed settings for reproducible development environment"
git push origin develop
```

---

## Workflow: Using OpenClaw Profile

### Daily Work

```bash
# Open Open Claw project in OpenClaw profile
zed-openclaw ~/open-claw-agents

# All settings auto-loaded from .zed/ directory
# Start developing Phase 1B
```

### Switching Contexts

```bash
# Work on personal projects
zed-personal ~/personal-project

# Back to Open Claw
zed-openclaw ~/open-claw-agents
```

### Sharing Settings with Team (Future)

If you bring others into Open Claw:
```bash
# They just clone the repo
git clone https://github.com/cathykiriakos/open-claw-agents.git
cd open-claw-agents

# Run setup script (create in repo):
./scripts/setup-zed.sh

# Their Zed OpenClaw profile is now configured identically
```

---

## Troubleshooting

### Symlinks Not Working?

```bash
# If symlinks fail, try:
# 1. Check if Zed profile directory exists
ls ~/Library/Application\ Support/Zed/profiles/OpenClaw/

# 2. If not, create it manually
mkdir -p ~/Library/Application\ Support/Zed/profiles/OpenClaw

# 3. Try symlink again
ln -s $(pwd)/.zed/settings.json \
  ~/Library/Application\ Support/Zed/profiles/OpenClaw/settings.json
```

### Settings Not Loading?

```bash
# Zed caches settings. Force reload:
# 1. Quit Zed entirely (Cmd+Q)
# 2. Reopen with profile:
zed-openclaw

# 3. Check that symlinks are correct:
ls -la ~/Library/Application\ Support/Zed/profiles/OpenClaw/settings.json
# Should show arrow pointing to .zed/settings.json
```

### Want to Edit Settings Manually?

```bash
# Instead of symlink, edit Zed settings directly:
# 1. In Zed (OpenClaw profile), open Command Palette (Cmd+Shift+P)
# 2. Search "Settings: Open Default Settings"
# 3. Edit, save

# Then copy those to .zed/settings.json:
cp ~/Library/Application\ Support/Zed/profiles/OpenClaw/settings.json \
   $(pwd)/.zed/settings.json

# Commit to git
git add .zed/settings.json
git commit -m "chore: update Zed settings"
```

---

## Why This Approach?

✅ **Separation of concerns:** Personal Zed untouched, OpenClaw isolated  
✅ **Reproducible:** Settings in git = anyone can get same environment  
✅ **Version controlled:** Track setting changes like code changes  
✅ **Scalable:** Add team members, they run setup script, done  
✅ **Easy switching:** `zed-personal` vs `zed-openclaw` aliases  

---

## Next: Phase 1B Ready

Once setup is complete:
1. Open OpenClaw profile: `zed-openclaw ~/open-claw-agents`
2. Create `/open-claw/inference/` directory structure
3. Start building `router.py` from PHASE_1 guide
4. Use Zed to edit Python files (formatter, linting all set)

Ready to build Phase 1B? 🚀
