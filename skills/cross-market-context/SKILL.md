---
name: cross-market-context
description: use this skill when the task is to explain how btc, gold, nq, rates, dollar, liquidity, and risk appetite shape the macro context for an rwa research output.
---

# cross-market-context

Use this skill when the workflow needs `macro_context.md` for an RWA report and the job is to interpret BTC, gold, NQ, rates, dollar, liquidity, and risk appetite as background variables around the RWA mainline.

## Trigger

Use this skill when:
- the request asks for cross-market context around RWA
- the workflow needs `macro_context.md`
- you have `review_plan.md` or `news_digest.md` and need macro framing

Do not use this skill for news collection, chart-level technical analysis, or final report writing.

## Inputs To Read

Read only relevant upstream context:
- `review_plan.md`
- `news_digest.md`
- macro notes or market summaries for BTC, gold, NQ, rates, and USD

If you need the output layout, read:
- [macro-context-template.md](references/macro-context-template.md)

## Output

Write one markdown file:
- `macro_context.md`

Prefer the active job directory. Keep the file concise, structured, and directly reusable by the report writer.

## Required Output Structure

`macro_context.md` should contain:
1. `# Macro Context`
2. `## 本周宏观背景摘要`
3. `## 风险偏好`
4. `## 流动性环境`
5. `## 利率与美元背景`
6. `## 避险逻辑`
7. `## 成长资产估值环境`
8. `## BTC / 黄金 / NQ 对 RWA 的意义`
9. `## 对本周 RWA 主线的支撑结论`

## Execution Rules

1. Keep RWA as the center of gravity.
2. Treat BTC, gold, and NQ as reference systems, not the main subject.
3. Explain why each macro variable matters for RWA, not just what happened.
4. Separate observed backdrop from forward-looking inference.
5. End with a short statement of what this macro setup implies for the week's RWA theme.

## Do Not

- do not rewrite the news digest
- do not produce price targets
- do not drift into a generic weekly crypto market recap
- do not let one macro asset dominate the entire file

## Handoff

This skill feeds:
- `research-report-writer`
- optionally `content-director-pack` when macro framing needs to appear in article or script sections
