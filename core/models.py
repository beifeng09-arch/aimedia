from __future__ import annotations

from dataclasses import asdict, dataclass, field, is_dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


class TaskCategory(str, Enum):
    MILITARY = "military"
    FINANCE = "finance"
    RWA = "rwa"
    MIXED = "mixed"
    SYSTEM = "system"


class StepStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    PAUSED = "paused"
    FAILED = "failed"
    SKIPPED = "skipped"


class ReviewDecisionType(str, Enum):
    PENDING = "pending"
    APPROVE = "approve"
    REVISE = "revise"
    REJECT = "reject"


class WorkflowFinalStatus(str, Enum):
    COMPLETED = "completed"
    NEEDS_REVIEW = "needs_review"
    REJECTED = "rejected"
    FAILED = "failed"


@dataclass
class StepPlan:
    step_id: str
    module_name: str
    agent_name: str
    action: str
    expected_artifacts: List[str]
    status: str = StepStatus.PENDING.value
    review_stage: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StepPlan":
        return cls(
            step_id=data["step_id"],
            module_name=data["module_name"],
            agent_name=data["agent_name"],
            action=data["action"],
            expected_artifacts=list(data.get("expected_artifacts", [])),
            status=data.get("status", StepStatus.PENDING.value),
            review_stage=data.get("review_stage"),
        )


@dataclass
class ExecutionPlan:
    job_id: str
    category: str
    request_text: str
    workflow_name: str
    template_name: str
    route_reason: str
    steps: List[StepPlan]
    review_points: List[str]
    status: str = StepStatus.PENDING.value
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExecutionPlan":
        return cls(
            job_id=data["job_id"],
            category=data["category"],
            request_text=data["request_text"],
            workflow_name=data["workflow_name"],
            template_name=data["template_name"],
            route_reason=data["route_reason"],
            steps=[StepPlan.from_dict(step) for step in data.get("steps", [])],
            review_points=list(data.get("review_points", [])),
            status=data.get("status", StepStatus.PENDING.value),
            created_at=data.get("created_at", datetime.utcnow().isoformat()),
            metadata=dict(data.get("metadata", {})),
        )


@dataclass
class ArtifactEnvelope:
    artifact_type: str
    path: str
    producer: str
    schema_version: str = "1.0"
    description: str = ""

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ArtifactEnvelope":
        return cls(
            artifact_type=data["artifact_type"],
            path=data["path"],
            producer=data["producer"],
            schema_version=data.get("schema_version", "1.0"),
            description=data.get("description", ""),
        )


@dataclass
class WorkflowResult:
    job_id: str
    category: str
    final_status: str
    artifacts: List[ArtifactEnvelope]
    logs: List[str]
    next_actions: List[str]
    summary: str = ""
    review_stage: Optional[str] = None
    errors: List[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WorkflowResult":
        return cls(
            job_id=data["job_id"],
            category=data["category"],
            final_status=data["final_status"],
            artifacts=[ArtifactEnvelope.from_dict(item) for item in data.get("artifacts", [])],
            logs=list(data.get("logs", [])),
            next_actions=list(data.get("next_actions", [])),
            summary=data.get("summary", ""),
            review_stage=data.get("review_stage"),
            errors=list(data.get("errors", [])),
        )


@dataclass
class ReviewTicket:
    job_id: str
    stage: str
    revision: int
    artifact_paths: List[str]
    channels: List[str]
    status: str = ReviewDecisionType.PENDING.value
    instructions: str = ""
    ticket_path: str = ""
    decision_path: str = ""


@dataclass
class ReviewDecision:
    stage: str
    revision: int
    decision: str
    note: str = ""
    source: str = "local_file"
    decided_at: Optional[str] = None


def to_serializable(value: Any) -> Any:
    if is_dataclass(value):
        return to_serializable(asdict(value))
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {key: to_serializable(item) for key, item in value.items()}
    if isinstance(value, list):
        return [to_serializable(item) for item in value]
    return value
