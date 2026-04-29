#!/usr/bin/env bash
# setup_mac.sh — Open Claw Mac Studio setup script
# Run once on your Mac Studio to install Ollama, pull models, and prep Python env.
# Usage: bash setup_mac.sh

set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "=== Open Claw Mac Studio Setup ==="
echo "Working directory: $REPO_DIR"
echo ""

# ============================================================================
# 1. Ollama
# ============================================================================

if ! command -v ollama &>/dev/null; then
  echo "[1/5] Installing Ollama..."
  brew install ollama
else
  echo "[1/5] Ollama already installed: $(ollama --version)"
fi

echo "[2/5] Starting Ollama service (if not running)..."
brew services start ollama 2>/dev/null || true
sleep 2

if ! curl -sf http://localhost:11434/api/tags &>/dev/null; then
  echo "      Ollama not responding yet — waiting 5s..."
  sleep 5
fi

echo "[3/5] Pulling Gemma models (this may take a few minutes)..."
ollama pull gemma:7b
ollama pull gemma:13b

echo "      Verifying models..."
curl -sf http://localhost:11434/api/tags | python3 -c "
import sys, json
data = json.load(sys.stdin)
models = [m['name'] for m in data.get('models', [])]
print('      Available models:', models)
needed = {'gemma:7b', 'gemma:13b'}
missing = needed - set(models)
if missing:
    print('      WARNING: missing models:', missing)
else:
    print('      All required models present.')
"

# ============================================================================
# 2. Custom Ollama model for Open Claw
# ============================================================================

MODELFILE="$HOME/.ollama/OpenClawModelfile"
cat > "$MODELFILE" << 'EOF'
FROM gemma:7b

PARAMETER top_k 40
PARAMETER top_p 0.95
PARAMETER temperature 0.7
PARAMETER repeat_penalty 1.1

SYSTEM """You are a helpful AI assistant integrated into an agentic system.
Be concise and structured in your responses.
When uncertain, say so clearly.
If a task requires high accuracy, defer to a human expert."""
EOF

echo "[4/5] Building optimised gemma:7b-openclaw model..."
ollama create gemma:7b-openclaw -f "$MODELFILE"

# ============================================================================
# 3. Python environment
# ============================================================================

echo "[5/5] Setting up Python environment..."
python3 -m venv "$REPO_DIR/.venv"
source "$REPO_DIR/.venv/bin/activate"
pip install --upgrade pip -q
pip install -r "$REPO_DIR/requirements.txt" -q

# ============================================================================
# 4. Verify inference
# ============================================================================

echo ""
echo "=== Verifying local inference ==="
curl -sf http://localhost:11434/api/generate \
  -H "Content-Type: application/json" \
  -d '{"model":"gemma:7b","prompt":"What is 2+2? Answer in one word.","stream":false}' \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print('Response:', d.get('response','').strip())"

# ============================================================================
# 5. Environment file reminder
# ============================================================================

if [ ! -f "$REPO_DIR/.env" ]; then
  echo ""
  echo "=== Action required ==="
  echo "Create $REPO_DIR/.env with your Anthropic API key:"
  echo "  echo 'ANTHROPIC_API_KEY=sk-ant-...' > .env"
fi

echo ""
echo "=== Setup complete ==="
echo "Activate your venv: source $REPO_DIR/.venv/bin/activate"
echo "Run a quick test:   python -c \"from inference.router import InferenceRouter; print('OK')\""
