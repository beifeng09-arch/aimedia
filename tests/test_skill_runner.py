from pathlib import Path

from core.skill_runner import SkillRunner


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_skill_runner_resolves_rwa_stage_skills():
    runner = SkillRunner(PROJECT_ROOT)
    assert runner.resolve_skill_for_stage("rwa", "news_digest") == "rwa-news-research"
    assert runner.resolve_skill_for_stage("rwa", "macro_context") == "cross-market-context"
    assert runner.resolve_skill_for_stage("rwa", "technical_report") == "market-technical-analysis"
    assert runner.resolve_skill_for_stage("rwa", "research_report") == "research-report-writer"
    assert runner.resolve_skill_for_stage("rwa", "content_pack") == "content-director-pack"


def test_skill_runner_loads_skill_metadata():
    runner = SkillRunner(PROJECT_ROOT)
    skill = runner.get_skill("research-report-writer")
    record = runner.record_run(
        category="rwa",
        job_id="rwa-demo-001",
        job_dir=PROJECT_ROOT / "outputs" / "rwa-demo-001",
        stage="research_report",
        skill_name="research-report-writer",
        agent_name="chief_strategist_agent",
        payload={"request_text": "做本周 RWA 深度研究"},
        output_paths=["/tmp/research_report.md"],
    )
    assert skill["path"] == "skills/research-report-writer"
    assert record["display_name"] == "Research Report Writer"
    assert record["skill_name"] == "research-report-writer"
