# rwa_weekly_deep_research Workflow 设计文档

## 1. Workflow 名称与目标

- Workflow 名称：`rwa_weekly_deep_research`
- 目标：围绕 RWA（Real World Assets）主线，按周生成一套结构化深度研究内容包，覆盖新闻调研、跨市场宏观背景、技术走势分析、综合研究报告、文章初稿、视频脚本提纲和素材整理。
- 与普通币圈周报的区别：
  - 研究主轴不是单一币种涨跌，而是 RWA 产业进展与结构变化。
  - BTC、黄金、NQ 作为宏观与市场参照系，用于解释流动性、风险偏好、成长资产估值与风险转移，不是唯一主角。
  - 输出目标偏研究型与内容生产型，兼容后续文章发布与视频制作链路。

## 2. 适用场景

- 每周固定生成一份 RWA 深度研究包，供内容团队审阅、选题、发布。
- 用户手动发起“做本周 RWA 深度研究”等指令时，触发完整工作流。
- 作为后续视频生产链的前置层，为数字人口播、剪辑、素材调度提供上游结构化产物。
- 作为高信息密度内容中台，为周报、专题、深度文章和视频解说共用同一份研究底稿。

## 3. 角色划分

### 3.1 RWA 研究总监

- 职责：
  - 定义本周核心研究问题。
  - 明确本期 RWA 主线与研究边界。
  - 设计本周输出顺序、风险点和审核节点。
- 产出：
  - `review_plan.md`

### 3.2 RWA 新闻研究员

- 职责：
  - 搜集过去一周 RWA 相关新闻与行业动态。
  - 分类为机构推进、监管动态、项目进展、市场炒作、基础设施变化。
  - 去重、筛选并提炼高可信信息。
- 产出：
  - `news_digest.md`

### 3.3 跨市场分析师

- 职责：
  - 研究 BTC、黄金、NQ 对 RWA 的宏观背景意义。
  - 输出流动性、风险偏好、避险、成长资产估值等解释框架。
- 产出：
  - `macro_context.md`

### 3.4 技术分析师

- 职责：
  - 分析 BTC、黄金、NQ 以及必要 RWA 相关标的的技术结构。
  - 输出周线、日线、关键位、回顾和下周观察点。
- 产出：
  - `technical_report.md`

### 3.5 首席策略师

- 职责：
  - 汇总新闻、宏观背景与技术分析。
  - 形成完整研究报告，提炼本周主结论、结构性变化与下周判断。
- 产出：
  - `research_report.md`

### 3.6 编导 / 内容统筹

- 职责：
  - 将研究报告改写为文章初稿与视频脚本提纲。
  - 输出素材需求与剪辑方向建议。
- 产出：
  - `article_draft.md`
  - `script_outline.md`
  - `material_list.md`

## 4. 阶段划分

### Stage 1：任务启动

- 执行角色：RWA 研究总监
- 目标：定义本周研究问题、研究范围、交付结构、审核要求。
- 输出：`review_plan.md`

### Stage 2：新闻采集与筛选

- 执行角色：RWA 新闻研究员
- 目标：完成过去一周 RWA 新闻的搜集、分类、去重与可信度整理。
- 输出：`news_digest.md`

### Stage 3：跨市场背景分析

- 执行角色：跨市场分析师
- 目标：建立 BTC、黄金、NQ 对 RWA 的宏观背景解释框架。
- 输出：`macro_context.md`

### Stage 4：技术走势分析

- 执行角色：技术分析师
- 目标：建立主要参照资产与必要 RWA 标的的技术结构观察。
- 输出：`technical_report.md`

### Stage 5：综合研究报告

- 执行角色：首席策略师
- 目标：整合新闻、宏观背景、技术结构，形成完整周度研究报告。
- 输出：`research_report.md`

### Stage 6：文章初稿

- 执行角色：编导 / 内容统筹
- 目标：基于研究报告生成面向图文发布的文章初稿。
- 输出：`article_draft.md`

### Stage 7：视频脚本与素材整理

- 执行角色：编导 / 内容统筹
- 目标：生成面向视频制作链路的脚本提纲与素材清单。
- 输出：
  - `script_outline.md`
  - `material_list.md`

## 5. 每个阶段的输入、输出、依赖

### Stage 1：任务启动

- 输入来源：
  - 用户请求文本
  - 调度任务默认指令
  - 既有模板配置与工作流配置
- 输入依赖：
  - 路由结果为 `rwa`
  - 模板：`templates/rwa_weekly_deep_research.yaml`
- 输出文件：
  - `review_plan.md`
- 输出格式建议：
  - 本周研究主题
  - 本周核心研究问题
  - 本周主线定义
  - 研究边界与不覆盖范围
  - 阶段清单
  - 风险点
  - 审核节点说明
- 审核：
  - 不单独审核

### Stage 2：新闻采集与筛选

- 输入来源：
  - `review_plan.md`
  - `web_search` 工具结果
  - 外部公开新闻源与项目公告
