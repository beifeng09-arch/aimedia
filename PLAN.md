# OpenClaw 媒体智能体团队 MVP 实施计划

**摘要**
- 以空仓库为起点，先落地一个 Python + YAML 的“半自动多智能体内容工厂”。
- 一期目标锁定为“本地 CLI MVP”，先跑通两条节目流程：`东南军情` 与 `数字货币财经`。
- 审核采用“双通道”，但以本地审批文件为事实源；微信/OpenClaw 在一期提供接入边界、事件契约和模拟回调，不把真实联调塞进首轮实现。
- 工具层全部先做 stub/mock，保证从任务输入到结构化结果输出可完整跑通。

**架构图（文字版）**
- 输入层：`CLI 命令` -> 后续预留 `OpenClaw webhook` / `微信回调`
- 路由层：`Task Router` 识别 `military / finance / mixed / system`
- 总控层：`director_agent` 生成任务计划，`operator_agent` 负责状态推进、日志、失败回退
- 节目策划层：`military_editor_agent` / `finance_editor_agent`
- 内容生产层：`researcher_agent` -> `scriptwriter_agent` -> `storyboard_agent` -> `avatar_host_agent`
- 后期执行层：`editor_agent` -> `publisher_agent`
- 审核层：在 `plan` 和 `content pack` 两个节点暂停，等待 `approve / revise / reject`
- 工具层：统一 `execute(input: dict) -> dict` 适配器，先返回 mock 数据
- 输出层：写入 `outputs/{job_id}/` 的 Markdown/YAML/JSON 产物与 `logs/*.log`

**项目目录结构**
```text
project_root/
├── README.md
├── requirements.txt
├── .env.example
├── main.py
├── config/
│   ├── app.yaml
│   ├── routing.yaml
│   └── workflows.yaml
├── core/
│   ├── models.py
│   ├── router.py
│   ├── orchestrator.py
│   ├── agent_runner.py
│   ├── review.py
│   ├── llm.py
│   └── logging_utils.py
├── agents/
│   ├── director_agent.yaml
│   ├── operator_agent.yaml
│   ├── military_editor_agent.yaml
│   ├── finance_editor_agent.yaml
│   ├── researcher_agent.yaml
│   ├── scriptwriter_agent.yaml
│   ├── storyboard_agent.yaml
│   ├── avatar_host_agent.yaml
│   ├── editor_agent.yaml
│   └── publisher_agent.yaml
├── prompts/
│   ├── director.md
│   ├── operator.md
│   ├── military_editor.md
│   ├── finance_editor.md
│   ├── researcher.md
│   ├── scriptwriter.md
│   ├── storyboard.md
│   ├── avatar_host.md
│   ├── editor.md
│   └── publisher.md
├── workflows/
│   ├── southeast_military_pipeline.py
│   ├── crypto_finance_pipeline.py
│   └── mixed_topic_pipeline.py
├── tools/
│   ├── __init__.py
│   ├── base.py
│   ├── registry.py
│   ├── web_search.py
│   ├── video_download.py
│   ├── transcript.py
│   ├── subtitle_generate.py
│   ├── ffmpeg_edit.py
│   ├── tts_generate.py
│   ├── avatar_presenter.py
│   └── publish_output.py
├── templates/
│   ├── southeast_military.yaml
│   └── crypto_finance.yaml
├── outputs/
├── logs/
└── tests/
```

**关键接口与配置**
- 路由接口：
  - `classify_task(text: str) -> TaskCategory`
  - `build_execution_plan(category: TaskCategory, text: str) -> ExecutionPlan`
  - `run_workflow(plan: ExecutionPlan) -> WorkflowResult`
  - `save_log(result: dict) -> Path`
- 工具接口：
  - 每个工具文件暴露 `execute(input: dict) -> dict`
  - 统一返回 `{success, tool, data, error, meta}`
- 审核接口：
  - `request_review(job_id, stage, artifact_paths) -> ReviewTicket`
  - `consume_decision(job_id) -> ReviewDecision`
- 关键数据模型：
  - `TaskCategory = military | finance | mixed | system`
  - `ExecutionPlan` 含 `job_id / category / steps / review_points / status`
  - `ArtifactEnvelope` 含 `artifact_type / path / producer / schema_version`
  - `WorkflowResult` 含 `artifacts / logs / final_status / next_actions`
