from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from zoneinfo import ZoneInfo

from core.logging_utils import load_json, load_yaml, write_json


WEEKDAY_ALIASES = {
    "mon": 0,
    "monday": 0,
    "周一": 0,
    "tue": 1,
    "tues": 1,
    "tuesday": 1,
    "周二": 1,
    "wed": 2,
    "wednesday": 2,
    "周三": 2,
    "thu": 3,
    "thur": 3,
    "thurs": 3,
    "thursday": 3,
    "周四": 3,
    "fri": 4,
    "friday": 4,
    "周五": 4,
    "sat": 5,
    "saturday": 5,
    "周六": 5,
    "sun": 6,
    "sunday": 6,
    "周日": 6,
    "周天": 6,
}


@dataclass
class DueResult:
    due: bool
    reason: str


class JobScheduler:
    def __init__(
        self,
        orchestrator,
        jobs_path: Optional[Path] = None,
        state_path: Optional[Path] = None,
    ) -> None:
        self.orchestrator = orchestrator
        root_dir = self.orchestrator.root_dir
        self.jobs_path = Path(jobs_path or root_dir / "scheduler" / "jobs.yaml")
        self.state_path = Path(state_path or self.orchestrator.output_dir / "_scheduler_state.json")

    def list_jobs(self) -> List[Dict[str, Any]]:
        jobs = self._load_jobs()
        state = self._load_state()
        output: List[Dict[str, Any]] = []
        for job in jobs:
            memory = state.get("jobs", {}).get(job["id"], {})
            output.append(
                {
                    "id": job["id"],
                    "name": job.get("name", job["id"]),
                    "enabled": bool(job.get("enabled", True)),
                    "schedule": job.get("schedule", {}),
                    "task_text": job.get("task", {}).get("text", ""),
                    "last_run_local_date": memory.get("last_run_local_date"),
                    "last_job_id": memory.get("last_job_id"),
                    "last_final_status": memory.get("last_final_status"),
                }
            )
        return output

    def run_due(self, now: Optional[datetime] = None) -> Dict[str, Any]:
        jobs = self._load_jobs()
        state = self._load_state()
        executed = []
        skipped = []
        for job in jobs:
            due, reason, local_now = self._is_due(job, state, now=now)
            if not due:
                skipped.append({"job_id": job["id"], "reason": reason})
                continue
            result = self._execute_job(job)
            local_date = local_now.date().isoformat()
            self._mark_run(
                state=state,
                job_id=job["id"],
                local_date=local_date,
                result=result,
            )
            executed.append(
                {
                    "job_id": job["id"],
                    "trigger_time": local_now.isoformat(),
                    "run_result": result,
                }
            )
        self._save_state(state)
        return {"executed": executed, "skipped": skipped, "executed_count": len(executed)}

    def run_job(self, job_id: str, force: bool = True, now: Optional[datetime] = None) -> Dict[str, Any]:
        jobs = self._load_jobs()
        state = self._load_state()
        target = None
        for job in jobs:
            if job["id"] == job_id:
                target = job
                break
        if target is None:
            raise ValueError(f"Unknown scheduler job: {job_id}")

        due, reason, local_now = self._is_due(target, state, now=now)
        if not force and not due:
            return {"executed": False, "reason": reason, "job_id": job_id}

        result = self._execute_job(target)
        self._mark_run(
            state=state,
            job_id=target["id"],
            local_date=local_now.date().isoformat(),
            result=result,
        )
        self._save_state(state)
        return {"executed": True, "job_id": job_id, "result": result, "reason": reason if not due else "due"}

    def _execute_job(self, job: Dict[str, Any]) -> Dict[str, Any]:
        task = job.get("task", {})
        result = self.orchestrator.run_request(
            text=str(task.get("text", "")).strip(),
            auto_approve=bool(task.get("auto_approve", True)),
            source=str(task.get("source", "scheduler")),
        )
        serialized = {
            "job_id": result.job_id,
            "category": result.category,
            "final_status": result.final_status,
            "summary": result.summary,
            "review_stage": result.review_stage,
        }
        return serialized

    def _is_due(
        self,
        job: Dict[str, Any],
        state: Dict[str, Any],
        now: Optional[datetime] = None,
    ) -> Tuple[bool, str, datetime]:
        enabled = bool(job.get("enabled", True))
        schedule = job.get("schedule", {})
        timezone_name = schedule.get("timezone", "Asia/Shanghai")
        local_now = self._resolve_now(timezone_name, now)
        if not enabled:
            return False, "job is disabled", local_now

        due_time = str(schedule.get("time", "00:00"))
        hour, minute = self._parse_hhmm(due_time)
        schedule_type = str(schedule.get("type", "daily")).strip().lower()

        if schedule_type == "weekly":
            raw_weekdays = schedule.get("weekdays", [])
            expected_days = {self._weekday_to_int(day) for day in raw_weekdays}
            if local_now.weekday() not in expected_days:
                return False, "today is not in configured weekdays", local_now
        elif schedule_type != "daily":
            return False, f"unsupported schedule type: {schedule_type}", local_now

        due_marker = local_now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if local_now < due_marker:
            return False, "not reached scheduled time yet", local_now

        memory = state.get("jobs", {}).get(job["id"], {})
        if memory.get("last_run_local_date") == local_now.date().isoformat():
            return False, "already executed today", local_now
        return True, "due", local_now

    @staticmethod
    def _resolve_now(timezone_name: str, now: Optional[datetime] = None) -> datetime:
        tz = ZoneInfo(timezone_name)
        if now is None:
            return datetime.now(tz)
        if now.tzinfo is None:
            return now.replace(tzinfo=tz)
        return now.astimezone(tz)

    @staticmethod
    def _parse_hhmm(value: str) -> Tuple[int, int]:
        parts = value.strip().split(":")
        if len(parts) != 2:
            raise ValueError(f"Invalid time format: {value}")
        hour = int(parts[0])
        minute = int(parts[1])
        if not (0 <= hour <= 23 and 0 <= minute <= 59):
            raise ValueError(f"Invalid time value: {value}")
        return hour, minute

    @staticmethod
    def _weekday_to_int(value: Any) -> int:
        key = str(value).strip().lower()
        if key not in WEEKDAY_ALIASES:
            raise ValueError(f"Unsupported weekday value: {value}")
        return WEEKDAY_ALIASES[key]

    def _load_jobs(self) -> List[Dict[str, Any]]:
        payload = load_yaml(self.jobs_path, default={"jobs": []})
        jobs = payload.get("jobs", [])
        if not isinstance(jobs, list):
            raise ValueError("scheduler/jobs.yaml must contain a top-level 'jobs' list")
        return [job for job in jobs if isinstance(job, dict)]

    def _load_state(self) -> Dict[str, Any]:
        return load_json(self.state_path, default={"jobs": {}})

    def _save_state(self, state: Dict[str, Any]) -> Path:
        return write_json(self.state_path, state)

    @staticmethod
    def _mark_run(
        state: Dict[str, Any],
        job_id: str,
        local_date: str,
        result: Dict[str, Any],
    ) -> None:
        bucket = state.setdefault("jobs", {}).setdefault(job_id, {})
        bucket["last_run_local_date"] = local_date
        bucket["last_job_id"] = result.get("job_id")
        bucket["last_final_status"] = result.get("final_status")
