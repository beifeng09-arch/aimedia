from __future__ import annotations

from typing import Any, Dict

from tools.base import execute_with_guard


def _handler(input_data: Dict[str, Any]) -> Dict[str, Any]:
    query = input_data.get("query", "未命名查询")
    return {
        "query": query,
        "sources": [
            {"title": f"{query} - 公开信息线索 A", "url": "https://example.com/source-a"},
            {"title": f"{query} - 公开信息线索 B", "url": "https://example.com/source-b"},
            {"title": f"{query} - 公开信息线索 C", "url": "https://example.com/source-c"},
        ],
    }


def execute(input: dict) -> dict:
    return execute_with_guard("web_search", input, _handler)
