# OpenClaw Media Agent Team MVP

OpenClaw `媒体智能体团队系统` 的第一版本地 MVP。这个版本专注于把三条内容生产链路跑通：

- `东南军情` 节目策划与内容包生成
- `数字货币财经` 节目策划、口播与发布包生成
- `RWA 周度深度研究` 的研究、文章和视频提纲生成

当前实现是一个 `Python + YAML` 的半自动多智能体工作流：

1. 从 CLI 接收自然语言任务
2. 路由到对应节目流程
3. 由总导演、主编、研究员、编剧、分镜、数字人主持、剪辑、发布运营等角色顺序产出
4. 在 `plan` 和 `content_pack` 两个节点支持人工审核
5. 以本地文件为审核事实源，同时生成微信/OpenClaw 模拟消息载荷

## Features

- Python 3.9 compatible
- YAML-first configuration and agent definitions
- Rule-based router with reserved LLM classifier interface
- Review gates with `approve / revise / reject`
- Tool adapter stubs with unified `execute(input: dict) -> dict`
- Local outputs under `outputs/<job_id>/`
- Basic tests for routing, tools, review flow, and both content pipelines
- Workspace-level reusable skills for the RWA workflow

## Project Layout

```text
.
├── README.md
├── requirements.txt
├── .env.example
├── main.py
├── config/
├── core/
├── agents/
├── prompts/
├── workflows/
├── tools/
├── templates/
├── outputs/
├── logs/
└── tests/
```

## Quick Start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

运行军情演示：

```bash
python3 main.py run "做一期南海局势节目" --auto-approve
```

运行财经演示：

```bash
python3 main.py run "做一期比特币周报" --auto-approve
```

运行 RWA 深度研究演示：

```bash
python3 main.py run "做本周 RWA 深度研究" --auto-approve
```

查看双流程 demo：

```bash
python3 main.py demo --auto-approve
```

启动本地服务：

```bash
python3 main.py serve --host 127.0.0.1 --port 8787
```

查看定时任务：

```bash
python3 main.py schedule-list
```

执行当前到点任务：

```bash
python3 main.py schedule-run-due
```

立即执行某个定时任务：

```bash
python3 main.py schedule-run-job military_weekday_briefing
```

立即执行 RWA 周度调度任务：

```bash
python3 main.py schedule-run-job rwa_weekly_deep_research
```

将 OpenClaw 当前微信会话绑定到本项目线程：

```bash
python3 main.py bind-openclaw
```

如果需要指定 thread id 或会话 id：

```bash
python3 main.py bind-openclaw \
  --thread-id 019d1897-2814-76f3-aec0-7c2414aaad39 \
  --conversation-id your-conversation-id
```

## Call The Team

服务启动后，你可以把这支团队当成一个本地接口来调用。

健康检查：

```bash
curl http://127.0.0.1:8787/health
```

直接呼叫团队：

```bash
curl -X POST http://127.0.0.1:8787/team/call \
  -H "Content-Type: application/json" \
  -d '{
    "text": "做一期南海局势节目",
    "auto_approve": true
  }'
```

查询任务状态：

```bash
curl http://127.0.0.1:8787/jobs/<job_id>
```

提交审核意见：

```bash
curl -X POST http://127.0.0.1:8787/jobs/<job_id>/review \
  -H "Content-Type: application/json" \
  -d '{
    "stage": "plan",
    "decision": "approve",
    "revision": 0
  }'
```

继续执行：

```bash
curl -X POST http://127.0.0.1:8787/jobs/<job_id>/resume \
  -H "Content-Type: application/json" \
  -d '{}'
```

## OpenClaw / WeChat Adapter Payloads

OpenClaw 风格任务入口：

```bash
curl -X POST http://127.0.0.1:8787/adapters/openclaw/task \
  -H "Content-Type: application/json" \
  -d '{
    "channel": "wechat",
    "message": {
      "text": "做一期比特币周报"
    },
    "auto_approve": false
  }'
```

微信风格审核入口：

```bash
curl -X POST http://127.0.0.1:8787/adapters/wechat/review \
  -H "Content-Type: application/json" \
  -d '{
    "job_id": "finance-xxxxxx",
    "stage": "plan",
    "decision": "approve",
    "revision": 0
  }'
```

当前接口返回：

- `job`：任务结果或当前状态
- `reply_text`：可直接回发给 OpenClaw / 微信的简短回复
- `artifacts`：生成产物路径列表

微信统一消息入口（推荐）：

```bash
curl -X POST http://127.0.0.1:8787/adapters/wechat/message \
  -H "Content-Type: application/json" \
  -d '{
    "channel": "openclaw-weixin",
    "account_id": "dd657bb7d0bb-im-bot",
    "conversation_id": "o9cq80-qlqa3aa_STcrwf4-ngE38@im.wechat",
    "message": {"text": "做一期南海局势节目"},
    "auto_approve": false
  }'
```

