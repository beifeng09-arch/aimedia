from __future__ import annotations

from typing import Any, Dict

from core.models import ExecutionPlan, WorkflowFinalStatus
from workflows.base import BaseWorkflow


class RWAWeeklyDeepResearchPipeline(BaseWorkflow):
    def _skill_name(self, category: str, stage: str, fallback: str) -> str:
        return self.o.skill_runner.resolve_skill_for_stage(category, stage) or fallback

    def run(self, plan: ExecutionPlan, state: Dict[str, Any], auto_approve: bool = False):
        if state.get("stage_statuses", {}).get("review_plan") != "completed":
            revision_note = state.get("revision_notes", {}).get("review_plan")
            director = self._run_agent(
                "rwa_research_director_agent",
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
                content=self._render_rwa_review_plan(director, plan),
                producer="rwa_research_director_agent",
                description="Weekly RWA research plan and scope definition",
            )
            self.o.append_artifact(state, artifact)
            self._record_skill_run(
                state,
                plan,
                stage="review_plan",
                skill_name=self._skill_name("rwa", "review_plan", "workflow-planning"),
                agent_name="rwa_research_director_agent",
                payload={"request_text": plan.request_text, "category": plan.category},
                artifact_paths=[artifact.path],
            )
            self._record_operator_log(
                state,
                step_id="review_plan",
                module_name="planning",
                input_payload={"request_text": plan.request_text},
                output_payload=director,
                status="completed",
                next_step="news_digest",
            )
            self.o.mark_stage(state, "review_plan", "completed")
            self.o.save_state(plan.job_id, state)

        if state.get("stage_statuses", {}).get("news_digest") != "completed":
            news_payload = {
                "request_text": plan.request_text,
                "revision_note": state.get("revision_notes", {}).get("news_digest"),
            }
            news_sources = self.o.tools.execute(
                "web_search",
                {"query": f"{plan.request_text} RWA news weekly", "category": plan.category},
            )
            news = self._run_agent(
                "rwa_news_researcher_agent",
                {
                    **news_payload,
                    "news_sources": news_sources,
                },
            )
            artifact = self.o.register_artifact(
                plan.job_id,
                "news_digest",
                "news_digest.md",
                self._render_news_digest(news, news_sources),
                "rwa_news_researcher_agent",
                "Weekly RWA news digest",
            )
            self.o.append_artifact(state, artifact)
            self._record_skill_run(
                state,
                plan,
                stage="news_digest",
                skill_name=self._skill_name("rwa", "news_digest", "rwa-news-research"),
                agent_name="rwa_news_researcher_agent",
                payload={**news_payload, "news_sources": True},
                artifact_paths=[artifact.path],
            )
            self._record_operator_log(
                state,
                step_id="news_digest",
                module_name="research",
                input_payload={"request_text": plan.request_text},
                output_payload=news,
                status="completed",
                next_step="macro_context",
            )
            self.o.mark_stage(state, "news_digest", "completed")
            self.o.save_state(plan.job_id, state)

        if state.get("stage_statuses", {}).get("macro_context") != "completed":
            macro_payload = {
                "request_text": plan.request_text,
                "revision_note": state.get("revision_notes", {}).get("macro_context"),
            }
            macro = self._run_agent(
                "cross_market_analyst_agent",
                macro_payload,
            )
            artifact = self.o.register_artifact(
                plan.job_id,
                "macro_context",
                "macro_context.md",
                self._render_macro_context(macro),
                "cross_market_analyst_agent",
                "Cross-market context for the weekly RWA report",
            )
            self.o.append_artifact(state, artifact)
            self._record_skill_run(
                state,
                plan,
                stage="macro_context",
                skill_name=self._skill_name("rwa", "macro_context", "cross-market-context"),
                agent_name="cross_market_analyst_agent",
                payload=macro_payload,
                artifact_paths=[artifact.path],
            )
            self._record_operator_log(
                state,
                step_id="macro_context",
                module_name="analysis",
                input_payload={"request_text": plan.request_text},
                output_payload=macro,
                status="completed",
                next_step="technical_report",
            )
            self.o.mark_stage(state, "macro_context", "completed")
            self.o.save_state(plan.job_id, state)

        if state.get("stage_statuses", {}).get("technical_report") != "completed":
            technical_payload = {
                "request_text": plan.request_text,
                "revision_note": state.get("revision_notes", {}).get("technical_report"),
            }
            technical = self._run_agent(
                "technical_analyst_agent",
                technical_payload,
            )
            artifact = self.o.register_artifact(
                plan.job_id,
                "technical_report",
                "technical_report.md",
                self._render_technical_report(technical),
                "technical_analyst_agent",
                "Weekly technical structure report",
            )
            self.o.append_artifact(state, artifact)
            self._record_skill_run(
                state,
                plan,
                stage="technical_report",
                skill_name=self._skill_name("rwa", "technical_report", "market-technical-analysis"),
                agent_name="technical_analyst_agent",
                payload=technical_payload,
                artifact_paths=[artifact.path],
            )
            self._record_operator_log(
                state,
                step_id="technical_report",
                module_name="analysis",
                input_payload={"request_text": plan.request_text},
                output_payload=technical,
                status="completed",
                next_step="research_report",
            )
            self.o.mark_stage(state, "technical_report", "completed")
            self.o.save_state(plan.job_id, state)

        if state.get("stage_statuses", {}).get("research_report_review") != "completed":
            while True:
                revision_note = state.get("revision_notes", {}).get("research_report_review")
                report_payload = {
                    "request_text": plan.request_text,
                    "revision_note": revision_note,
                }
                report = self._run_agent(
                    "chief_strategist_agent",
                    report_payload,
                )
                artifact = self.o.register_artifact(
                    plan.job_id,
                    "research_report",
                    "research_report.md",
                    self._render_research_report(report),
                    "chief_strategist_agent",
                    "RWA weekly integrated research report",
                )
                self.o.append_artifact(state, artifact)
                self._record_skill_run(
                    state,
                    plan,
                    stage="research_report",
                    skill_name=self._skill_name("rwa", "research_report", "research-report-writer"),
                    agent_name="chief_strategist_agent",
                    payload=report_payload,
                    artifact_paths=[artifact.path],
                )
                self._record_operator_log(
                    state,
                    step_id="research_report",
                    module_name="strategy",
                    input_payload={"request_text": plan.request_text},
                    output_payload=report,
                    status="completed",
                    next_step="article_draft",
                )
                self.o.mark_stage(state, "research_report", "completed")
                outcome = self._gate(
                    plan,
                    state,
                    "research_report_review",
                    [artifact.path],
                    "Review the integrated RWA research report before article and video adaptation.",
                    auto_approve,
                )
                if outcome == "retry":
                    continue
                if outcome:
                    return outcome
                break

        if state.get("stage_statuses", {}).get("article_draft") != "completed":
            article_payload = {
                "request_text": plan.request_text,
                "revision_note": state.get("revision_notes", {}).get("article_draft"),
            }
            content = self._run_agent(
                "content_orchestrator_agent",
                article_payload,
            )
            article_artifact = self.o.register_artifact(
                plan.job_id,
                "article_draft",
                "article_draft.md",
                self._render_article_draft(content),
                "content_orchestrator_agent",
                "Article draft adapted from the weekly RWA report",
            )
            self.o.append_artifact(state, article_artifact)
            self._record_skill_run(
                state,
                plan,
                stage="article_draft",
                skill_name=self._skill_name("rwa", "article_draft", "content-director-pack"),
                agent_name="content_orchestrator_agent",
                payload=article_payload,
                artifact_paths=[article_artifact.path],
            )
            self._record_operator_log(
                state,
                step_id="article_draft",
                module_name="content",
                input_payload={"request_text": plan.request_text},
                output_payload=content,
                status="completed",
                next_step="content_pack",
            )
            self.o.mark_stage(state, "article_draft", "completed")
            self.o.save_state(plan.job_id, state)
        else:
            content = self._run_agent("content_orchestrator_agent", {"request_text": plan.request_text})

        if state.get("stage_statuses", {}).get("content_pack_review") != "completed":
            while True:
                revision_note = state.get("revision_notes", {}).get("content_pack_review")
                content_payload = {
                    "request_text": plan.request_text,
                    "revision_note": revision_note,
                }
                content = self._run_agent(
                    "content_orchestrator_agent",
                    content_payload,
                )
                script_artifact = self.o.register_artifact(
                    plan.job_id,
                    "script_outline",
                    "script_outline.md",
                    self._render_script_outline_rwa(content),
                    "content_orchestrator_agent",
                    "Video script outline for the RWA weekly report",
                )
                material_artifact = self.o.register_artifact(
                    plan.job_id,
                    "material_list",
                    "material_list.md",
                    self._render_material_list(content),
                    "content_orchestrator_agent",
                    "Material directions for the RWA weekly report",
                )
                for artifact in [script_artifact, material_artifact]:
                    self.o.append_artifact(state, artifact)
                self._record_skill_run(
                    state,
                    plan,
                    stage="content_pack",
                    skill_name=self._skill_name("rwa", "content_pack", "content-director-pack"),
                    agent_name="content_orchestrator_agent",
                    payload=content_payload,
                    artifact_paths=[script_artifact.path, material_artifact.path],
                )
                self._record_operator_log(
                    state,
                    step_id="content_pack",
                    module_name="content",
                    input_payload={"request_text": plan.request_text},
                    output_payload=content,
                    status="completed",
                    next_step=None,
                )
                self.o.mark_stage(state, "content_pack", "completed")
                outcome = self._gate(
                    plan,
                    state,
                    "content_pack_review",
                    [script_artifact.path, material_artifact.path],
                    "Review the RWA video outline and material list before downstream production.",
                    auto_approve,
                )
                if outcome == "retry":
                    continue
                if outcome:
                    return outcome
                break

        state["status"] = WorkflowFinalStatus.COMPLETED.value
        self.o.save_state(plan.job_id, state)
        return self.o.build_result(
            plan=plan,
            state=state,
            final_status=WorkflowFinalStatus.COMPLETED.value,
            summary="RWA weekly deep research workflow completed with research, article draft, script outline, and material list.",
            next_actions=[
                f"Open {self.o.get_job_dir(plan.job_id) / 'research_report.md'} to review the integrated report.",
                f"Open {self.o.get_job_dir(plan.job_id) / 'script_outline.md'} to continue into video production.",
            ],
        )

    def _render_rwa_review_plan(self, director: Dict[str, Any], plan: ExecutionPlan) -> str:
        scope = self._bullet_lines(director["scope"])
        out_of_scope = self._bullet_lines(director["out_of_scope"])
        phases = self._bullet_lines(director["phases"])
        risks = self._bullet_lines(director["risk_points"])
        reviews = self._bullet_lines(director["review_nodes"])
        return f"""# Review Plan

- Job ID: `{plan.job_id}`
- Workflow: `{plan.workflow_name}`
- Request: {plan.request_text}

## 本周研究主题
{director["theme"]}

## 核心研究问题
{director["core_question"]}

## 本周主线定义
{director["mainline"]}

## 研究范围
{scope}

## 不覆盖范围
{out_of_scope}

## 阶段清单
{phases}

## 风险点
{risks}

## 审核节点
{reviews}
"""

    def _render_news_digest(self, news: Dict[str, Any], tool_result: Dict[str, Any]) -> str:
        sections = []
        for title, items in news["categories"].items():
            bullet = self._bullet_lines(items)
            sections.append(f"## {title}\n{bullet}")
        source_lines = "\n".join(
            f"- [{item['title']}]({item['url']})"
            for item in tool_result.get("data", {}).get("sources", [])
        )
        return f"""# News Digest

## 本周新闻总览
{news["summary"]}

{chr(10).join(sections)}

## 去重与筛选原则
{self._bullet_lines(news["verification_notes"])}

## 重点观察清单
{self._bullet_lines(news["watchlist"])}

## Mock Search Sources
{source_lines or "- 暂无"}
"""

    def _render_macro_context(self, macro: Dict[str, Any]) -> str:
        dimensions = "\n".join(
            f"- {item['name']}：{item['insight']}" for item in macro["dimensions"]
        )
        return f"""# Macro Context

## 本周宏观背景摘要
{macro["macro_summary"]}

## BTC 对 RWA 的背景意义
{macro["btc_context"]}

## 黄金对 RWA 的背景意义
{macro["gold_context"]}

## NQ 对 RWA 的背景意义
{macro["nq_context"]}

## 四维分析
{dimensions}

## 对 RWA 主线的支撑结论
{macro["rwa_implication"]}
"""

    def _render_technical_report(self, technical: Dict[str, Any]) -> str:
        sections = []
        for item in technical["instruments"]:
            sections.append(
                f"""## {item["name"]}

- 周线：{item["weekly"]}
- 日线：{item["daily"]}
- 关键位：{item["levels"]}
- 本周回顾：{item["review"]}
- 下周观察点：{item["watch_next_week"]}
"""
            )
        return f"""# Technical Report

## 观察标的列表
{self._bullet_lines([item["name"] for item in technical["instruments"]])}

{chr(10).join(sections)}

## 总结
{technical["conclusion"]}
"""

    def _render_research_report(self, report: Dict[str, Any]) -> str:
        return f"""# Research Report

## 本周 RWA 核心结论
{report["core_conclusion"]}

## 本周关键新闻与结构性进展
{self._bullet_lines(report["news_progress"])}

## BTC / 黄金 / NQ 的宏观背景
{report["macro_bridge"]}

## 技术走势与市场验证
{report["technical_validation"]}

## 下周预测
{self._bullet_lines(report["next_week_outlook"])}

## 风险提示
{self._bullet_lines(report["risk_warnings"])}
"""

    def _render_article_draft(self, content: Dict[str, Any]) -> str:
        return f"""# Article Draft

## 标题建议
{content["article_title"]}

## 导语
本稿围绕本周 RWA 主线展开，重点区分真实结构进展与市场情绪交易。

## 正文结构
{self._bullet_lines(content["article_sections"])}

## 本周结论
RWA 的研究重点仍应放在机构推进、监管边界和基础设施完善，而不是只看概念热度。

## 风险提示
- 结构性进展未必同步反映在二级市场价格上
- 市场情绪可能放大短期波动

## 下周前瞻
继续观察机构、监管与基础设施三条线是否形成共振。
"""

    def _render_script_outline_rwa(self, content: Dict[str, Any]) -> str:
        sections = "\n".join(
            f"### {item['heading']}\n{item['point']}" for item in content["script_sections"]
        )
        return f"""# Script Outline

## 视频标题
{content["script_title"]}

## 开头钩子
{content["hook"]}

## 视频结构
{sections}

## 结尾收束
把下周最值得盯的变量讲清楚，让内容形成连续栏目感。

## 可延展说明
本提纲可进一步扩展为完整口播稿或数字人口播稿。
"""

    def _render_material_list(self, content: Dict[str, Any]) -> str:
        return f"""# Material List

## 画面素材方向
{self._bullet_lines(content["material_directions"])}

## 图表与数据卡建议
- RWA 结构进展四象限图
- BTC / 黄金 / NQ 跨市场参照图
- 本周关键事件时间线

## 引用素材类别
- 机构公告
- 监管表述截图
- 市场结构图卡
- 关键结论字幕卡

## 后续剪辑建议
{self._bullet_lines(content["editing_notes"])}
"""
