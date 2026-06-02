from __future__ import annotations

from typing import Dict

from tools.base import execute_with_guard


def _handler(input_data: Dict[str, object]) -> Dict[str, object]:
    topic = input_data.get("topic", "未命名素材")
    return {
        "topic": topic,
        "asset_bundle": [
            {"name": "map_clip.mp4", "path": f"mock_assets/{topic}_map_clip.mp4"},
            {"name": "broll_clip.mp4", "path": f"mock_assets/{topic}_broll_clip.mp4"},
        ],
    }


def execute(input: dict) -> dict:
    return execute_with_guard("video_download", input, _handler)
