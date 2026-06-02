from __future__ import annotations

from typing import Any, Dict

from core.models import ExecutionPlan, WorkflowFinalStatus
from workflows.base import BaseWorkflow


class MixedTopicPipeline(BaseWorkflow):
    def run(self, plan: ExecutionPlan, state: Dict[str, Any], auto_approve: bool = False):
        if state.get("stage_statuses", {}).get("plan") != "completed":
            while True:
                revision_note = state.get("revision_notes", {}).get("plan")
                director = self._run_agent(
                    "director_agent",
                    {
                        "request_text": plan.request_text,
                        "category": plan.category,
                        "revision_note": revision_note,
                    },
                )
                artifact = self.o.register_artifact(
                    plan.job_id,
                    "review_plan",
                    "review_plan.md",
                    self._render_review_plan(director, plan),
                    "director_agent",
                    "Director-level task plan for mixed topic",
                )
                self.o.append_artifact(state, artifact)
                self._record_skill_run(
                    state,
                    plan,
                    stage="plan",
                    skill_name=self._skill_name(plan.category, "plan", "workflow-planning"),
                    agent_name="director_agent",
                    payload={"request_text": plan.request_text, "category": plan.category},
                    artifact_paths=[artifact.path],
                )
                outcome = self._gate(
                    plan,
                    state,
                    "plan",
                    [artifact.path],
                    "Review the mixed-topic plan before content production begins.",
                    auto_approve,
                )
                if outcome == "retry":
                    continue
                if outcome:
                    return outcome
                break

        if state.get("stage_statuses", {}).get("content_pack") != "completed":
            while True:
                revision_note = state.get("revision_notes", {}).get("content_pack")
                military_editorial = self._run_agent(
                    "military_editor_agent",
                    {"request_text": plan.request_text, "revision_note": revision_note},
                )
                finance_editorial = self._run_agent(
                    "finance_editor_agent",
                    {"request_text": plan.request_text, "revision_note": revision_note},
                )
                research_sources = self.o.tools.execute("web_search", {"query": plan.request_text, "category": "mixed"})
                research = self._run_agent(
                    "researcher_agent",
                    {
                        "request_text": plan.request_text,
                        "category": "mixed",
                        "editorial_output": {
                            "military": military_editorial,
                            "finance": finance_editorial,
                        },
                        "revision_note": revision_note,
                    },
                )
                script = self._run_agent(
                    "scriptwriter_agent",
                    {
                        "request_text": plan.request_text,
                        "category": "military",
                        "editorial_output": military_editorial,
                        "research_output": research,
                        "revision_note": revision_note,
                    },
                )
                storyboard = self._run_agent(
                    "storyboard_agent",
                    {"request_text": plan.request_text, "script_output": script, "revision_note": revision_note},
                )
                research_artifact = self.o.register_artifact(
                    plan.job_id,
                    "research_brief",
                    "research_brief.md",
                    self._render_research_brief(research, research_sources),
                    "researcher_agent",
                    "Mixed-topic research brief",
                )
                script_artifact = self.o.register_artifact(
                    plan.job_id,
                    "script_outline",
                    "script_outline.md",
                    self._render_script_outline(military_editorial, script, "military")
                    + "\n## 财经补充视角\n"
                    + finance_editorial["macro_logic"]
                    + "\n",
                    "scriptwriter_agent",
                    "Mixed-topic script outline",
                )
                storyboard_artifact = self.o.register_artifact(
                    plan.job_id,
                    "storyboard",
                    "storyboard.md",
                    self._render_storyboard(storyboard),
                    "storyboard_agent",
                    "Mixed-topic storyboard",
                )
                for artifact in [research_artifact, script_artifact, storyboard_artifact]:
                    self.o.append_artifact(state, artifact)
                self._record_skill_run(
                    state,
                    plan,
                    stage="content_pack",
                    skill_name=self._skill_name(plan.category, "content_pack", "content-pack"),
                    agent_name="storyboard_agent",
                    payload={"request_text": plan.request_text, "category": plan.category},
                    artifact_paths=[
                        research_artifact.path,
                        script_artifact.path,
                        storyboard_artifact.path,
                    ],
                )
                outcome = self._gate(
                    plan,
                    state,
                    "content_pack",
                    [research_artifact.path, script_artifact.path, storyboard_artifact.path],
                    "Review the mixed-topic content pack before publishing.",
                    auto_approve,
                )
                if outcome == "retry":
                    continue
                if outcome:
                    return outcome
                break

        publish = self._run_agent(
            "publisher_agent",
            {"request_text": plan.request_text, "category": "military"},
        )
        publish_stub = self.o.tools.execute(
            "publish_output",
            {"job_id": plan.job_id, "platforms": ["wechat", "youtube"]},
        )
        publish_artifact = self.o.register_artifact(
            plan.job_id,
            "publish_pack",
            "publish_pack.md",
            self._render_publish_pack(publish, publish_stub),
            "publisher_agent",
            "Mixed-topic publish pack",
        )
        self.o.append_artifact(state, publish_artifact)
        self._record_skill_run(
            state,
            plan,
            stage="publish",
            skill_name=self._skill_name(plan.category, "publish", "publication-pack"),
            agent_name="publisher_agent",
            payload={"request_text": plan.request_text, "category": plan.category},
            artifact_paths=[publish_artifact.path],
        )
        self.o.mark_stage(state, "publish", "completed")
        state["status"] = WorkflowFinalStatus.COMPLETED.value
        self.o.save_state(plan.job_id, state)
        return self.o.build_result(
            plan=plan,
            state=state,
            final_status=WorkflowFinalStatus.COMPLETED.value,
            summary="Mixed-topic workflow completed.",
            next_actions=[f"Open {publish_artifact.path} to review the release package."],
        )


class SystemConfigWorkflow(BaseWorkflow):
    def run(self, plan: ExecutionPlan, state: Dict[str, Any], auto_approve: bool = False):
        artifact = self.o.register_artifact(
            plan.job_id,
            "system_task",
            "review_plan.md",
            "# System Task\n\n当前系统类任务在 MVP 中仅提供路由与占位说明。\n",
            "director_agent",
            "System placeholder output",
        )
        self.o.append_artifact(state, artifact)
        self.o.mark_stage(state, "publish", "completed")
        state["status"] = WorkflowFinalStatus.COMPLETED.value
        self.o.save_state(plan.job_id, state)
        return self.o.build_result(
            plan=plan,
            state=state,
            final_status=WorkflowFinalStatus.COMPLETED.value,
            summary="System-config task routed successfully to the placeholder workflow.",
            next_actions=["Implement the concrete system task in the next iteration."],
        )
