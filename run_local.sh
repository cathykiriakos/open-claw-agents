#!/usr/bin/env bash
# run_local.sh — Start Open Claw on your Mac Studio (local-only, no API key needed)
# Usage: bash run_local.sh

set -euo pipefail
REPO="$(cd "$(dirname "$0")" && pwd)"

echo "=== Open Claw — Local Mode ==="

# 1. Check Ollama is running
if ! curl -sf http://localhost:11434/api/tags &>/dev/null; then
  echo "Starting Ollama..."
  ollama serve &>/tmp/ollama.log &
  sleep 3
fi

MODELS=$(curl -sf http://localhost:11434/api/tags | python3 -c "import sys,json; print([m['name'] for m in json.load(sys.stdin).get('models',[])])")
echo "Models available: $MODELS"

if ! echo "$MODELS" | grep -q "gemma:7b"; then
  echo "ERROR: gemma:7b not found. Run: ollama pull gemma:7b"
  exit 1
fi

# 2. Activate venv (create if missing)
if [ ! -d "$REPO/.venv" ]; then
  echo "Creating Python venv..."
  python3 -m venv "$REPO/.venv"
  source "$REPO/.venv/bin/activate"
  pip install -q httpx
else
  source "$REPO/.venv/bin/activate"
fi

# 3. Init DB if not present
if [ ! -f "$REPO/data/agent_context.db" ]; then
  echo "Initialising SQLite database..."
  python3 - <<'PYEOF'
import sys, sqlite3
from pathlib import Path
sql = Path("data/agent_context.sql").read_text()
conn = sqlite3.connect("data/agent_context.db")
conn.executescript(sql)
conn.commit()
print("  DB ready.")
PYEOF
fi

# 4. Smoke test
echo "Running inference smoke test..."
python3 - <<'PYEOF'
import asyncio, sys
sys.path.insert(0, ".")
from inference.router import InferenceRouter, InferenceRequest

async def test():
    router = InferenceRouter()
    models = await router.available_models()
    print(f"  Ollama models: {models}")
    req = InferenceRequest(task_id="smoke-1", prompt="What is 2+2? Answer in one word.", task_type="simple")
    resp = await router.infer(req)
    print(f"  Model   : {resp.model_used}")
    print(f"  Latency : {resp.latency_ms:.0f}ms")
    print(f"  Answer  : {resp.content.strip()[:80]}")

asyncio.run(test())
PYEOF

echo ""
echo "=== Open Claw is ready ==="
echo "All inference runs locally via Ollama — no API key required."
echo ""
echo "Next: build your agents on top of OpenClawAgent in agents/base_agent.py"
