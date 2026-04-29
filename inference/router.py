"""inference/router.py — Quality-first inference router for Open Claw agents."""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Literal, Optional

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
    provider: Literal["local", "claude"] = "local"
    tokens_input: int = 0
    tokens_output: int = 0
    latency_ms: float = 0.0
    cost_usd: float = 0.0
    quality_score: Optional[float] = None


@dataclass
class RoutingDecision:
    model: str
    provider: Literal["local", "claude"]
    reason: str
    confidence: float
    fallback_model: str


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
        complex_score = len(words & self.COMPLEX_KEYWORDS)
        simple_score = len(words & self.SIMPLE_KEYWORDS)
        return "complex" if complex_score > simple_score else "simple"


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
        sig = self._sig(prompt, task_type)
        return self.proven.get(sig, {}).get("validated", False)

    def mark_proven(self, prompt: str, task_type: str, quality_score: float):
        if quality_score >= 0.85:
            sig = self._sig(prompt, task_type)
            self.proven[sig] = {
                "validated": True,
                "quality_score": quality_score,
                "timestamp": datetime.now().isoformat(),
                "model": "gemma:13b",
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
            "cost_usd": response.cost_usd,
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
            local = [e for e in entries if e["provider"] == "local"]
            cloud = [e for e in entries if e["provider"] == "claude"]
            return {
                "total_inferences": len(entries),
                "local_inferences": len(local),
                "claude_inferences": len(cloud),
                "total_cost_usd": sum(e["cost_usd"] for e in entries),
                "avg_latency_ms": sum(e["latency_ms"] for e in entries) / len(entries),
            }
        except Exception as exc:
            return {"error": str(exc)}


# ============================================================================
# Inference Router
# ============================================================================


class InferenceRouter:
    OLLAMA_URL = "http://localhost:11434/api/generate"

    def __init__(self, claude_api_key: str, ollama_url: str = OLLAMA_URL):
        self.claude_api_key = claude_api_key
        self.ollama_url = ollama_url
        self.classifier = TaskClassifier()
        self.proven_cache = ProvenTaskCache()
        self.metrics = InferenceMetrics()

    async def route(self, request: InferenceRequest) -> RoutingDecision:
        if self.proven_cache.is_proven(request.prompt, request.task_type):
            return RoutingDecision(
                model="gemma:13b",
                provider="local",
                reason="proven task cached on local model",
                confidence=0.95,
                fallback_model="claude-sonnet-4-6",
            )

        task_type = (
            self.classifier.classify(request.prompt)
            if request.task_type == "simple"
            else request.task_type
        )

        if task_type == "complex":
            return RoutingDecision(
                model="claude-sonnet-4-6",
                provider="claude",
                reason="complex task → Claude for quality",
                confidence=0.95,
                fallback_model="gemma:13b",
            )

        return RoutingDecision(
            model="gemma:7b",
            provider="local",
            reason="simple task → local model for cost savings",
            confidence=0.70,
            fallback_model="claude-sonnet-4-6",
        )

    async def infer(self, request: InferenceRequest) -> InferenceResponse:
        start = datetime.now()
        decision = await self.route(request)

        try:
            if decision.provider == "local":
                response = await self._infer_local(request, decision.model)
            else:
                response = await self._infer_claude(request, decision.model)

            response.latency_ms = (datetime.now() - start).total_seconds() * 1000
            self.metrics.log(response, decision.reason)
            return response

        except Exception as exc:
            if decision.provider == "local":
                print(f"[router] local inference failed ({decision.model}): {exc}")
                print(f"[router] falling back to {decision.fallback_model}")
                fallback = await self._infer_claude(request, decision.fallback_model)
                fallback.latency_ms = (datetime.now() - start).total_seconds() * 1000
                self.metrics.log(fallback, f"fallback after local failure: {decision.reason}")
                return fallback
            raise

    async def _infer_local(self, request: InferenceRequest, model: str) -> InferenceResponse:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                self.ollama_url,
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

    async def _infer_claude(
        self, request: InferenceRequest, model: str = "claude-sonnet-4-6"
    ) -> InferenceResponse:
        import anthropic

        client = anthropic.Anthropic(api_key=self.claude_api_key)
        resp = client.messages.create(
            model=model,
            max_tokens=request.max_tokens,
            messages=[{"role": "user", "content": request.prompt}],
        )
        # Pricing: Sonnet 4.6 — ~$3/MTok input, ~$15/MTok output
        input_cost = (resp.usage.input_tokens / 1_000_000) * 3
        output_cost = (resp.usage.output_tokens / 1_000_000) * 15
        return InferenceResponse(
            content=resp.content[0].text,
            model_used=model,
            provider="claude",
            tokens_input=resp.usage.input_tokens,
            tokens_output=resp.usage.output_tokens,
            cost_usd=input_cost + output_cost,
        )


# ============================================================================
# Quality Validator
# ============================================================================


class QualityValidator:
    def __init__(self, claude_api_key: str):
        self.claude_api_key = claude_api_key

    async def validate(self, prompt: str, local_output: str) -> float:
        import anthropic

        client = anthropic.Anthropic(api_key=self.claude_api_key)
        assessment = f"""You are a quality assessor for AI outputs.

Original task: {prompt}

Local model output:
{local_output}

Rate 0-1 how well this answers the task. Consider correctness, completeness, clarity.
Respond with ONLY a number between 0 and 1."""

        resp = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=10,
            messages=[{"role": "user", "content": assessment}],
        )
        try:
            score = float(resp.content[0].text.strip())
            return max(0.0, min(1.0, score))
        except ValueError:
            return 0.5
