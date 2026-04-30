"""manifest_loader.py — Load agent YAML manifests and apply config to agent instances.

Usage:
    from manifest_loader import ManifestLoader
    loader = ManifestLoader()
    config = loader.load("researcher")
    # config.cost_limit_daily_usd, config.routing_strategy, etc.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False


AGENTS_DIR = Path(__file__).parent / "agents"
TEMPLATES_DIR = Path(__file__).parent / "templates"


@dataclass
class AgentManifestConfig:
    """Parsed, flattened config derived from an agent YAML manifest."""

    agent_id: str
    agent_name: str
    primary_role: str
    description: str
    version: str = "1.0.0"
    stability: str = "production"

    # Inference
    routing_strategy: str = "quality-first"
    local_models: List[str] = field(default_factory=lambda: ["gemma:7b"])
    cloud_model: str = "claude-sonnet-4-6"
    cost_threshold_usd: float = 2.0

    # Capabilities
    can_research: bool = False
    can_synthesize: bool = False
    can_execute: bool = False
    can_schedule: bool = False

    # Budget
    cost_limit_daily_usd: float = 10.0
    cost_limit_monthly_usd: float = 200.0

    # Integrations
    slack_enabled: bool = False
    twitter_enabled: bool = False
    email_enabled: bool = False
    google_calendar_enabled: bool = False
    git_enabled: bool = False

    # Raw manifest for anything not explicitly mapped
    raw: Dict[str, Any] = field(default_factory=dict)


class ManifestLoader:
    def __init__(
        self,
        agents_dir: Path = AGENTS_DIR,
        templates_dir: Path = TEMPLATES_DIR,
    ):
        self.agents_dir = agents_dir
        self.templates_dir = templates_dir

    # -------------------------------------------------------------------------
    # Public API
    # -------------------------------------------------------------------------

    def load(self, agent_id: str) -> AgentManifestConfig:
        """Load and parse the manifest for a given agent ID."""
        manifest_path = self.agents_dir / f"{agent_id}.agent.yml"
        if not manifest_path.exists():
            raise FileNotFoundError(f"Manifest not found: {manifest_path}")

        raw = self._parse_yaml(manifest_path)
        return self._to_config(raw, agent_id)

    def load_all(self) -> Dict[str, AgentManifestConfig]:
        """Load manifests for all agents found in the agents directory."""
        configs = {}
        for path in sorted(self.agents_dir.glob("*.agent.yml")):
            agent_id = path.name.replace(".agent.yml", "")
            try:
                configs[agent_id] = self.load(agent_id)
            except Exception as exc:
                print(f"[manifest_loader] Warning: could not load {path.name}: {exc}")
        return configs

    def print_summary(self):
        """Print a summary of all loaded agent configs."""
        configs = self.load_all()
        print(f"\n=== Agent Manifests ({len(configs)} loaded) ===\n")
        for agent_id, cfg in configs.items():
            caps = [k.replace("can_", "") for k in ["can_research", "can_synthesize", "can_execute", "can_schedule"] if getattr(cfg, k)]
            integrations = [k.replace("_enabled", "") for k in ["slack_enabled", "twitter_enabled", "google_calendar_enabled", "git_enabled"] if getattr(cfg, k)]
            print(f"  {agent_id} v{cfg.version} [{cfg.stability}]")
            print(f"    role        : {cfg.primary_role}")
            print(f"    routing     : {cfg.routing_strategy}")
            print(f"    capabilities: {', '.join(caps) or 'none'}")
            print(f"    integrations: {', '.join(integrations) or 'none'}")
            print(f"    daily budget: ${cfg.cost_limit_daily_usd}")
            print()

    # -------------------------------------------------------------------------
    # Internal
    # -------------------------------------------------------------------------

    def _parse_yaml(self, path: Path) -> Dict:
        if HAS_YAML:
            return yaml.safe_load(path.read_text()) or {}
        # Minimal YAML parser for simple key: value pairs (no PyYAML dependency)
        return self._minimal_parse(path.read_text())

    def _minimal_parse(self, text: str) -> Dict:
        """Very basic YAML parser — handles simple key: value only, no lists/nesting."""
        result: Dict = {}
        current: Dict = result
        stack = [result]
        indent_stack = [-1]

        for line in text.splitlines():
            stripped = line.lstrip()
            if not stripped or stripped.startswith("#"):
                continue
            indent = len(line) - len(stripped)
            if ":" in stripped:
                key, _, value = stripped.partition(":")
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                while len(indent_stack) > 1 and indent <= indent_stack[-1]:
                    stack.pop()
                    indent_stack.pop()
                current = stack[-1]
                if value:
                    current[key] = value
                else:
                    new_dict: Dict = {}
                    current[key] = new_dict
                    stack.append(new_dict)
                    indent_stack.append(indent)
        return result

    def _to_config(self, raw: Dict, agent_id: str) -> AgentManifestConfig:
        """Flatten the nested YAML structure into an AgentManifestConfig."""
        agent = raw.get("agent", raw)

        # Nested helpers
        def get(*keys, default=None):
            node = agent
            for k in keys:
                if not isinstance(node, dict):
                    return default
                node = node.get(k, {})
            return node if node != {} else default

        inference = agent.get("inference", {}) or {}
        capabilities = agent.get("capabilities", {}) or {}
        config_block = agent.get("config", {}) or {}
        integrations = agent.get("integrations", {}) or {}
        metadata = agent.get("metadata", {}) or {}
        cloud = (inference.get("models") or {}).get("cloud", {}) or {}

        local_instances = ((inference.get("models") or {}).get("local") or {}).get("instances", []) or []
        local_models = [i.get("model") for i in local_instances if isinstance(i, dict) and i.get("model")]

        def bool_val(val) -> bool:
            if isinstance(val, bool):
                return val
            return str(val).lower() in ("true", "yes", "1")

        def float_val(val, default: float) -> float:
            try:
                return float(val)
            except (TypeError, ValueError):
                return default

        return AgentManifestConfig(
            agent_id=agent_id,
            agent_name=str(agent.get("name", agent_id)),
            primary_role=str(agent.get("primary_role", "")),
            description=str(agent.get("description", "")),
            version=str(metadata.get("version", "1.0.0")),
            stability=str(metadata.get("stability", "production")),

            routing_strategy=str(inference.get("routing_strategy", "quality-first")),
            local_models=local_models or ["gemma:7b"],
            cloud_model=str(cloud.get("model", "claude-sonnet-4-6")),
            cost_threshold_usd=float_val(cloud.get("cost_threshold_usd"), 2.0),

            can_research=bool_val(capabilities.get("can_research", False)),
            can_synthesize=bool_val(capabilities.get("can_synthesize", False)),
            can_execute=bool_val(capabilities.get("can_execute", False)),
            can_schedule=bool_val(capabilities.get("can_schedule", False)),

            cost_limit_daily_usd=float_val(config_block.get("cost_limit_daily_usd"), 10.0),
            cost_limit_monthly_usd=float_val(config_block.get("cost_limit_monthly_usd"), 200.0),

            slack_enabled=bool_val(integrations.get("slack", False)),
            twitter_enabled=bool_val(integrations.get("twitter", False)),
            email_enabled=bool_val(integrations.get("email", False)),
            google_calendar_enabled=bool_val(integrations.get("google_calendar", False)),
            git_enabled=bool_val(integrations.get("git", False)),

            raw=raw,
        )
