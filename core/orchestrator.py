from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from core.agent_runner import AgentRunner
from core.llm import LLMClient
from core.logging_utils import (
    append_json_line,
    configure_app_logging,
    ensure_directory,
    load_json,
    load_yaml,
    write_json,
    write_text,
    write_yaml,
)
from core.models import ArtifactEnvelope, ExecutionPlan, TaskCategory, WorkflowResult, to_serializable
from core.review import ReviewManager
from core.router import TaskRouter
from core.skill_runner import SkillRunner
from tools.registry import ToolRegistry


class MediaOrchestrator:
    def __init__(
        self,
        root_dir: Optional[Path] = None,
        output_dir: Optional[Path] = None,
        log_dir: Optional[Path] = None,
    ) -> None:
        self.root_dir = Path(root_dir or Path(__file__).resolve().parents[1])
        self.app_config = load_yaml(self.root_dir / "config" / "app.yaml")
        self.output_dir = self._resolve_path(
            output_dir,
            self.app_config.get("paths", {}).get("output_dir", "outputs"),
            env_key="MEDIA_AGENT_OUTPUT_DIR",
        )
        self.log_dir = self._resolve_path(
            log_dir,
            self.app_config.get("paths", {}).get("log_dir", "logs"),
            env_key="MEDIA_AGENT_LOG_DIR",
        )
        ensure_directory(self.output_dir)
        ensure_directory(self.log_dir)

        os.environ["MEDIA_AGENT_LOG_DIR"] = str(self.log_dir)
        self.logger = configure_app_logging(
            self.log_dir,
            self.app_config.get("logging", {}).get("app_log", "app.log"),
        )
        llm_cfg = self.app_config.get("llm", {})
        self.router = TaskRouter(
            self.root_dir,
            llm_client=LLMClient(
                provider=llm_cfg.get("provider", "mock"),
                model=llm_cfg.get("model", "mock-director-v1"),
            ),
        )
        self.agent_runner = AgentRunner(self.root_dir)
        review_channels = self.app_config.get("review", {}).get("channels", ["local_file"])
        self.review_manager = ReviewManager(self.output_dir, channels=review_channels)
        self.tools = ToolRegistry()
        self.skill_runner = SkillRunner(self.root_dir)

    def run_request(self, text: str, auto_approve: bool = False, source: str = "cli") -> WorkflowResult:
        category = self.router.classify_task(text)
        plan = self.router.build_execution_plan(category, text)
        return self.run_workflow(plan, auto_approve=auto_approve, source=source)

    def resume(self, job_id: str, auto_approve: bool = False) -> WorkflowResult:
        plan = self.load_plan(job_id)
        return self.run_workflow(plan, auto_approve=auto_approve, source="resume")

    def run_workflow(self, plan: ExecutionPlan, auto_approve: bool = False, source: str = "cli") -> WorkflowResult:
        self.initialize_job(plan, source=source)
        state = self.load_state(plan.job_id)
        pipeline_class = self._resolve_pipeline(plan.category)
        pipeline = pipeline_class(self)
        result = pipeline.run(plan=plan, state=state, auto_approve=auto_approve)
        self.save_log(to_serializable(result))
        return result

    def initialize_job(self, plan: ExecutionPlan, source: str = "cli") -> None:
        job_dir = self.get_job_dir(plan.job_id)
        ensure_directory(job_dir)
        request_path = job_dir / "request.yaml"
        execution_plan_path = job_dir / "execution_plan.yaml"
        state_path = job_dir / "state.yaml"
        if not request_path.exists():
            write_yaml(
                request_path,
                {
                    "job_id": plan.job_id,
                    "request_text": plan.request_text,
                    "category": plan.category,
                    "source": source,
                },
            )
        if not execution_plan_path.exists():
            write_yaml(execution_plan_path, to_serializable(plan))
        if not state_path.exists():
            initial_state = self._initial_state(plan, source)
            initial_state["artifacts"] = [
                {
                    "artifact_type": "request",
                    "path": str(request_path),
                    "producer": "system",
                    "schema_version": "1.0",
                    "description": "Original request payload",
                },
                {
                    "artifact_type": "execution_plan",
                    "path": str(execution_plan_path),
                    "producer": "director_agent",
                    "schema_version": "1.0",
                    "description": "Structured execution plan",
                },
            ]
            write_yaml(state_path, initial_state)

    def load_plan(self, job_id: str) -> ExecutionPlan:
        payload = load_yaml(self.get_job_dir(job_id) / "execution_plan.yaml")
        if not payload:
            raise FileNotFoundError(f"Missing execution plan for job {job_id}")
        return ExecutionPlan.from_dict(payload)

    def get_job_dir(self, job_id: str) -> Path:
        return self.output_dir / job_id

    def load_state(self, job_id: str) -> Dict[str, Any]:
        return load_yaml(self.get_job_dir(job_id) / "state.yaml")

    def save_state(self, job_id: str, state: Dict[str, Any]) -> Path:
        return write_yaml(self.get_job_dir(job_id) / "state.yaml", state)

    def load_result(self, job_id: str) -> Dict[str, Any]:
        return load_json(self.get_job_dir(job_id) / "result.json")

    def register_artifact(
        self,
        job_id: str,
        artifact_type: str,
        filename: str,
        content: Union[str, Dict[str, Any]],
        producer: str,
        description: str = "",
    ) -> ArtifactEnvelope:
        artifact_path = self.get_job_dir(job_id) / filename
        if filename.endswith(".yaml"):
            write_yaml(artifact_path, content if isinstance(content, dict) else {"content": content})
        elif filename.endswith(".json"):
            write_json(artifact_path, content if isinstance(content, dict) else {"content": content})
        else:
            write_text(artifact_path, content if isinstance(content, str) else str(content))
        return ArtifactEnvelope(
            artifact_type=artifact_type,
            path=str(artifact_path),
            producer=producer,
            description=description,
        )

    def append_artifact(self, state: Dict[str, Any], artifact: ArtifactEnvelope) -> None:
        artifacts = state.setdefault("artifacts", [])
        serialized = to_serializable(artifact)
        if serialized["path"] not in [item["path"] for item in artifacts]:
            artifacts.append(serialized)

    def mark_stage(self, state: Dict[str, Any], stage: str, status: str) -> None:
        state.setdefault("stage_statuses", {})[stage] = status
        state["current_stage"] = stage

    def request_review(
        self,
        job_id: str,
        stage: str,
        artifact_paths: List[str],
        instructions: str,
        revision: int = 0,
    ):
        return self.review_manager.request_review(
            job_id=job_id,
            stage=stage,
            artifact_paths=artifact_paths,
            instructions=instructions,
            revision=revision,
        )

    def submit_review_decision(
        self,
        job_id: str,
        stage: str,
        decision: str,
        note: str = "",
        source: str = "local_file",
        revision: int = 0,
    ) -> Path:
        return self.review_manager.submit_decision(
            job_id=job_id,
            stage=stage,
            decision=decision,
            note=note,
            source=source,
            revision=revision,
        )

    def consume_decision(self, job_id: str, stage: str, revision: int = 0):
        return self.review_manager.consume_decision(job_id=job_id, stage=stage, revision=revision)

    def save_log(self, result: Dict[str, Any]) -> Path:
        job_id = result["job_id"]
        result_path = self.get_job_dir(job_id) / "result.json"
        write_json(result_path, result)
        workflow_log = self.log_dir / self.app_config.get("logging", {}).get("workflow_log", "workflows.log")
        append_json_line(workflow_log, result)
        return result_path

    def get_job_snapshot(self, job_id: str) -> Dict[str, Any]:
        job_dir = self.get_job_dir(job_id)
        if not job_dir.exists():
            raise FileNotFoundError(f"Unknown job_id: {job_id}")
        request_payload = load_yaml(job_dir / "request.yaml")
        plan_payload = load_yaml(job_dir / "execution_plan.yaml")
        state_payload = load_yaml(job_dir / "state.yaml")
        result_payload = load_json(job_dir / "result.json")
        reviews_dir = job_dir / "reviews"
        review_files = sorted(str(path) for path in reviews_dir.glob("*")) if reviews_dir.exists() else []
        return {
            "job_id": job_id,
            "request": request_payload,
            "plan": plan_payload,
            "state": state_payload,
            "result": result_payload,
            "review_files": review_files,
            "artifacts": state_payload.get("artifacts", []),
        }

    def list_jobs(self, limit: int = 20) -> List[Dict[str, Any]]:
        if not self.output_dir.exists():
            return []
        items = []
        for job_dir in sorted(
            [path for path in self.output_dir.iterdir() if path.is_dir()],
            key=lambda path: path.stat().st_mtime,
            reverse=True,
        )[:limit]:
            request_payload = load_yaml(job_dir / "request.yaml")
            state_payload = load_yaml(job_dir / "state.yaml")
            result_payload = load_json(job_dir / "result.json")
            items.append(
                {
                    "job_id": job_dir.name,
                    "category": request_payload.get("category"),
                    "request_text": request_payload.get("request_text"),
                    "status": state_payload.get("status"),
                    "current_stage": state_payload.get("current_stage"),
                    "pending_review_stage": state_payload.get("pending_review_stage"),
                    "final_status": result_payload.get("final_status"),
                }
            )
        return items

    def build_result(
        self,
        plan: ExecutionPlan,
        state: Dict[str, Any],
        final_status: str,
        summary: str,
        next_actions: Optional[List[str]] = None,
        review_stage: Optional[str] = None,
        errors: Optional[List[str]] = None,
    ) -> WorkflowResult:
        return WorkflowResult(
            job_id=plan.job_id,
            category=plan.category,
            final_status=final_status,
            artifacts=[ArtifactEnvelope.from_dict(item) for item in state.get("artifacts", [])],
            logs=[str(self.log_dir / self.app_config.get("logging", {}).get("workflow_log", "workflows.log"))],
            next_actions=next_actions or [],
            summary=summary,
            review_stage=review_stage,
            errors=errors or [],
        )

    def _resolve_pipeline(self, category: str):
        if category == TaskCategory.MILITARY.value:
            from workflows.southeast_military_pipeline import SoutheastMilitaryPipeline

            return SoutheastMilitaryPipeline
        if category == TaskCategory.FINANCE.value:
            from workflows.crypto_finance_pipeline import CryptoFinancePipeline

            return CryptoFinancePipeline
        if category == TaskCategory.RWA.value:
            from workflows.rwa_weekly_deep_research_pipeline import RWAWeeklyDeepResearchPipeline

            return RWAWeeklyDeepResearchPipeline
        if category == TaskCategory.MIXED.value:
            from workflows.mixed_topic_pipeline import MixedTopicPipeline

            return MixedTopicPipeline
        from workflows.mixed_topic_pipeline import SystemConfigWorkflow

        return SystemConfigWorkflow

    def _resolve_path(self, explicit: Optional[Path], config_value: str, env_key: str) -> Path:
        if explicit:
            return Path(explicit)
        value = os.getenv(env_key)
        if value:
            return Path(value)
        return self.root_dir / config_value

    @staticmethod
    def _initial_state(plan: ExecutionPlan, source: str) -> Dict[str, Any]:
        stage_statuses = {}
        for step in plan.steps:
            stage_statuses.setdefault(step.step_id, "pending")
            if step.review_stage:
                stage_statuses.setdefault(step.review_stage, "pending")
        for review_point in plan.review_points:
            stage_statuses.setdefault(review_point, "pending")
        if "publish" not in stage_statuses:
            stage_statuses["publish"] = "pending"

        stage_revisions = {review_point: 0 for review_point in plan.review_points}
        first_stage = plan.steps[0].step_id if plan.steps else "plan"
        return {
            "job_id": plan.job_id,
            "category": plan.category,
            "source": source,
            "status": "running",
            "current_stage": first_stage,
            "stage_statuses": stage_statuses,
            "stage_revisions": stage_revisions,
            "revision_notes": {},
            "artifacts": [],
        }
