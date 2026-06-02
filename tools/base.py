from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Callable, Dict

from core.logging_utils import append_json_line, ensure_directory


def _tool_log_path() -> Path:
    base_dir = Path(
        os.getenv(
            "MEDIA_AGENT_LOG_DIR",
            str(Path(__file__).resolve().parents[1] / "logs"),
        )
    )
    ensure_directory(base_dir)
    return base_dir / "tools.log"


def execute_with_guard(
    tool_name: str,
    input_data: Dict[str, Any],
    handler: Callable[[Dict[str, Any]], Dict[str, Any]],
) -> Dict[str, Any]:
    try:
        data = handler(input_data)
        result = {
            "success": True,
            "tool": tool_name,
            "data": data,
            "error": None,
            "meta": {"mock": True},
        }
    except Exception as exc:  # pragma: no cover - defensive path
        result = {
            "success": False,
            "tool": tool_name,
            "data": {},
            "error": {"type": exc.__class__.__name__, "message": str(exc)},
            "meta": {"mock": True},
        }

    append_json_line(
        _tool_log_path(),
        {"tool": tool_name, "input": input_data, "result": result},
    )
    return result
