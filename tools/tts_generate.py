from __future__ import annotations

from typing import Dict

from tools.base import execute_with_guard


def _handler(input_data: Dict[str, object]) -> Dict[str, object]:
    text = str(input_data.get("text", ""))
    return {
        "voice": input_data.get("voice", "news_cn_female"),
        "audio_path": "mock_assets/avatar_voice.wav",
        "estimated_seconds": max(5, len(text) // 8),
    }


def execute(input: dict) -> dict:
    return execute_with_guard("tts_generate", input, _handler)
