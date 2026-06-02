from pathlib import Path

from core.orchestrator import MediaOrchestrator


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_review_pause_and_resume(tmp_path):
    orchestrator = MediaOrchestrator(
        root_dir=PROJECT_ROOT,
        output_dir=tmp_path / "outputs",
        log_dir=tmp_path / "logs",
    )
    first = orchestrator.run_request("做一期南海局势节目", auto_approve=False)
    assert first.final_status == "needs_review"
    assert first.review_stage == "plan"

    orchestrator.submit_review_decision(first.job_id, "plan", "approve", revision=0)
    second = orchestrator.resume(first.job_id, auto_approve=False)
    assert second.final_status == "needs_review"
    assert second.review_stage == "content_pack"

    orchestrator.submit_review_decision(first.job_id, "content_pack", "approve", revision=0)
    final = orchestrator.resume(first.job_id, auto_approve=False)
    assert final.final_status == "completed"


def test_review_revise_creates_new_revision(tmp_path):
    orchestrator = MediaOrchestrator(
        root_dir=PROJECT_ROOT,
        output_dir=tmp_path / "outputs",
        log_dir=tmp_path / "logs",
    )
    first = orchestrator.run_request("做一期南海局势节目", auto_approve=False)
    orchestrator.submit_review_decision(first.job_id, "plan", "revise", note="开头冲突感更强一些", revision=0)
    second = orchestrator.resume(first.job_id, auto_approve=False)

    assert second.final_status == "needs_review"
    assert second.review_stage == "plan"
    assert (orchestrator.get_job_dir(first.job_id) / "reviews" / "plan_r1_ticket.yaml").exists()


def test_rwa_review_pause_and_resume(tmp_path):
    orchestrator = MediaOrchestrator(
        root_dir=PROJECT_ROOT,
        output_dir=tmp_path / "outputs",
        log_dir=tmp_path / "logs",
    )
    first = orchestrator.run_request("开始本周 RWA 研究流程", auto_approve=False)
    assert first.final_status == "needs_review"
    assert first.review_stage == "research_report_review"

    orchestrator.submit_review_decision(first.job_id, "research_report_review", "approve", revision=0)
    second = orchestrator.resume(first.job_id, auto_approve=False)
    assert second.final_status == "needs_review"
    assert second.review_stage == "content_pack_review"

    orchestrator.submit_review_decision(first.job_id, "content_pack_review", "approve", revision=0)
    final = orchestrator.resume(first.job_id, auto_approve=False)
    assert final.final_status == "completed"
