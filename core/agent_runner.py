from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from core.logging_utils import load_yaml


class AgentRunner:
    def __init__(self, root_dir: Path) -> None:
        self.root_dir = Path(root_dir)
        self._config_cache: Dict[str, Dict[str, Any]] = {}
        self._prompt_cache: Dict[str, str] = {}
        self._handlers = {
            "director_agent": self._run_director,
            "operator_agent": self._run_operator,
            "military_editor_agent": self._run_military_editor,
            "finance_editor_agent": self._run_finance_editor,
            "rwa_research_director_agent": self._run_rwa_research_director,
            "rwa_news_researcher_agent": self._run_rwa_news_researcher,
            "cross_market_analyst_agent": self._run_cross_market_analyst,
            "technical_analyst_agent": self._run_technical_analyst,
            "chief_strategist_agent": self._run_chief_strategist,
            "content_orchestrator_agent": self._run_content_orchestrator,
            "researcher_agent": self._run_researcher,
            "scriptwriter_agent": self._run_scriptwriter,
            "storyboard_agent": self._run_storyboard,
            "avatar_host_agent": self._run_avatar_host,
            "editor_agent": self._run_editor,
            "publisher_agent": self._run_publisher,
        }

    def run(self, agent_name: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        config = self._load_agent_config(agent_name)
        prompt = self._load_prompt(config["system_prompt_file"])
        handler = self._handlers.get(agent_name)
        if handler is None:
            raise ValueError(f"Unsupported agent: {agent_name}")

        output = handler(payload)
        return {
            "agent_name": agent_name,
            "role": config.get("role"),
            "goal": config.get("goal"),
            "prompt_preview": prompt[:200],
            "output": output,
        }

    def _load_agent_config(self, agent_name: str) -> Dict[str, Any]:
        if agent_name not in self._config_cache:
            path = self.root_dir / "agents" / f"{agent_name}.yaml"
            self._config_cache[agent_name] = load_yaml(path)
        return self._config_cache[agent_name]

    def _load_prompt(self, relative_path: str) -> str:
        if relative_path not in self._prompt_cache:
            path = self.root_dir / relative_path
            self._prompt_cache[relative_path] = path.read_text(encoding="utf-8")
        return self._prompt_cache[relative_path]

    @staticmethod
    def _extract_topic(payload: Dict[str, Any]) -> str:
        text = payload.get("request_text") or payload.get("topic") or "本期选题"
        prefixes = ["做一期", "请做一期", "做一个", "来一期"]
        for prefix in prefixes:
            if text.startswith(prefix):
                return text[len(prefix) :].strip()
        return text.strip()

    @staticmethod
    def _revision_suffix(payload: Dict[str, Any]) -> str:
        note = payload.get("revision_note")
        if not note:
            return ""
        return f"（已吸收修订意见：{note}）"

    def _run_director(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        category = payload.get("category", "military")
        topic = self._extract_topic(payload)
        suffix = self._revision_suffix(payload)
        if category == "finance":
            agents = [
                "director_agent",
                "operator_agent",
                "finance_editor_agent",
                "researcher_agent",
                "scriptwriter_agent",
                "avatar_host_agent",
                "editor_agent",
                "publisher_agent",
            ]
            deliverables = [
                "execution_plan.yaml",
                "review_plan.md",
                "research_brief.md",
                "script_outline.md",
                "avatar_script.md",
                "publish_pack.md",
            ]
        elif category == "rwa":
            agents = [
                "rwa_research_director_agent",
                "operator_agent",
                "rwa_news_researcher_agent",
                "cross_market_analyst_agent",
                "technical_analyst_agent",
                "chief_strategist_agent",
                "content_orchestrator_agent",
            ]
            deliverables = [
                "execution_plan.yaml",
                "review_plan.md",
                "news_digest.md",
                "macro_context.md",
                "technical_report.md",
                "research_report.md",
                "article_draft.md",
                "script_outline.md",
                "material_list.md",
            ]
        else:
            agents = [
                "director_agent",
                "operator_agent",
                "military_editor_agent",
                "researcher_agent",
                "scriptwriter_agent",
                "storyboard_agent",
                "editor_agent",
                "publisher_agent",
            ]
            deliverables = [
                "execution_plan.yaml",
                "review_plan.md",
                "research_brief.md",
                "script_outline.md",
                "storyboard.md",
                "publish_pack.md",
            ]
        return {
            "task_type": category,
            "task_goal": f"围绕“{topic}”生成一期结构化节目内容包{suffix}",
            "required_agents": agents,
            "execution_order": agents,
            "deliverables": deliverables,
            "risk_points": [
                "研究结论不得替代事实核验",
                "脚本需要兼顾信息密度和口播可读性",
                "发布标题需要控制传播性与可信度的平衡",
            ],
            "review_nodes": ["research_report_review", "content_pack_review"] if category == "rwa" else ["plan", "content_pack"],
        }

    def _run_operator(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        step = payload.get("step_id", "unknown")
        return {
            "step_id": step,
            "module_name": payload.get("module_name", "workflow"),
            "input": payload.get("input", {}),
            "action": payload.get("action", "execute_step"),
            "output": payload.get("output", {}),
            "status": payload.get("status", "completed"),
            "next_step": payload.get("next_step"),
        }

    def _run_military_editor(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        topic = self._extract_topic(payload)
        suffix = self._revision_suffix(payload)
        return {
            "title": f"南海局势观察：{topic}{suffix}",
            "background": f"围绕“{topic}”梳理东南方向安全、海上态势与区域关系变化。",
            "core_conflict": "局势升温与各方克制之间的张力",
            "three_act_structure": [
                {"section": "开场冲突", "point": "先把近期最具冲突感的现象抛出来"},
                {"section": "背景与变化", "point": "解释局势为什么变得更值得关注"},
                {"section": "战略观察", "point": "收束到未来观察点和判断边界"},
            ],
            "segment_points": [
                "开头强调局势变化而非渲染情绪",
                "中段用背景、地理和行动链条讲清因果",
                "结尾给出观察指标，而不是绝对结论",
            ],
            "duration_minutes": "5-6",
            "visual_directions": ["海域地图", "公开演训画面", "时间线图卡", "区域关系图示"],
        }

    def _run_finance_editor(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        topic = self._extract_topic(payload)
        suffix = self._revision_suffix(payload)
        return {
            "theme": f"数字货币焦点：{topic}{suffix}",
            "focus": f"围绕“{topic}”梳理本周最值得关注的数据、逻辑和风险。",
            "key_data_points": [
                "价格区间与周内波动幅度",
                "资金流向或 ETF 相关变化",
                "链上活跃度或稳定币流动性指标",
            ],
            "macro_logic": "从流动性、政策预期和风险偏好三个维度看市场",
            "market_impact": "区分短线交易情绪和中期基本面变化",
            "risk_warning": "强调不确定性与风险管理，而不是收益承诺",
            "format": "周报",
        }

    def _run_rwa_research_director(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        topic = self._extract_topic(payload) or "本周 RWA 深度研究"
        suffix = self._revision_suffix(payload)
        return {
            "theme": f"RWA 周度深度研究：{topic}{suffix}",
            "core_question": "本周 RWA 主线究竟是机构推进、监管重估，还是市场对资产上链叙事的提前交易。",
            "mainline": "围绕 RWA 真实结构进展，而不是单一价格涨跌做判断。",
            "scope": [
                "过去一周 RWA 新闻与产业动向",
                "BTC、黄金、NQ 对 RWA 的宏观背景意义",
                "主要参照资产与必要 RWA 标的技术结构",
                "可转化为文章和视频的内容框架",
            ],
            "out_of_scope": [
                "纯情绪喊单",
                "未经验证的小道消息",
                "脱离 RWA 主线的泛加密市场杂谈",
            ],
            "phases": [
                "任务启动",
                "新闻采集与筛选",
                "跨市场背景分析",
                "技术走势分析",
                "综合研究报告",
                "文章初稿",
                "视频脚本与素材整理",
            ],
            "risk_points": [
                "必须区分新闻事实、研究判断和市场推演",
                "BTC、黄金、NQ 只能作为参照系，不能喧宾夺主",
                "技术分析只能作为验证层，不能替代产业研究",
            ],
            "review_nodes": ["research_report_review", "content_pack_review"],
        }

    def _run_rwa_news_researcher(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        topic = self._extract_topic(payload) or "本周 RWA 深度研究"
        return {
            "topic": topic,
            "summary": "本周 RWA 新闻以机构推进、监管讨论和基础设施升级为主，市场炒作成分需要与真实产业进展分开看。",
            "categories": {
                "机构推进": [
                    "传统金融机构继续测试代币化基金、国债或链上清算流程",
                    "大型资管或金融基础设施服务商扩大试点合作范围",
                ],
                "监管动态": [
                    "监管口径更关注合规发行、托管和投资者保护",
                    "部分地区对资产上链的合规边界表达更清晰",
                ],
                "项目进展": [
                    "RWA 协议披露新的资产类别覆盖或合作方进展",
                    "项目方更强调真实收益与可验证底层资产",
                ],
                "市场炒作": [
                    "二级市场对 RWA 概念做情绪交易，但并不等于基本面同步兑现",
                ],
                "基础设施变化": [
                    "托管、清算、身份、合规中间件和链上结算设施持续升级",
                ],
            },
            "verification_notes": [
                "优先保留有公告、机构声明或主流媒体来源的事件",
                "把概念拉升与真实业务进展分开书写",
            ],
            "watchlist": [
                "tokenized treasuries",
                "tokenized funds",
                "on-chain settlement rails",
                "compliance middleware",
            ],
        }

    def _run_cross_market_analyst(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        topic = self._extract_topic(payload) or "本周 RWA 深度研究"
        return {
            "topic": topic,
            "macro_summary": "RWA 本周要放在流动性预期、风险偏好切换和成长资产估值重估的框架里观察。",
            "btc_context": "BTC 提供市场风险偏好与加密资金主流情绪的参照，但其上涨不必然等于 RWA 基本面同步改善。",
            "gold_context": "黄金反映避险需求与真实利率预期，能帮助判断市场是否在寻找更稳健的价值锚。",
            "nq_context": "NQ 反映成长资产估值与科技风险偏好，对 RWA 估值叙事和基础设施类项目有映射意义。",
            "dimensions": [
                {"name": "流动性", "insight": "若流动性边际宽松，RWA 更容易得到估值与叙事加成。"},
                {"name": "风险偏好", "insight": "风险偏好抬升时，市场更愿意交易资产上链与收益类叙事。"},
                {"name": "避险", "insight": "避险升温时，RWA 中与国债、基金和现金流资产相关的方向更受关注。"},
                {"name": "成长估值", "insight": "成长资产估值修复会提升基础设施型 RWA 项目的市场关注度。"},
            ],
            "rwa_implication": "RWA 本周更适合作为连接传统金融信用资产与链上结算效率的桥梁来理解。",
        }

    def _run_technical_analyst(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        topic = self._extract_topic(payload) or "本周 RWA 深度研究"
        return {
            "topic": topic,
            "instruments": [
                {
                    "name": "BTC",
                    "weekly": "周线仍处于强势区间，但短线进入高位震荡。",
                    "daily": "日线关注前高附近承接与量能变化。",
                    "levels": "关键位：前高支撑、突破延续位、回撤确认位。",
                    "review": "本周走势主要验证市场风险偏好仍在。",
                    "watch_next_week": "观察放量突破是否可持续。",
                },
                {
                    "name": "黄金",
                    "weekly": "周线维持高位强势，避险需求仍有韧性。",
                    "daily": "日线关注冲高后的回踩稳定性。",
                    "levels": "关键位：阶段高点、短期均线支撑。",
                    "review": "本周表现提供了避险定价参考。",
                    "watch_next_week": "关注风险事件与利率预期共振。",
                },
                {
                    "name": "NQ",
                    "weekly": "周线结构决定成长资产风险偏好是否继续扩张。",
                    "daily": "日线重视回调是否缩量、反弹是否放量。",
                    "levels": "关键位：上升趋势支撑与短线压力区。",
                    "review": "本周反映科技成长板块估值弹性。",
                    "watch_next_week": "关注是否继续强化对 RWA 基础设施叙事的映射。",
                },
                {
                    "name": "RWA 相关标的",
                    "weekly": "重点看是否有跟随主线共振，而不是单独异动。",
                    "daily": "日线更适合验证题材是否具备持续交易性。",
                    "levels": "关键位：放量启动位、回踩确认位。",
                    "review": "本周更多用于情绪验证，而不是单独定价中心。",
                    "watch_next_week": "关注是否从概念炒作转向结构化轮动。",
                },
            ],
            "conclusion": "技术层面对 RWA 的意义是验证市场是否愿意为这条主线持续定价。",
        }

    def _run_chief_strategist(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        topic = self._extract_topic(payload) or "本周 RWA 深度研究"
        return {
            "topic": topic,
            "core_conclusion": "本周 RWA 主线更接近结构性推进，而不是单纯情绪炒作；真正值得盯的是机构化落地与合规基础设施。",
            "news_progress": [
                "机构推进与监管表达共同推动 RWA 叙事向更可验证的方向发展。",
                "项目层面的扩容和合作落地，比短线概念拉升更有研究价值。",
            ],
            "macro_bridge": "BTC、黄金、NQ 分别代表风险偏好、避险需求和成长估值环境，为 RWA 提供跨市场坐标系。",
            "technical_validation": "技术结构并不决定 RWA 主线，但能验证市场是否愿意为这条主线持续定价。",
            "next_week_outlook": [
                "观察机构和监管表述是否继续提供正向催化。",
                "观察 RWA 相关标的是否出现从概念炒作到结构轮动的切换。",
                "观察风险偏好是否仍支持链上真实收益资产的叙事扩张。",
            ],
            "risk_warnings": [
                "真实落地进展可能慢于市场预期。",
                "宏观风险偏好回落时，RWA 概念交易可能先降温。",
                "未验证叙事容易带来结构性误判。",
            ],
        }

    def _run_content_orchestrator(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        topic = self._extract_topic(payload) or "本周 RWA 深度研究"
        return {
            "topic": topic,
            "article_title": f"本周 RWA 深度研究：从机构推进到市场验证",
            "article_sections": [
                "导语：先交代本周为什么要继续盯 RWA",
                "新闻结构：把真进展和情绪交易分开",
                "宏观背景：BTC、黄金、NQ 如何提供坐标",
                "技术验证：市场有没有为 RWA 主线持续定价",
                "结论与下周前瞻",
            ],
            "script_title": f"本周 RWA 研究：别只盯 BTC，这条主线可能更重要",
            "hook": "这一周，如果你只看币价，可能会错过 RWA 真正的结构变化。",
            "script_sections": [
                {"heading": "为什么本周还要盯 RWA", "point": "先给结论和研究主线。"},
                {"heading": "本周有哪些真进展", "point": "机构、监管、项目和基础设施逐项拆开。"},
                {"heading": "BTC、黄金、NQ 告诉了我们什么", "point": "建立跨市场参照系。"},
                {"heading": "技术面有没有验证这条主线", "point": "看市场是否持续定价。"},
                {"heading": "下周看什么", "point": "给出明确观察清单。"},
            ],
            "material_directions": [
                "RWA 产业结构图",
                "机构 / 监管 / 项目 / 基建四分图",
                "BTC、黄金、NQ 对比图卡",
                "关键结论字幕卡",
            ],
            "editing_notes": [
                "视频前 15 秒先把 RWA 主线立住",
                "中段用图卡而不是长段口播承载信息密度",
                "结尾明确下周观察点，方便做连续栏目",
            ],
        }

    def _run_researcher(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        topic = self._extract_topic(payload)
        category = payload.get("category", "military")
        suffix = self._revision_suffix(payload)
        if category == "finance":
            facts = [
                {"fact": "本周价格区间与成交量变化", "status": "待核验", "confidence": "medium"},
                {"fact": "ETF 或机构资金流入流出", "status": "待核验", "confidence": "medium"},
                {"fact": "监管、政策或宏观数据发布时间", "status": "待核验", "confidence": "low"},
            ]
            disputes = ["市场上涨是否由单一事件驱动", "资金流是否具有持续性"]
            angles = ["先讲数据，再讲逻辑，最后给风险提示"]
        else:
            facts = [
                {"fact": "近期公开通报的行动与时间线", "status": "待核验", "confidence": "medium"},
                {"fact": "相关海域和区域关系背景", "status": "已知背景", "confidence": "medium"},
                {"fact": "外部媒体与官方表述是否一致", "status": "待核验", "confidence": "low"},
            ]
            disputes = ["局势变化是短期事件还是节奏升级", "外界解读是否高于事实本身"]
            angles = ["突出冲突点，但把判断建立在证据链和背景解释上"]
        return {
            "research_topic": f"{topic}{suffix}",
            "background_summary": f"本稿先梳理“{topic}”的公开信息，再区分已知、待核验和不可确认部分。",
            "key_facts": facts,
            "controversies": disputes,
            "verification_questions": [
                "最关键的时间节点是什么",
                "哪些表述有公开出处，哪些只是市场或舆论推演",
                "哪些结论需要明确写成观察而非事实",
            ],
            "writer_angles": angles,
        }

    def _run_scriptwriter(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        topic = self._extract_topic(payload)
        category = payload.get("category", "military")
        suffix = self._revision_suffix(payload)
        if category == "finance":
            title = f"比特币周报：{topic}{suffix}"
            hook = "这一周，市场真正需要看的，不是情绪，而是资金和节奏。"
            sections = [
                {"heading": "当周焦点", "summary": f"围绕“{topic}”快速交代本周最重要的变化。"},
                {"heading": "数据与事实", "summary": "用三个核心数据点建立观众的判断坐标。"},
                {"heading": "逻辑分析", "summary": "拆解数据背后的宏观流动性、政策预期和风险偏好。"},
                {"heading": "市场影响", "summary": "区分短期交易影响和中期结构影响。"},
                {"heading": "风险提示", "summary": "提醒高波动与事件驱动风险。"},
            ]
        else:
            title = f"东南军情：{topic}{suffix}"
            hook = "这不是一个孤立动作，而是一连串信号叠加之后的结果。"
            sections = [
                {"heading": "开场冲突", "summary": f"直接点出“{topic}”最值得关注的变化。"},
                {"heading": "背景介绍", "summary": "把地理、关系和前序动作放回同一时间线里。"},
                {"heading": "关键变化", "summary": "说明这次与过去相比，到底哪里不同。"},
                {"heading": "战略分析", "summary": "讲清各方行为逻辑与约束。"},
                {"heading": "未来观察", "summary": "给出接下来最值得继续盯的指标。"},
            ]
        subtitles = [item["heading"] for item in sections]
        return {
            "title": title,
            "hook": hook,
            "sections": sections,
            "closing": "先看事实，再看逻辑，最后才谈判断。",
            "subtitle_suggestions": subtitles,
            "voice_tone": "稳健、清晰、有节奏",
        }

    def _run_storyboard(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        topic = self._extract_topic(payload)
        shots: List[Dict[str, Any]] = [
            {
                "shot_no": 1,
                "duration": "0:08",
                "visual": f"{topic} 标题卡 + 关键冲突字幕",
                "material_type": "title_card",
                "narration": "开头先抛出本期核心问题。",
                "subtitle": "先看这次变化到底意味着什么",
                "transition": "hard_cut",
            },
            {
                "shot_no": 2,
                "duration": "0:18",
                "visual": "地图 + 时间线图示",
                "material_type": "map_and_timeline",
                "narration": "用地图和时间线把背景讲清楚。",
                "subtitle": "背景不是陪衬，而是理解判断的前提",
                "transition": "push",
            },
            {
                "shot_no": 3,
                "duration": "0:22",
                "visual": "公开素材 + 数据/要点卡片",
                "material_type": "broll_and_graphic",
                "narration": "展示关键变化和分析框架。",
                "subtitle": "关键变化要拆开看，而不是混着说",
                "transition": "cross_dissolve",
            },
            {
                "shot_no": 4,
                "duration": "0:12",
                "visual": "总结卡 + 下一步观察点",
                "material_type": "summary_card",
                "narration": "结尾落到观察指标和下期钩子。",
                "subtitle": "真正值得盯的，是接下来的信号",
                "transition": "fade_out",
            },
        ]
        return {"topic": topic, "shots": shots}

    def _run_avatar_host(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        topic = self._extract_topic(payload)
        suffix = self._revision_suffix(payload)
        return {
            "host_script": (
                f"今天我们用几个关键点，快速看懂“{topic}”。{suffix} "
                "先看数据，再看逻辑，最后提醒风险。"
            ),
            "sentence_breaks": [
                "今天我们用几个关键点，",
                f"快速看懂“{topic}”。",
                "先看数据，",
                "再看逻辑，",
                "最后提醒风险。",
            ],
            "emphasis_words": ["关键点", "数据", "逻辑", "风险"],
            "tone": "稳重",
            "style": "新闻感",
        }

    def _run_editor(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        topic = self._extract_topic(payload)
        return {
            "input_assets": ["script_outline.md", "storyboard.md", "subtitle cues", "mock b-roll list"],
            "edit_sequence": [
                "assemble intro",
                "insert map or data cards",
                "align subtitles with narration beats",
                "export preview version",
            ],
            "subtitle_strategy": "大字重点词 + 下方完整字幕",
            "bgm": "低压迫感新闻节奏底乐",
            "transitions": ["hard_cut", "push", "cross_dissolve"],
            "export_settings": {"resolution": "1920x1080", "fps": 30, "codec": "h264"},
            "draft_command": f"ffmpeg_edit --job {topic} --preset mvp_preview",
        }

    def _run_publisher(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        topic = self._extract_topic(payload)
        category = payload.get("category", "military")
        if category == "finance":
            return {
                "douyin_title": f"比特币周报：这一周最该看的三个信号 | {topic}",
                "wechat_title": f"数字货币周报：{topic}",
                "youtube_title": f"Crypto Weekly Brief: {topic}",
                "description": "从数据、逻辑和风险三个层面拆解本期焦点，适合做周度复盘。",
                "tags": ["比特币", "数字货币", "周报", "宏观", "风险提示"],
                "cover_copy": "三组数据，看清这一周",
                "publish_time_suggestion": "周日 20:00",
            }
        return {
            "douyin_title": f"南海局势最新观察：{topic}",
            "wechat_title": f"东南军情节：{topic}",
            "youtube_title": f"Southeast Military Brief: {topic}",
            "description": "围绕公开信息与战略逻辑拆解本期焦点，适合中视频深度解读。",
            "tags": ["南海", "军情", "区域安全", "战略分析", "东南方向"],
            "cover_copy": "局势变了，关键看哪里",
            "publish_time_suggestion": "工作日 19:30",
        }
