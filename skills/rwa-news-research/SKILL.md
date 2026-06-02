---
name: rwa-news-research
description: use this skill when the task is to collect, filter, classify, and summarize the past week's rwa news into a reusable markdown digest for downstream research or content workflows.
---

# rwa-news-research

Use this skill when the request is about weekly RWA news collection, source filtering, taxonomy tagging, de-duplication, or building `news_digest.md` for the `rwa_weekly_deep_research` workflow.

## Trigger

Use this skill when at least one of these is true:
- the user asks for this week's RWA news digest
- the workflow needs `news_digest.md`
- the input is a set of search results, article links, article excerpts, or raw news bullets about RWA

Do not use this skill for macro analysis, technical chart reading, or full report synthesis.

## Inputs To Read

Read only what is needed:
- search results, article URLs, article text, or prior collected news notes
- the current job request in `request.yaml` or `review_plan.md` if available
- upstream topic framing from the RWA workflow

If you need classification rules, read:
- [source-priority.md](references/source-priority.md)
- [news-taxonomy.md](references/news-taxonomy.md)

## Output

Write one markdown file:
- `news_digest.md`

Prefer writing into the active job directory under `outputs/{job_id}/`. If no job directory is provided, write into the workspace path requested by the caller.

## Required Output Structure

`news_digest.md` should contain these sections in order:
1. `# News Digest`
2. `## 本周新闻总览`
3. `## 机构推进`
4. `## 监管动态`
5. `## 项目进展`
6. `## 基础设施变化`
7. `## 市场炒作 / 叙事噪音`
8. `## 去重与筛选原则`
9. `## 待进一步核验项`

Within each news section:
- group related items instead of repeating near-duplicate headlines
- keep the factual statement separate from interpretation
- mark confidence as `high`, `medium`, or `low`

## Execution Rules

1. Prefer official releases, regulated institutions, primary reporting, and well-attributed mainstream reporting.
2. Separate real institutional or infrastructure progress from narrative noise.
3. Collapse duplicate coverage of the same event into one entry.
4. When facts are incomplete, say what is known and what still needs verification.
5. Keep the digest useful for the next skill, not optimized for flashy writing.

## Do Not

- do not turn this into a macro report
- do not write technical chart commentary
- do not produce investment advice
- do not present rumors as confirmed events
- do not let BTC or general crypto market noise replace the RWA mainline

## Handoff

This skill feeds:
- `cross-market-context` for macro framing
- `research-report-writer` for integrated synthesis

It should leave the downstream agent with a clean, structured, non-duplicative `news_digest.md`.
