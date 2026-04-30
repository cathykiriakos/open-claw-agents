"""inference/router.py — Local-first inference router for Open Claw agents.

All inference routes to Ollama (localhost:11434). No cloud API required.
Complex tasks use gemma:7b with a larger context window; simple tasks use
gemma:7b at default settings. When gemma:13b is available it is used for
proven/cached tasks instead.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, Literal, Optional

import httpx


# ============================================================================
# Data Models
# ============================================================================


@dataclass
class InferenceRequest:
    task_id: str
    prompt: str
    task_type: Literal["simple", "complex", "proven"] = "simple"
    max_tokens: int = 500
    temperature: float = 0.7
    agent_role: str = "executor"


@dataclass
class InferenceResponse:
    content: str
    model_used: str
    provider: str = "local"
    tokens_input: int = 0
    tokens_output: int = 0
    latency_ms: float = 0.0
    cost_usd: float = 0.0        # always 0 — local inference is free
    quality_score: Optional[float] = None


@dataclass
class RoutingDecision:
    model: str
    reason: str
    confidence: float
    fallback_model: str          # used if primary model is missing


# ============================================================================
# Task Classifier
# ============================================================================


class TaskClassifier:
    SIMPLE_KEYWORDS = {
        "retrieve", "list", "summarize", "extract", "format",
        "categorize", "count", "search", "lookup", "validate",
        "create", "schedule", "block", "remind", "find",
    }
    COMPLEX_KEYWORDS = {
        "analyze", "reason", "decide", "recommend", "evaluate",
        "compare", "synthesize", "strategize", "predict", "debug",
        "refactor", "architecture", "design",
    }

    def classify(self, prompt: str) -> Literal["simple", "complex"]:
        words = set(prompt.lower().split())
        if len(words & self.COMPLEX_KEYWORDS) > len(words & self.SIMPLE_KEYWORDS):
            return "complex"
        return "simple"


# ============================================================================
# Proven Task Cache
# ============================================================================


class ProvenTaskCache:
    def __init__(self, cache_file: str = "data/proven_tasks.json"):
        self.cache_file = Path(cache_file)
        self.proven: Dict[str, Dict] = self._load()

    def _load(self) -> Dict:
        try:
            return json.loads(self.cache_file.read_text())
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def _save(self):
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)
        self.cache_file.write_text(json.dumps(self.proven, indent=2))

    def _sig(self, prompt: str, task_type: str) -> str:
        return hashlib.sha256(f"{task_type}:{prompt[:100]}".encode()).hexdigest()[:16]

    def is_proven(self, prompt: str, task_type: str) -> bool:
        return self.proven.get(self._sig(prompt, task_type), {}).get("validated", False)

    def mark_proven(self, prompt: str, task_type: str, model: str, quality_score: float):
        if quality_score >= 0.85:
            sig = self._sig(prompt, task_type)
            self.proven[sig] = {
                "validated": True,
                "quality_score": quality_score,
                "timestamp": datetime.now().isoformat(),
                "model": model,
            }
            self._save()


# ============================================================================
# Observability
# ============================================================================


class InferenceMetrics:
    def __init__(self, log_file: str = "logs/inference_metrics.jsonl"):
        self.log_file = Path(log_file)

    def log(self, response: InferenceResponse, routing_reason: str):
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        entry = {
            "timestamp": datetime.now().isoformat(),
            "model": response.model_used,
            "provider": response.provider,
            "tokens_input": response.tokens_input,
            "tokens_output": response.tokens_output,
            "latency_ms": response.latency_ms,
            "cost_usd": 0.0,
            "routing_reason": routing_reason,
            "quality_score": response.quality_score,
        }
        with self.log_file.open("a") as f:
            f.write(json.dumps(entry) + "\n")

    def daily_summary(self) -> Dict:
        try:
            today = datetime.now().date().isoformat()
            entries = [
                json.loads(line)
                for line in self.log_file.read_text().splitlines()
                if line and json.loads(line)["timestamp"].startswith(today)
            ]
            if not entries:
                return {"total_inferences": 0, "total_cost_usd": 0.0}
            return {
                "total_inferences": len(entries),
                "avg_latency_ms": sum(e["latency_ms"] for e in entries) / len(entries),
                "total_cost_usd": 0.0,
            }
        except Exception as exc:
            return {"error": str(exc)}


# ============================================================================
# Inference Router — local only
# ============================================================================


class InferenceRouter:
    DEFAULT_OLLAMA_URL = "http://localhost:11434"

    def __init__(self, ollama_url: str = DEFAULT_OLLAMA_URL):
        self.ollama_url = ollama_url.rstrip("/")
        self.classifier = TaskClassifier()
        self.proven_cache = ProvenTaskCache()
        self.metrics = InferenceMetrics()
        self._available_models: Optional[set] = None

    async def available_models(self) -> set:
        if self._available_models is None:
            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    resp = await client.get(f"{self.ollama_url}/api/tags")
                    data = resp.json()
                    self._available_models = {m["name"] for m in data.get("models", [])}
            except Exception:
                self._available_models = set()
        return self._available_models

    async def route(self, request: InferenceRequest) -> RoutingDecision:
        models = await self.available_models()

        # Prefer gemma:13b for proven/cached tasks if available
        if self.proven_cache.is_proven(request.prompt, request.task_type):
            primary = "gemma:13b" if "gemma:13b" in models else "gemma:7b"
            return RoutingDecision(
                model=primary,
                reason="proven task — using best available local model",
                confidence=0.95,
                fallback_model="gemma:7b",
            )

        task_type = (
            self.classifier.classify(request.prompt)
            if request.task_type == "simple"
            else request.task_type
        )

        if task_type == "complex":
            # Use 13b if available, fall back to 7b
            primary = "gemma:13b" if "gemma:13b" in models else "gemma:7b"
            return RoutingDecision(
                model=primary,
                reason="complex task → best available local model",
                confidence=0.80,
                fallback_model="gemma:7b",
            )

        return RoutingDecision(
            model="gemma:7b",
            reason="simple task → gemma:7b",
            confidence=0.90,
            fallback_model="gemma:7b",
        )

    async def infer(self, request: InferenceRequest) -> InferenceResponse:
        start = datetime.now()
        decision = await self.route(request)

        try:
            response = await self._call_ollama(request, decision.model)
        except Exception as exc:
            if decision.fallback_model != decision.model:
                print(f"[router] {decision.model} failed: {exc} — retrying with {decision.fallback_model}")
                response = await self._call_ollama(request, decision.fallback_model)
            else:
                raise RuntimeError(
                    f"Ollama inference failed ({decision.model}): {exc}\n"
                    "Make sure Ollama is running: ollama serve"
                ) from exc

        response.latency_ms = (datetime.now() - start).total_seconds() * 1000
        self.metrics.log(response, decision.reason)
        return response

    async def _call_ollama(self, request: InferenceRequest, model: str) -> InferenceResponse:
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": model,
                    "prompt": request.prompt,
                    "stream": False,
                    "options": {
                        "top_k": 40,
                        "top_p": 0.95,
                        "temperature": request.temperature,
                        "num_predict": request.max_tokens,
                    },
                },
            )
            resp.raise_for_status()
            data = resp.json()
            content = data.get("response", "")
            return InferenceResponse(
                content=content,
                model_used=model,
                provider="local",
                tokens_input=len(request.prompt.split()),
                tokens_output=len(content.split()),
                cost_usd=0.0,
            )
