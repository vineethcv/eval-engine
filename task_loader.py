from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

import yaml


def load_json(path: str | Path) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_yaml(path: str | Path) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _optional_json(path: str | Path | None) -> Any | None:
    if not path:
        return None

    p = Path(path)
    if not p.exists():
        return None

    return load_json(p)


def load_task_bundle(task_config_path: str) -> Dict[str, Any]:
    task_config = load_yaml(task_config_path)

    bundle: Dict[str, Any] = {
        "task_config_path": task_config_path,
        "task_config": task_config,
        "dataset": load_json(task_config["dataset_path"]),
        "rubric": load_json(task_config["rubric_path"]),
        "knowledge_base": _optional_json(task_config.get("knowledge_base_path")),
        "catalog": _optional_json(task_config.get("catalog_path")),
        "orders": _optional_json(task_config.get("orders_path")),
        "tool_scenarios": _optional_json(task_config.get("tool_scenarios_path")),
        "expected_outputs": _optional_json(task_config.get("expected_outputs_path")),
    }

    return bundle