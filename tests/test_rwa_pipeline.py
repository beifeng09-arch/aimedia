from pathlib import Path

from core.logging_utils import load_yaml
from core.orchestrator import MediaOrchestrator


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_rwa_pipeline_auto_approve(tmp_path):
    orchestrator = MediaOrchestrator(
        root_dir=PROJECT_ROOT,
        output_dir=tmp_path / "outputs",
        log_dir=tmp_path / "logs",
    )
    result = orchestrator.run_request("做本周 RWA 深度研究", auto_approve=True)
    job_dir = orchestrator.get_job_dir(result.job_id)

    assert result.final_status == "completed"
    assert (job_dir / "review_plan.md").exists()
    assert (job_dir / "news_digest.md").exists()
    assert (job_dir / "macro_context.md").exists()
    assert (job_dir / "technical_report.md").exists()
    assert (job_dir / "research_report.md").exists()
    assert (job_dir / "article_draft.md").exists()
    assert (job_dir / "script_outline.md").exists()
    assert (job_dir / "material_list.md").exists()
    assert (job_dir / "skill_runs.yaml").exists()
    assert "RWA" in (job_dir / "research_report.md").read_text(encoding="utf-8")
    skill_runs = load_yaml(job_dir / "skill_runs.yaml")
    assert [item["skill_name"] for item in skill_runs["skill_runs"]] == [
        "workflow-planning",
        "rwa-news-research",
        "cross-market-context",
        "market-technical-analysis",
        "research-report-writer",
        "content-director-pack",
        "content-director-pack",
    ]
