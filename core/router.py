from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from uuid import uuid4

from core.llm import LLMClient
from core.logging_utils import load_yaml
from core.models import ExecutionPlan, StepPlan, TaskCategory


class TaskRouter:
    def __init__(self, root_dir: Path, llm_client: Optional[LLMClient] = None) -> None:
        self.root_dir = Path(root_dir)
        self.routing_config = load_yaml(self.root_dir / "config" / "routing.yaml")
        self.workflow_config = load_yaml(self.root_dir / "config" / "workflows.yaml")
        llm_section = self.routing_config.get("llm_classifier", {})
        self.llm_client = llm_client or LLMClient(provider="mock")
        self.llm_enabled = bool(llm_section.get("enabled", False))

    def classify_task(self, text: str) -> TaskCategory:
        category, _ = self._route_reason(text)
        return category

    def build_execution_plan(self, category: TaskCategory, text: str) -> ExecutionPlan:
        category_key = category.value
        workflow_map = self.routing_config.get("workflow_map", {})
        workflow_name = workflow_map.get(category_key, "system_config_workflow")
        workflow_bundle = self.workflow_config.get("workflows", {}).get(category_key, {})
        steps = [
            StepPlan(
                step_id=step["id"],
                module_name=step["module"],
                agent_name=step["agent"],
                action=step["action"],
                expected_artifacts=list(step.get("produces", [])),
                review_stage=step.get("review_stage"),
            )
            for step in workflow_bundle.get("steps", [])
        ]
        _, route_reason = self._route_reason(text)
        return ExecutionPlan(
            job_id=self._build_job_id(category_key),
            category=category_key,
            request_text=text,
            workflow_name=workflow_name,
            template_name=workflow_bundle.get("template", ""),
            route_reason=route_reason,
            steps=steps,
            review_points=list(workflow_bundle.get("review_points", [])),
            metadata={"router_strategy": "rules_then_prompt"},
        )

    def _route_reason(self, text: str) -> Tuple[TaskCategory, str]:
        categories = self.routing_config.get("categories", {})
        lowered = text.lower()
        scores: Dict[str, int] = defaultdict(int)
        matches: Dict[str, List[str]] = defaultdict(list)

        for category, payload in categories.items():
            for keyword in payload.get("keywords", []):
                if keyword.lower() in lowered:
                    scores[category] += 1
                    matches[category].append(keyword)

        if scores.get("system", 0) > 0 and scores["system"] >= max(scores.values() or [0]):
            return TaskCategory.SYSTEM, f"Matched system keywords: {matches['system']}"

        if scores.get("military", 0) > 0 and scores.get("finance", 0) > 0:
            reason = (
                f"Matched both military {matches['military']} and finance {matches['finance']} keywords"
            )
            return TaskCategory.MIXED, reason

        if scores.get("mixed", 0) > 0:
            return TaskCategory.MIXED, f"Matched mixed-topic keywords: {matches['mixed']}"

        best_category = None
        best_score = -1
        for category, score in scores.items():
            if score > best_score:
                best_category = category
                best_score = score

        if best_category and best_score > 0:
            return TaskCategory(best_category), f"Matched keywords: {matches[best_category]}"

        if self.llm_enabled:
            llm_guess = self.llm_client.classify_task(text, categories)
            if llm_guess:
                return TaskCategory(llm_guess), f"LLM classifier fallback selected {llm_guess}"

        fallback = self._fallback_category(text)
        return fallback, f"No explicit rule match. Fallback routed to {fallback.value}"

    @staticmethod
    def _build_job_id(category: str) -> str:
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        return f"{category}-{timestamp}-{uuid4().hex[:6]}"

    @staticmethod
    def _fallback_category(text: str) -> TaskCategory:
        lowered = text.lower()
        if any(
            token in lowered
            for token in [
                "rwa",
                "real world assets",
                "资产上链",
                "现实世界资产",
                "tokenized",
                "代币化国债",
            ]
        ):
            return TaskCategory.RWA
        if any(token in lowered for token in ["比特币", "btc", "eth", "周报", "行情"]):
            return TaskCategory.FINANCE
        if any(token in lowered for token in ["配置", "系统", "工作流", "接入"]):
            return TaskCategory.SYSTEM
        return TaskCategory.MILITARY
