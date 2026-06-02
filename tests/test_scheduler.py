from datetime import datetime
from pathlib import Path

from core.orchestrator import MediaOrchestrator
from scheduler.scheduler import JobScheduler


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _write_jobs(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        """jobs:
  - id: daily_test_job
    name: Daily Test Job
    enabled: true
    schedule:
      type: daily
      time: "09:00"
      timezone: "Asia/Shanghai"
    task:
      text: 做一期南海局势节目
      auto_approve: true
      source: scheduler_test
  - id: weekly_test_job
    name: Weekly Test Job
    enabled: true
    schedule:
      type: weekly
      weekdays: [Sun]
      time: "20:00"
      timezone: "Asia/Shanghai"
    task:
      text: 做一期比特币周报
      auto_approve: true
      source: scheduler_test
  - id: rwa_weekly_job
    name: RWA Weekly Job
    enabled: true
    schedule:
      type: weekly
      weekdays: [Sat]
      time: "09:00"
      timezone: "Asia/Shanghai"
    task:
      text: 做本周 RWA 深度研究
      auto_approve: true
      source: scheduler_test
""",
        encoding="utf-8",
    )


def test_scheduler_run_due_once_per_day(tmp_path):
    jobs_path = tmp_path / "scheduler" / "jobs.yaml"
    _write_jobs(jobs_path)
    orchestrator = MediaOrchestrator(
        root_dir=PROJECT_ROOT,
        output_dir=tmp_path / "outputs",
        log_dir=tmp_path / "logs",
    )
    scheduler = JobScheduler(
        orchestrator=orchestrator,
        jobs_path=jobs_path,
        state_path=tmp_path / "outputs" / "_scheduler_state.json",
    )
    now = datetime.fromisoformat("2026-03-23T09:30:00+08:00")
    first = scheduler.run_due(now=now)
    assert first["executed_count"] == 1
    assert first["executed"][0]["job_id"] == "daily_test_job"
    assert first["executed"][0]["run_result"]["final_status"] == "completed"

    second = scheduler.run_due(now=now)
    assert second["executed_count"] == 0
    reasons = {item["job_id"]: item["reason"] for item in second["skipped"]}
    assert reasons["daily_test_job"] == "already executed today"


def test_scheduler_run_job_force_and_respect_time(tmp_path):
    jobs_path = tmp_path / "scheduler" / "jobs.yaml"
    _write_jobs(jobs_path)
    orchestrator = MediaOrchestrator(
        root_dir=PROJECT_ROOT,
        output_dir=tmp_path / "outputs",
        log_dir=tmp_path / "logs",
    )
    scheduler = JobScheduler(
        orchestrator=orchestrator,
        jobs_path=jobs_path,
        state_path=tmp_path / "outputs" / "_scheduler_state.json",
    )
    early = datetime.fromisoformat("2026-03-23T08:00:00+08:00")
    not_due = scheduler.run_job("daily_test_job", force=False, now=early)
    assert not_due["executed"] is False
    assert "not reached scheduled time yet" in not_due["reason"]

    forced = scheduler.run_job("daily_test_job", force=True, now=early)
    assert forced["executed"] is True
    assert forced["result"]["final_status"] == "completed"


def test_scheduler_run_rwa_weekly_job(tmp_path):
    jobs_path = tmp_path / "scheduler" / "jobs.yaml"
    _write_jobs(jobs_path)
    orchestrator = MediaOrchestrator(
        root_dir=PROJECT_ROOT,
        output_dir=tmp_path / "outputs",
        log_dir=tmp_path / "logs",
    )
    scheduler = JobScheduler(
        orchestrator=orchestrator,
        jobs_path=jobs_path,
        state_path=tmp_path / "outputs" / "_scheduler_state.json",
    )
    due_time = datetime.fromisoformat("2026-03-28T09:05:00+08:00")
    result = scheduler.run_job("rwa_weekly_job", force=False, now=due_time)
    assert result["executed"] is True
    assert result["result"]["category"] == "rwa"
    assert result["result"]["final_status"] == "completed"
