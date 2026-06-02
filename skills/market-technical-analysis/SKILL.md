---
name: market-technical-analysis
description: use this skill when the task is to turn btc, gold, nq, and selected rwa-related market materials into a structured technical markdown report for weekly rwa research.
---

# market-technical-analysis

Use this skill when the workflow needs `technical_report.md` and the job is to summarize weekly and daily technical structure, key levels, and next-week watch points for BTC, gold, NQ, and any necessary RWA-related instruments.

## Trigger

Use this skill when:
- the task explicitly asks for technical analysis in the RWA workflow
- you have price structure notes, chart observations, or market level summaries
- the workflow needs `technical_report.md`

Do not use this skill for pure macro interpretation or final report synthesis.

## Inputs To Read

Read the minimum needed:
- `review_plan.md`
- `macro_context.md` if available
- chart notes, OHLC summaries, level notes, or prior weekly technical observations

If you need formatting guidance, read:
- [technical-template.md](references/technical-template.md)

## Output

Write one markdown file:
- `technical_report.md`

## Required Output Structure

`technical_report.md` should contain:
1. `# Technical Report`
2. `## 观察标的列表`
3. one section per instrument
4. `## 总结`

Each instrument section should include:
- 周线趋势
- 日线结构
- 关键支撑阻力
- 上周回顾
- 下周观察位

## Execution Rules

1. Use technicals as a validation layer, not the main narrative.
2. Cover BTC, gold, and NQ by default.
3. Add RWA-related instruments only when they are directly relevant to the week's research theme.
4. Keep statements observational and conditional.
5. End with a short explanation of what the technical layer validates or fails to validate for the RWA mainline.

## Do Not

- do not turn this into trade advice
- do not overfit commentary to one candle or one session
- do not replace sector research with chart language
- do not ignore macro context already established upstream

## Handoff

This skill feeds:
- `research-report-writer`

It should make the next writer's job easier by offering clear, compact validation notes instead of dense trader jargon.
