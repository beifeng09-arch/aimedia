from pathlib import Path

from core.logging_utils import load_yaml
from core.orchestrator import MediaOrchestrator


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_mixed_workflow_uses_shared_skill_registry(tmp_path):
    orchestrator = MediaOrchestrator(
        root_dir=PROJECT_ROOT,
        output_dir=tmp_path / "outputs",
        log_dir=tmp_path / "logs",
    )
    result = orchestrator.run_request("做一期地缘经济与比特币联动专题", auto_approve=True)
    job_dir = orchestrator.get_job_dir(result.job_id)
    skill_runs = load_yaml(job_dir / "skill_runs.yaml")

    assert result.final_status == "completed"
    assert skill_runs["skill_runs"][0]["skill_name"] == "workflow-planning"
    assert skill_runs["skill_runs"][-1]["skill_name"] == "publication-pack"
