from __future__ import annotations

from typing import Dict

from tools.base import execute_with_guard


def _handler(input_data: Dict[str, object]) -> Dict[str, object]:
    source = input_data.get("source", "mock_audio.wav")
    return {
        "source": source,
        "segments": [
            {"start": "00:00", "end": "00:05", "text": "这是第一段转写示例。"},
            {"start": "00:05", "end": "00:10", "text": "这是第二段转写示例。"},
        ],
    }


def execute(input: dict) -> dict:
    return execute_with_guard("transcript", input, _handler)