支持命令：

- `做一期...`：创建新任务
- `状态`：查看当前会话最近任务进度
- `通过`：对当前待审核节点执行 approve 并自动继续
- `修改：你的意见`：对当前待审核节点执行 revise 并自动继续
- `拒绝`：对当前待审核节点执行 reject 并自动继续
- `继续`：继续执行最近任务

OpenClaw 原生事件桥接入口（插件可直接对接）：

```bash
curl -X POST http://127.0.0.1:8787/adapters/openclaw/event \
  -H "Content-Type: application/json" \
  -d '{
    "account_id": "dd657bb7d0bb-im-bot",
    "msgs": [
      {
        "message_type": 1,
        "session_id": "wechat-room-x",
        "item_list": [
          {"type": 1, "text_item": {"text": "做一期南海局势节目"}}
        ]
      }
    ],
    "auto_approve": false
  }'
```

也支持单消息形态：

```bash
POST /adapters/openclaw/weixin/event
```

## Time-Driven Automation

定时任务定义在 `scheduler/jobs.yaml`，当前支持：

- `daily`：每天固定时刻
- `weekly`：指定星期 + 固定时刻

关键字段：

- `id`：任务唯一标识
- `enabled`：是否启用
- `schedule.time`：`HH:MM`
- `schedule.timezone`：建议 `Asia/Shanghai`
- `task.text`：要交给团队执行的自然语言任务
- `task.auto_approve`：是否自动通过审核节点

调度状态自动写入：

- `outputs/_scheduler_state.json`

同一个调度任务在同一自然日只会执行一次，避免重复触发。

## RWA Skills Layer

RWA workflow 现在有一层独立的 workspace 级 skills，位置在 `skills/`：

- `skills/rwa-news-research`
- `skills/cross-market-context`
- `skills/market-technical-analysis`
- `skills/research-report-writer`
- `skills/content-director-pack`

这层的作用是把 RWA workflow 的关键能力拆成可复用模块：

- `rwa-news-research` -> `news_digest.md`
- `cross-market-context` -> `macro_context.md`
- `market-technical-analysis` -> `technical_report.md`
- `research-report-writer` -> `research_report.md`
- `content-director-pack` -> `article_draft.md` / `script_outline.md` / `material_list.md`

对应关系与输入输出清单可见：

- `config/skills.yaml`
- `docs/workflows/rwa_weekly_deep_research.md`

如果后续要让 workflow 显式调用 skills，建议按这个顺序串联：

1. `$rwa-news-research`
2. `$cross-market-context`
3. `$market-technical-analysis`
4. `$research-report-writer`
5. `$content-director-pack`

## Shared Skill-Aware Runner

The project now records skill invocations for all main workflows through the shared runner in `core/skill_runner.py`.

Current behavior:

- RWA uses the dedicated workspace-level skills in `skills/`
- military, finance, and mixed workflows use shared virtual capability skills from `config/skills.yaml`
- every run can write `skill_runs.yaml` into the job directory for auditability

This keeps the existing workflows stable while making the project progressively more skill-aware.

## Manual Review Flow

默认不加 `--auto-approve` 时，流程会在审核节点暂停，并在 `outputs/<job_id>/reviews/` 生成审核文件。

1. 首次运行任务：

```bash
python3 main.py run "做一期南海局势节目"
```

2. 对某个审核节点提交决定：

```bash
python3 main.py review <job_id> plan approve
python3 main.py review <job_id> content_pack revise --note "开头冲突更强一些"
```

3. 继续执行：

```bash
python3 main.py resume <job_id>
```

## Output Artifacts

每个任务在 `outputs/<job_id>/` 下生成结构化产物：

- `request.yaml`
- `execution_plan.yaml`
- `review_plan.md`
- `research_brief.md`
- `script_outline.md`
- `storyboard.md`
- `avatar_script.md`（财经必产）
- `edit_plan.md`
- `skill_runs.yaml`（RWA workflow 的显式 skill 调用记录）
- `publish_pack.md`
- `result.json`

RWA workflow 额外产物：

- `news_digest.md`
- `macro_context.md`
- `technical_report.md`
- `research_report.md`
- `article_draft.md`
- `material_list.md`

## Tests

```bash
pytest
```

## Notes

- 当前版本工具层全部为 stub/mock，以保证工程可以本地跑通。
- `web_search`、`ffmpeg_edit`、`tts_generate`、`avatar_presenter` 等真实 API 接入留给下一阶段。
- 输出内容默认是结构化策划稿，不假装提供未经核验的事实结论。
- 当前 API 执行模型是同步阻塞式，适合本地 MVP；如果后续接真实长任务，建议再加任务队列和异步 worker。
