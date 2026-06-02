from __future__ import annotations

from typing import Dict

from tools.base import execute_with_guard


def _handler(input_data: Dict[str, object]) -> Dict[str, object]:
    job_id = input_data.get("job_id", "demo")
    platforms = input_data.get("platforms", ["wechat"])
    return {
        "job_id": job_id,
        "platforms": platforms,
        "status": "prepared",
        "package_id": f"mock-publish-{job_id}",
    }


def execute(input: dict) -> dict:
    return execute_with_guard("publish_output", input, _handler)
