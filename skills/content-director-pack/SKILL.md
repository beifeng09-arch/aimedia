---
name: content-director-pack
description: use this skill when the task is to convert a completed rwa research report into article, script, material, and optional edit planning markdown assets for content production.
---

# content-director-pack

Use this skill after `research_report.md` is approved and the workflow needs downstream content assets for article publishing or video production.

## Trigger

Use this skill when:
- the workflow asks for `article_draft.md`, `script_outline.md`, or `material_list.md`
- the user wants a research report adapted into content production assets
- `research_report.md` already exists

Do not use this skill to write the primary research report itself.

## Inputs To Read

Primary input:
- `research_report.md`

Optional upstream context:
- `review_plan.md`
- `news_digest.md`
- `macro_context.md`
- `technical_report.md`

If you need formatting guidance, read:
- [article-template.md](references/article-template.md)
- [script-template.md](references/script-template.md)
- [material-list-template.md](references/material-list-template.md)

## Output

Write these markdown files:
- `article_draft.md`
- `script_outline.md`
- `material_list.md`

Optional:
- `edit_plan.md`

## Execution Rules

1. Preserve the report's logic while changing the form.
2. Make the article readable and coherent for a depth-content audience.
3. Make the script outline scannable for a producer or scriptwriter.
4. Make the material list concrete enough for charts, B-roll, screenshots, and graphics.
5. If you write `edit_plan.md`, keep it lightweight and production-oriented.

## Do Not

- do not rewrite the research report from scratch
- do not flatten the nuance into a hype thread
- do not produce vague material notes like “add some charts”
- do not assume video publishing APIs or editing systems are available

## Handoff

This skill feeds:
- the workflow's optional content review gate
- later video, subtitle, and edit workflows

It should leave the next agent with clean production assets, not another research memo.
