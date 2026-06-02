---
name: research-report-writer
description: use this skill when the task is to synthesize news_digest.md, macro_context.md, and technical_report.md into a complete weekly rwa research report in markdown.
---

# research-report-writer

Use this skill when the workflow has already produced `news_digest.md`, `macro_context.md`, and `technical_report.md`, and now needs a single integrated `research_report.md`.

## Trigger

Use this skill when:
- the workflow asks for the weekly RWA integrated report
- the upstream markdown inputs already exist
- the user wants a deeper RWA weekly report rather than a quick market note

Do not use this skill for first-pass news collection or article/script adaptation.

## Inputs To Read

Primary inputs:
- `news_digest.md`
- `macro_context.md`
- `technical_report.md`
- `review_plan.md` when available

If you need structure and reasoning rules, read:
- [report-outline.md](references/report-outline.md)
- [inference-rules.md](references/inference-rules.md)

## Output

Write one markdown file:
- `research_report.md`

## Required Output Structure

`research_report.md` must contain:
1. `# Research Report`
2. `## 本周 RWA 核心结论`
3. `## 本周关键新闻与结构性进展`
4. `## BTC / 黄金 / NQ 的宏观背景`
5. `## 技术走势与市场验证`
6. `## 下周预测`
7. `## 风险提示`

## Execution Rules

1. Start with the week's core conclusion, not with a chronology dump.
2. Integrate the three upstream files instead of summarizing each one separately.
3. Clearly separate:
   - confirmed facts
   - analytical inference
   - forward-looking observation
4. Keep RWA as the center and use BTC, gold, and NQ only as supporting context.
5. End with explicit risk warnings and next-week watch points.

## Do Not

- do not merely concatenate upstream markdown files
- do not let macro commentary overshadow RWA structure
- do not produce exaggerated certainty
- do not remove risk language to make the report sound stronger

## Handoff

This skill feeds:
- the workflow review gate after `research_report.md`
- `content-director-pack` after approval
