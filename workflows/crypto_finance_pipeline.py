from __future__ import annotations

from typing import Any, Dict

from core.models import ExecutionPlan, WorkflowFinalStatus
from workflows.base import BaseWorkflow


class CryptoFinancePipeline(BaseWorkflow):
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
                    job_id=plan.job_id,
                    artifact_type="review_plan",
                    filename="review_plan.md",
                    content=self._render_review_plan(director, plan),
                    producer="director_agent",
                    description="Director-level task plan and review checklist",
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
                self._record_operator_log(
                    state,
                    step_id="plan",
                    module_name="planning",
                    input_payload={"request_text": plan.request_text},
                    output_payload=director,
                    status="completed",
                    next_step="editorial",
                )
                outcome = self._gate(
                    plan,
                    state,
                    "plan",
                    [artifact.path],
                    "Review the finance episode plan and approve before content production begins.",
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
                editorial = self._run_agent(
                    "finance_editor_agent",
                    {"request_text": plan.request_text, "revision_note": revision_note},
                )
                research_sources = self.o.tools.execute(
                    "web_search",
                    {"query": plan.request_text, "category": plan.category},
                )
                research = self._run_agent(
                    "researcher_agent",
                    {
                        "request_text": plan.request_text,
                        "category": plan.category,
                        "editorial_output": editorial,
                        "revision_note": revision_note,
                    },
                )
                script = self._run_agent(
                    "scriptwriter_agent",
                    {
                        "request_text": plan.request_text,
                        "category": plan.category,
                        "editorial_output": editorial,
                        "research_output": research,
                        "revision_note": revision_note,
                    },
                )
                avatar = self._run_agent(
                    "avatar_host_agent",
                    {
                        "request_text": plan.request_text,
                        "script_output": script,
                        "revision_note": revision_note,
                    },
                )
                tts_result = self.o.tools.execute(
                    "tts_generate",
                    {"text": avatar["host_script"], "voice": "news_cn_female"},
                )
                presenter_result = self.o.tools.execute(
                    "avatar_presenter",
                    {"style": avatar["style"]},
                )
                subtitle_result = self.o.tools.execute("subtitle_generate", {"job_id": plan.job_id})
                transcript_result = self.o.tools.execute(
                    "transcript",
                    {"source": tts_result.get("data", {}).get("audio_path", "mock_assets/avatar_voice.wav")},
                )
                ffmpeg_result = self.o.tools.execute(
                    "ffmpeg_edit",
                    {"job_id": plan.job_id, "template": "finance_weekly"},
                )
                edit_plan = self._run_agent(
                    "editor_agent",
                    {
                        "request_text": plan.request_text,
                        "avatar_output": avatar,
                        "revision_note": revision_note,
                    },
                )

                research_artifact = self.o.register_artifact(
                    plan.job_id,
                    "research_brief",
                    "research_brief.md",
                    self._render_research_brief(research, research_sources),
                    "researcher_agent",
                    "Structured research brief",
                )
                script_artifact = self.o.register_artifact(
                    plan.job_id,
                    "script_outline",
                    "script_outline.md",
                    self._render_script_outline(editorial, script, plan.category),
                    "scriptwriter_agent",
                    "Script outline for the finance episode",
                )
                avatar_artifact = self.o.register_artifact(
                    plan.job_id,
                    "avatar_script",
                    "avatar_script.md",
                    self._render_avatar_script(avatar, tts_result, presenter_result),
                    "avatar_host_agent",
                    "Digital presenter delivery script",
                )
                edit_artifact = self.o.register_artifact(
                    plan.job_id,
                    "edit_plan",
                    "edit_plan.md",
                    self._render_edit_plan(edit_plan, ffmpeg_result, subtitle_result)
                    + f"\n## Mock Transcript\n- 段落数: {len(transcript_result.get('data', {}).get('segments', []))}\n",
                    "editor_agent",
                    "Draft edit plan with tool stubs",
                )
                for artifact in [research_artifact, script_artifact, avatar_artifact, edit_artifact]:
                    self.o.append_artifact(state, artifact)
                self._record_skill_run(
                    state,
                    plan,
                    stage="content_pack",
                    skill_name=self._skill_name(plan.category, "content_pack", "content-pack"),
                    agent_name="editor_agent",
                    payload={"request_text": plan.request_text, "category": plan.category},
                    artifact_paths=[
                        research_artifact.path,
                        script_artifact.path,
                        avatar_artifact.path,
                        edit_artifact.path,
                    ],
                )
                self._record_operator_log(
                    state,
                    step_id="content_pack",
                    module_name="content_production",
                    input_payload={"request_text": plan.request_text},
                    output_payload={
                        "editorial": editorial,
                        "research": research,
                        "script": script,
                        "avatar": avatar,
                        "edit_plan": edit_plan,
                    },
                    status="completed",
                    next_step="publish",
                )
                outcome = self._gate(
                    plan,
                    state,
                    "content_pack",
                    [
                        research_artifact.path,
                        script_artifact.path,
                        avatar_artifact.path,
                        edit_artifact.path,
                    ],
                    "Review the research, script, avatar script, and edit plan before publishing.",
                    auto_approve,
                )
                if outcome == "retry":
                    continue
                if outcome:
                    return outcome
                break

        publish = self._run_agent(
            "publisher_agent",
            {"request_text": plan.request_text, "category": plan.category},
        )
        publish_stub = self.o.tools.execute(
            "publish_output",
            {"job_id": plan.job_id, "platforms": ["douyin", "wechat", "youtube"]},
        )
        publish_artifact = self.o.register_artifact(
            plan.job_id,
            "publish_pack",
            "publish_pack.md",
            self._render_publish_pack(publish, publish_stub),
            "publisher_agent",
            "Platform-ready publish copy",
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
        self._record_operator_log(
            state,
            step_id="publish",
            module_name="publishing",
            input_payload={"request_text": plan.request_text},
            output_payload=publish,
            status="completed",
            next_step=None,
        )
        self.o.mark_stage(state, "publish", "completed")
        state["status"] = WorkflowFinalStatus.COMPLETED.value
        self.o.save_state(plan.job_id, state)
        return self.o.build_result(
            plan=plan,
            state=state,
            final_status=WorkflowFinalStatus.COMPLETED.value,
            summary="Finance workflow completed with planning, research, script, avatar script, and publish pack.",
            next_actions=[f"Open {publish_artifact.path} to review the release package."],
        )
