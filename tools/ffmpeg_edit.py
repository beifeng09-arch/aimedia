from __future__ import annotations

from typing import Dict

from tools.base import execute_with_guard


def _handler(input_data: Dict[str, object]) -> Dict[str, object]:
    job_id = input_data.get("job_id", "demo")
    preset = input_data.get("template", "mvp_preview")
    return {
        "job_id": job_id,
        "preset": preset,
        "command": f"ffmpeg -i intro.mp4 -i body.mp4 -filter_complex '[0:v][1:v]concat=n=2:v=1:a=0' outputs/{job_id}/preview.mp4",
        "output_path": f"outputs/{job_id}/preview.mp4",
    }


def execute(input: dict) -> dict:
    return execute_with_guard("ffmpeg_edit", input, _handler)