- 配置清单：
  - `config/app.yaml`：环境、日志、默认 LLM、审批模式、输出目录
  - `config/routing.yaml`：规则关键词、优先级、工作流映射、回退策略
  - `config/workflows.yaml`：各流程步骤、依赖、审核节点、默认模板
  - `agents/*.yaml`：你要求的 9 个字段全部落地
  - `templates/*.yaml`：节目结构模板、时长、输出字段、素材方向

**产物与审核机制**
- 每个任务写入 `outputs/{job_id}/`
- 一期固定产物：
  - `request.yaml`
  - `execution_plan.yaml`
  - `review_plan.md`
  - `research_brief.md`
  - `script_outline.md`
  - `storyboard.md`
  - `avatar_script.md`（财经必产，军情可选）
  - `publish_pack.md`
  - `result.json`
- 审核规则：
  - Gate 1：总导演计划完成后暂停
  - Gate 2：研究 + 脚本 + 分镜内容包完成后暂停
  - `approve` 继续执行，`revise` 回退到上一步责任智能体，`reject` 终止任务并保留日志
- 双通道实现：
  - 本地审批文件是事实源
  - 微信/OpenClaw 一期只实现消息映射与模拟决策适配，不承担唯一状态存储

**第一批生成文件**
- 基础：`README.md`、`requirements.txt`、`.env.example`、`main.py`
- 配置：`config/app.yaml`、`config/routing.yaml`、`config/workflows.yaml`
- 核心运行时：`core/models.py`、`core/router.py`、`core/orchestrator.py`、`core/review.py`
- 智能体：10 个 `agents/*.yaml` + 10 个 `prompts/*.md`
- 模板：`templates/southeast_military.yaml`、`templates/crypto_finance.yaml`
- 工具：8 个 stub + `tools/registry.py`
- 流程：`workflows/southeast_military_pipeline.py`、`workflows/crypto_finance_pipeline.py`、`workflows/mixed_topic_pipeline.py`
- 测试：`tests/test_router.py`、`tests/test_military_pipeline.py`、`tests/test_finance_pipeline.py`、`tests/test_review_flow.py`、`tests/test_tools.py`

**实施顺序**
1. 初始化仓库基础文件、目录、依赖和 YAML 配置加载。
2. 建立 `core` 层的数据模型、日志、任务状态机、审批状态机。
3. 完成 `routing.yaml` 与 `router.py`，先用规则分类，预留 LLM 分类器接口。
4. 落地 10 个核心智能体配置与 prompts，并实现统一 `agent_runner`。
5. 实现两条主流程，先生成结构化 Markdown/YAML 产物，不接真实外部工具。
6. 实现 8 个工具 stub、统一错误结构和 `logs/tools.log`。
7. 接入 `main.py` CLI demo，跑通“做一期南海局势节目”和“做一期比特币周报”。
8. 补齐测试与示例输出，再新增 OpenClaw/微信适配器骨架与模拟事件。
9. 二期再接真实 `ffmpeg / transcript / TTS / 数字人 / 发布`。

**测试与验收**
- 路由测试：
  - “做一期南海局势节目” -> `military`
  - “做一期比特币周报” -> `finance`
  - 系统配置指令 -> `system`
  - 混合议题 -> `mixed`
- 流程验收：
  - 军情流程输出 `节目标题 / 节目结构 / 研究提纲 / 脚本提纲 / 分镜提纲 / 发布标题`
  - 财经流程输出 `本周主题 / 三个关键数据点 / 节目提纲 / 数字人口播稿 / 发布文案`
- 审核验收：
  - Gate 1、Gate 2 都能暂停、继续、回退
  - 拒绝后生成终止日志，不丢失中间产物
- 工具验收：
  - 每个 stub 都能返回 mock
  - 报错时统一返回错误结构并写入 `logs/tools.log`

**假设与默认值**
- 当前目录为空仓库，实施时先初始化 Git 与基础工程。
- 运行环境按当前 Mac + Python 3.9 兼容设计；生产建议后续升级到 Python 3.11。
- 一期实现 10 个核心智能体，`素材统筹智能体` 作为二期补充，不阻塞 MVP。
- 内容产出默认中文；代码、配置 key、日志字段使用英文命名。
- OpenClaw、微信、真实 API 凭证通过 `.env` 注入，不写死在仓库中。
