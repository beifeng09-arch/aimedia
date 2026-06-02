from __future__ import annotations

from typing import Dict

from tools.base import execute_with_guard


def _handler(input_data: Dict[str, object]) -> Dict[str, object]:
    return {
        "presenter_style": input_data.get("style", "news"),
        "video_path": "mock_assets/avatar_presenter.mp4",
        "scene_notes": ["正面机位", "轻微手势", "中性背景"],
    }


def execute(input: dict) -> dict:
    return execute_with_guard("avatar_presenter", input, _handler)
