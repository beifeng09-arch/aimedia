from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional

from core.models import ExecutionPlan, WorkflowFinalStatus


class BaseWorkflow:
    def __init__(self, orchestrator) -> None:
        self.o = orchestrator

    def _skill_name(self, category: str, stage: str, fallback: str) -> str:
        return self.o.skill_runner.resolve_skill_for_stage(category, stage) or fallback

    def _run_agent(self, agent_name: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        result = self.o.agent_runner.run(agent_name, payload)
        return result["output"]

    def _record_operator_log(
        self,
        state: Dict[str, Any],
        step_id: str,
        module_name: str,
        input_payload: Dict[str, Any],
        output_payload: Dict[str, Any],
        status: str,
        next_step: Optional[str],
    ) -> None:
        step_log = self._run_agent(
            "operator_agent",
            {
                "step_id": step_id,
                "module_name": module_name,
                "input": input_payload,
                "action": "execute_step",
                "output": output_payload,
                "status": status,
                "next_step": next_step,
            },
        )
        state.setdefault("step_logs", []).append(step_log)

    def _record_skill_run(
        self,
        state: Dict[str, Any],
        plan: ExecutionPlan,
        stage: str,
        skill_name: str,
        agent_name: str,
        payload: Dict[str, Any],
        artifact_paths: Iterable[str],
    ) -> None:
        skill_run = self.o.skill_runner.record_run(
            category=plan.category,
            job_id=plan.job_id,
            job_dir=self.o.get_job_dir(plan.job_id),
            stage=stage,
            skill_name=skill_name,
            agent_name=agent_name,
            payload=payload,
            output_paths=list(artifact_paths),
        )
        state.setdefault("skill_runs", []).append(skill_run)
        artifact = self.o.register_artifact(
            job_id=plan.job_id,
            artifact_type="skill_runs",
            filename="skill_runs.yaml",
            content={"job_id": plan.job_id, "skill_runs": state["skill_runs"]},
            producer="skill_runner",
            description="Explicit skill invocation log for the workflow",
        )
        self.o.append_artifact(state, artifact)

    def _gate(
        self,
        plan: ExecutionPlan,
        state: Dict[str, Any],
        stage: str,
        artifact_paths: Iterable[str],
        instructions: str,
        auto_approve: bool,
    ):
        revision = int(state.setdefault("stage_revisions", {}).get(stage, 0))
        self.o.request_review(
            job_id=plan.job_id,
            stage=stage,
            artifact_paths=list(artifact_paths),
            instructions=instructions,
            revision=revision,
        )
        decision = self.o.consume_decision(plan.job_id, stage, revision=revision)
        if auto_approve and decision.decision == "pending":
            self.o.submit_review_decision(
                job_id=plan.job_id,
                stage=stage,
                decision="approve",
                source="auto_approve",
                revision=revision,
            )
            decision = self.o.consume_decision(plan.job_id, stage, revision=revision)

        if decision.decision == "pending":
            state["status"] = WorkflowFinalStatus.NEEDS_REVIEW.value
            state["pending_review_stage"] = stage
            self.o.mark_stage(state, stage, "paused")
            self.o.save_state(plan.job_id, state)
            return self.o.build_result(
                plan=plan,
                state=state,
                final_status=WorkflowFinalStatus.NEEDS_REVIEW.value,
                summary=f"Workflow paused at {stage} review.",
                next_actions=[
                    f"Submit a review decision for stage `{stage}` revision `{revision}`",
                    f"Resume the workflow with `python3 main.py resume {plan.job_id}`",
                ],
                review_stage=stage,
            )

        if decision.decision == "approve":
            state["pending_review_stage"] = None
            self.o.mark_stage(state, stage, "completed")
            self.o.save_state(plan.job_id, state)
            return None

        if decision.decision == "revise":
            state["status"] = "revising"
            state["pending_review_stage"] = None
            state.setdefault("revision_notes", {})[stage] = decision.note or "请根据审核意见修订。"
            state["stage_revisions"][stage] = revision + 1
            self.o.mark_stage(state, stage, "pending")
            self.o.save_state(plan.job_id, state)
            return "retry"

        state["status"] = WorkflowFinalStatus.REJECTED.value
        self.o.mark_stage(state, stage, "rejected")
        self.o.save_state(plan.job_id, state)
        return self.o.build_result(
            plan=plan,
            state=state,
            final_status=WorkflowFinalStatus.REJECTED.value,
            summary=f"Workflow rejected at {stage}.",
            next_actions=["Adjust the request or restart a new job."],
            review_stage=stage,
        )

    @staticmethod
    def _bullet_lines(items: Iterable[str]) -> str:
        return "\n".join(f"- {item}" for item in items)

    def _render_review_plan(self, plan_output: Dict[str, Any], plan: ExecutionPlan) -> str:
        return f"""# Review Plan

- Job ID: `{plan.job_id}`
- Category: `{plan.category}`
- Request: {plan.request_text}
- Route Reason: {plan.route_reason}

## Task Goal
{plan_output["task_goal"]}

## Required Agents
{self._bullet_lines(plan_output["required_agents"])}

## Deliverables
{self._bullet_lines(plan_output["deliverables"])}

## Risk Points
{self._bullet_lines(plan_output["risk_points"])}

## Review Nodes
{self._bullet_lines(plan_output["review_nodes"])}
"""

    def _render_research_brief(self, research: Dict[str, Any], tool_result: Dict[str, Any]) -> str:
        facts = "\n".join(
            f"- {item['fact']} | 状态: {item['status']} | 可信度: {item['confidence']}"
            for item in research["key_facts"]
        )
        controversies = self._bullet_lines(research["controversies"])
        verify = self._bullet_lines(research["verification_questions"])
        angles = self._bullet_lines(research["writer_angles"])
        sources = "\n".join(
            f"- [{item['title']}]({item['url']})"
            for item in tool_result.get("data", {}).get("sources", [])
        )
        return f"""# Research Brief

## 研究主题
{research["research_topic"]}

## 背景摘要
{research["background_summary"]}

## 关键事实点
{facts}

## 争议点
{controversies}

## 待核验问题
{verify}

## 给编剧的建议角度
{angles}

## Mock Search Sources
{sources or "- 暂无"}
"""

    def _render_script_outline(self, editorial: Dict[str, Any], script: Dict[str, Any], category: str) -> str:
        if category == "finance":
            intro = f"## 节目主题\n{editorial['theme']}\n\n## 当期焦点\n{editorial['focus']}\n"
        else:
            structure = "\n".join(
                f"- {item['section']}：{item['point']}" for item in editorial["three_act_structure"]
            )
            intro = f"## 节目标题\n{editorial['title']}\n\n## 节目结构\n{structure}\n"
        sections = "\n".join(f"### {item['heading']}\n{item['summary']}" for item in script["sections"])
        subtitles = self._bullet_lines(script["subtitle_suggestions"])
        return f"""# Script Outline

{intro}
## 开头钩子
{script["hook"]}

## 正文提纲
{sections}

## 结尾收束
{script["closing"]}

## 屏幕字幕建议
{subtitles}

## 配音语气建议
{script["voice_tone"]}
"""

    def _render_storyboard(self, storyboard: Dict[str, Any], download_result: Optional[Dict[str, Any]] = None) -> str:
        rows = [
            "| 镜头号 | 时长 | 画面描述 | 素材类型 | 旁白 | 字幕 | 转场建议 |",
            "| --- | --- | --- | --- | --- | --- | --- |",
        ]
        for shot in storyboard["shots"]:
            rows.append(
                f"| {shot['shot_no']} | {shot['duration']} | {shot['visual']} | {shot['material_type']} | "
                f"{shot['narration']} | {shot['subtitle']} | {shot['transition']} |"
            )
        asset_lines = ""
        if download_result:
            asset_lines = "\n".join(
                f"- `{asset['name']}` -> `{asset['path']}`"
                for asset in download_result.get("data", {}).get("asset_bundle", [])
            )
        return "# Storyboard\n\n" + "\n".join(rows) + f"\n\n## 素材包建议\n{asset_lines or '- 暂无'}\n"

    def _render_avatar_script(
        self,
        avatar: Dict[str, Any],
        tts_result: Dict[str, Any],
        presenter_result: Dict[str, Any],
    ) -> str:
        breaks = self._bullet_lines(avatar["sentence_breaks"])
        emphasis = self._bullet_lines(avatar["emphasis_words"])
        scenes = self._bullet_lines(presenter_result.get("data", {}).get("scene_notes", []))
        return f"""# Avatar Script

## 数字人口播稿
{avatar["host_script"]}

## 分句断点
{breaks}

## 重音词
{emphasis}

## 语气建议
{avatar["tone"]}

## 主持风格
{avatar["style"]}

## TTS Mock
- 音频: `{tts_result.get("data", {}).get("audio_path", "")}`
- 预计时长: `{tts_result.get("data", {}).get("estimated_seconds", "")}` 秒

## 数字人 Mock
{scenes or "- 默认中景新闻口播"}
"""

    def _render_edit_plan(
        self,
        edit: Dict[str, Any],
        ffmpeg_result: Dict[str, Any],
        subtitle_result: Dict[str, Any],
    ) -> str:
        sequence = self._bullet_lines(edit["edit_sequence"])
        transitions = self._bullet_lines(edit["transitions"])
        return f"""# Edit Plan

## 输入素材清单
{self._bullet_lines(edit["input_assets"])}

## 剪辑顺序
{sequence}

## 字幕方案
{edit["subtitle_strategy"]}

## BGM 建议
{edit["bgm"]}

## 转场建议
{transitions}

## 导出参数
- Resolution: `{edit['export_settings']['resolution']}`
- FPS: `{edit['export_settings']['fps']}`
- Codec: `{edit['export_settings']['codec']}`

## Subtitle Mock
- 字幕文件: `{subtitle_result.get('data', {}).get('subtitle_file', '')}`

## FFmpeg Draft
- 逻辑命令: `{edit['draft_command']}`
- Mock 输出: `{ffmpeg_result.get('data', {}).get('command', '')}`
"""

    def _render_publish_pack(self, publish: Dict[str, Any], publish_tool_result: Dict[str, Any]) -> str:
        tags = self._bullet_lines(publish["tags"])
        platforms = self._bullet_lines(publish_tool_result.get("data", {}).get("platforms", []))
        return f"""# Publish Pack

## 抖音标题
{publish["douyin_title"]}

## 视频号标题
{publish["wechat_title"]}

## YouTube 标题
{publish["youtube_title"]}

## 简介文案
{publish["description"]}

## 标签
{tags}

## 封面文案
{publish["cover_copy"]}

## 发布时间建议
{publish["publish_time_suggestion"]}

## Publish Stub
{platforms}
"""
