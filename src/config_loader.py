from __future__ import annotations
import os
import yaml
from typing import Any, Dict
from dotenv import load_dotenv

# Load .env AS EARLY AS POSSIBLE
load_dotenv(override=False)

def load_yaml(path: str) -> Dict[str, Any]:
    # Resolve path relative to config_loader.py
    base_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(base_dir, "..", path)
    config_path = os.path.normpath(config_path)  # Normalize path to handle ".." correctly
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def load_config() -> Dict[str, Any]:
    app = load_yaml(os.path.join("config", "app.yaml"))
    prompts = load_yaml(os.path.join("config", "prompts.yaml"))
    return {"app": app, "prompts": prompts}