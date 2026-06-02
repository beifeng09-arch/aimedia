from pathlib import Path

from core.logging_utils import load_yaml
from core.orchestrator import MediaOrchestrator


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_military_pipeline_auto_approve(tmp_path):
    orchestrator = MediaOrchestrator(
        root_dir=PROJECT_ROOT,
        output_dir=tmp_path / "outputs",
        log_dir=tmp_path / "logs",
    )
    result = orchestrator.run_request("做一期南海局势节目", auto_approve=True)
    job_dir = orchestrator.get_job_dir(result.job_id)

    assert result.final_status == "completed"
    assert (job_dir / "review_plan.md").exists()
    assert (job_dir / "research_brief.md").exists()
    assert (job_dir / "script_outline.md").exists()
    assert (job_dir / "storyboard.md").exists()
    assert (job_dir / "publish_pack.md").exists()
    assert (job_dir / "skill_runs.yaml").exists()
    assert "南海" in (job_dir / "publish_pack.md").read_text(encoding="utf-8")
    skill_runs = load_yaml(job_dir / "skill_runs.yaml")
    assert skill_runs["skill_runs"][0]["skill_name"] == "workflow-planning"
    assert skill_runs["skill_runs"][-1]["skill_name"] == "publication-pack"