- 输入依赖：
  - Stage 1 已完成
- 输出文件：
  - `news_digest.md`
- 输出格式建议：
  - 本周新闻总览
  - 机构推进
  - 监管动态
  - 项目进展
  - 市场炒作与情绪扰动
  - 基础设施变化
  - 去重后的关键事件列表
  - 待进一步核验项
- 审核：
  - 不单独审核

### Stage 3：跨市场背景分析

- 输入来源：
  - `review_plan.md`
  - `news_digest.md`
  - 必要市场背景与公开宏观信息
- 输入依赖：
  - Stage 2 已完成
- 输出文件：
  - `macro_context.md`
- 输出格式建议：
  - 本周宏观背景摘要
  - BTC 对 RWA 的背景意义
  - 黄金对 RWA 的背景意义
  - NQ 对 RWA 的背景意义
  - 流动性 / 风险偏好 / 避险 / 成长估值四维分析
  - 对本周 RWA 研究主线的支撑结论
- 审核：
  - 不单独审核

### Stage 4：技术走势分析

- 输入来源：
  - `review_plan.md`
  - `macro_context.md`
  - 必要市场价格与技术观察输入
- 输入依赖：
  - Stage 3 已完成
- 输出文件：
  - `technical_report.md`
- 输出格式建议：
  - 观察标的列表
  - 周线结构
  - 日线结构
  - 关键支撑与压力位
  - 本周走势回顾
  - 与 RWA 主线相关的市场验证
  - 下周观察点
- 审核：
  - 不单独审核

### Stage 5：综合研究报告

- 输入来源：
  - `news_digest.md`
  - `macro_context.md`
  - `technical_report.md`
- 输入依赖：
  - Stage 2、3、4 已完成
- 输出文件：
  - `research_report.md`
- 输出格式建议：
  - 本周 RWA 核心结论
  - 本周关键新闻与结构性进展
  - BTC / 黄金 / NQ 的宏观背景
  - 技术走势与市场验证
  - 下周预测
  - 风险提示
- 审核：
  - 需要审核，作为审核点 A

### Stage 6：文章初稿

- 输入来源：
  - `research_report.md`
- 输入依赖：
  - Stage 5 已审核通过
- 输出文件：
  - `article_draft.md`
- 输出格式建议：
  - 标题建议
  - 导语
  - 正文主体
  - 本周结论
  - 风险提示
  - 下周前瞻
- 审核：
  - 不单独强制审核

### Stage 7：视频脚本与素材整理

- 输入来源：
  - `research_report.md`
  - `article_draft.md`
- 输入依赖：
  - Stage 6 已完成
- 输出文件：
  - `script_outline.md`
  - `material_list.md`
- 输出格式建议：
  - `script_outline.md`
    - 视频标题
    - 开头钩子
    - 结构段落
    - 每段核心观点
    - 结尾收束
    - 可延展为口播稿的说明
  - `material_list.md`
    - 画面素材方向
    - 图表清单
    - 数据卡片建议
    - 引用素材类别
    - 后续剪辑建议
- 审核：
  - 可选审核，作为审核点 B

## 6. 审核点设计

### 审核点 A：研究报告审核

- 触发时机：
  - `research_report.md` 生成后
- 审核目的：
  - 确认本周研究主线、结构判断、风险表述和结论边界是否符合预期
- 用户指令：
  - `通过`
  - `继续`
  - `修改：xxx`
  - `拒绝`
- 系统行为：
  - `通过`：进入 Stage 6
  - `继续`：等同继续当前任务；若已在待审核阶段，则可视作恢复执行
  - `修改：xxx`：记录 revision note，回退到 Stage 5 重做
  - `拒绝`：终止当前 workflow

### 审核点 B：脚本与素材审核

- 触发时机：
  - `script_outline.md` 和 `material_list.md` 完成后
- 审核目的：
  - 确认视频化表达方向、内容节奏和素材组织是否适合进入后续制作链
- 说明：
  - 该审核点可配置为可选暂停
  - 在自动周度运行中可默认自动通过
  - 在手动高优先级任务中可保留人工审核

## 7. 调度方式

### 手动触发

- 支持消息示例：
  - `做本周 RWA 深度研究`
  - `生成本周 RWA 周报`
  - `开始本周 RWA 研究流程`

### 周度定时触发

- 建议调度任务：
  - 每周六上午运行一次
- 示例：
  - 周六 `09:00`，`Asia/Shanghai`
- 调度任务说明：
  - 文本任务默认写为：`做本周 RWA 深度研究`
  - 可默认 `auto_approve: true`，减少例行周报的人为阻塞

## 8. 与现有财经 workflow 的关系

