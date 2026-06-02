from __future__ import annotations

from typing import Dict

from tools.base import execute_with_guard


def _handler(input_data: Dict[str, object]) -> Dict[str, object]:
    job_id = input_data.get("job_id", "demo")
    return {
        "job_id": job_id,
        "subtitle_file": f"mock_assets/{job_id}.srt",
        "style": "large_keyword_plus_full_caption",
    }


def execute(input: dict) -> dict:
    return execute_with_guard("subtitle_generate", input, _handler)
