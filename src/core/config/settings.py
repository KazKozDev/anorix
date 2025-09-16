"""
Centralized settings loader for LLM configuration.
Reads from environment first, then falls back to config/friend_config.yaml.
Env overrides:
  OLLAMA_MODEL, OLLAMA_BASE_URL, OLLAMA_TEMPERATURE
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, Any

import yaml


def load_llm_settings() -> Dict[str, Any]:
    """Load LLM settings from env with YAML fallback."""
    # Defaults
    settings = {
        "model_name": "gpt-oss:20b",
        "base_url": "http://localhost:11434",
        "temperature": 0.2,
    }

    # YAML fallback
    try:
        cfg_path = Path("config/friend_config.yaml")
        if cfg_path.exists():
            with open(cfg_path, "r", encoding="utf-8") as f:
                cfg = yaml.safe_load(f) or {}
            llm = cfg.get("llm", {}) or {}
            settings.update({
                "model_name": llm.get("model_name", settings["model_name"]),
                "base_url": llm.get("base_url", settings["base_url"]),
                "temperature": llm.get("temperature", settings["temperature"]),
            })
    except Exception:
        pass

    # Env overrides
    model = os.getenv("OLLAMA_MODEL")
    base = os.getenv("OLLAMA_BASE_URL")
    temp = os.getenv("OLLAMA_TEMPERATURE")
    if model:
        settings["model_name"] = model
    if base:
        settings["base_url"] = base
    if temp:
        try:
            settings["temperature"] = float(temp)
        except ValueError:
            pass

    return settings