- 现有 `crypto_finance_pipeline` 仍然负责普通数字货币节目的周报、快评与口播内容包。
- `rwa_weekly_deep_research` 是一条新增主 workflow，不应覆盖或污染现有财经流程。
- 两者关系：
  - 共用统一编排层、审核机制、调度器、工具注册表和消息入口。
  - 路由上属于新增独立分类，优先根据 `RWA / real world assets / 资产上链 / tokenized treasuries / tokenized funds` 等关键词识别。
  - 内容目标不同：
    - `crypto_finance_pipeline`：节目化、口播化、周报化
    - `rwa_weekly_deep_research`：研究化、深度化、兼容文章与视频生产

## 9. 未来可扩展点

- 增加真实 `web_search` 与资料源聚合，提高新闻与研究质量。
- 增加行情数据接口，为技术分析提供真实数值输入。
- 增加图表生成模块，直接产出研究图卡与视频图表素材。
- 增加文章发布与视频制作后处理节点，形成端到端内容工厂。
- 增加 `delivery` 层，把研究摘要、审核请求和完成通知直接回传到微信。
- 增加多模板支持，例如：
  - `RWA 周报`
  - `RWA 专题深挖`
  - `RWA 监管追踪`

## 10. 风险与边界

### 风险

- 新闻真实性与去重准确度依赖工具层质量，当前 mock 工具阶段只能保证链路，不保证研究真实性。
- RWA 涉及宏观、监管、链上资产、传统金融与市场结构，若研究边界不明确，内容容易发散。
- 技术分析与研究结论必须明确区分“观察”“推演”“事实”，避免误导表达。

### 边界

- 该 workflow 当前产出标准 Markdown 文件，不直接生成最终视频或数字人口播稿。
- 该 workflow 优先服务“深度研究内容包”，不是即时快讯系统。
- BTC、黄金、NQ 在此流程中仅作为 RWA 的背景解释资产，不替代 RWA 主体研究。
- 真实外部 API、行情源、图表源未接入前，输出应默认视为“结构化研究草案”，仍需人工审阅。

## 11. Workflow 与 Skills 的映射

本 workflow 现在已经有对应的 workspace 级 skills，可按阶段调用：

| Workflow Stage | 默认执行角色 | 对应 Skill | 主要输入 | 主要输出 |
| --- | --- | --- | --- | --- |
| Stage 1：任务启动 | RWA 研究总监 | 无独立 skill，保留 workflow 内部编排 | 用户请求、模板配置 | `review_plan.md` |
| Stage 2：新闻采集与筛选 | RWA 新闻研究员 | `rwa-news-research` | 搜索结果、新闻链接、正文、`review_plan.md` | `news_digest.md` |
| Stage 3：跨市场背景分析 | 跨市场分析师 | `cross-market-context` | `review_plan.md`、`news_digest.md`、宏观材料 | `macro_context.md` |
| Stage 4：技术走势分析 | 技术分析师 | `market-technical-analysis` | `review_plan.md`、`macro_context.md`、行情与图表材料 | `technical_report.md` |
| Stage 5：综合研究报告 | 首席策略师 | `research-report-writer` | `news_digest.md`、`macro_context.md`、`technical_report.md` | `research_report.md` |
| Stage 6-7：内容生产资产 | 编导 / 内容统筹 | `content-director-pack` | `research_report.md` 及必要上游文件 | `article_draft.md`、`script_outline.md`、`material_list.md` |

调用原则：

- workflow 负责任务编排、审核暂停、调度和状态机。
- skill 负责具体能力执行规则和输出格式约束。
- 后续若需要把 workflow 改造成“显式技能调用模式”，优先复用这些 skill，而不是再次在 workflow 内重复定义规则。

## 12. 建议的文件落地规范

- 所有文件统一落到 `outputs/{job_id}/`
- 至少产出以下文件：
  - `review_plan.md`
  - `news_digest.md`
  - `macro_context.md`
  - `technical_report.md`
  - `research_report.md`
  - `article_draft.md`
  - `script_outline.md`
  - `material_list.md`
- 状态管理与命名风格保持与现有 workflow 一致。

## 13. 当前使用建议

在当前项目中，可以把这条 workflow 理解为：

- `workflow = 编排层`
- `skills = 能力层`

推荐协同顺序：

1. workflow 根据任务创建 `job_id`
2. `rwa-news-research` 生成 `news_digest.md`
3. `cross-market-context` 生成 `macro_context.md`
4. `market-technical-analysis` 生成 `technical_report.md`
5. `research-report-writer` 生成 `research_report.md`
6. 审核点 A 暂停
7. `content-director-pack` 生成内容资产包
8. 审核点 B 可选暂停

## 14. 实现建议摘要

- 新增独立类别：`rwa`
- 新增 workflow：`workflows/rwa_weekly_deep_research_pipeline.py`
- 新增模板：`templates/rwa_weekly_deep_research.yaml`
- 新增调度任务：周六上午
- 新增或复用 prompts / agent 输出逻辑：
  - 优先复用现有 `director_agent`、`researcher_agent`、`scriptwriter_agent`
  - 对于 RWA 专属角色，建议在 agent runner 中新增专用处理分支，避免强行塞进现有财经周报逻辑
- 审核点至少保留：
  - `research_report_review`
  - `content_pack_review`
