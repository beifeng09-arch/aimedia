from __future__ import annotations

import os
from typing import Dict, Optional


class LLMClient:
    """Reserved interface for a future prompt-based classifier or agent backend."""

    def __init__(self, provider: str = "mock", model: str = "mock-director-v1") -> None:
        self.provider = provider
        self.model = model

    @property
    def enabled(self) -> bool:
        return self.provider != "mock" and bool(os.getenv("OPENAI_API_KEY"))

    def classify_task(self, text: str, categories: Dict[str, Dict[str, object]]) -> Optional[str]:
        """Return a category string when a real LLM backend is available."""
        if not self.enabled:
            return None

        lowered = text.lower()
        if "比特币" in text or "btc" in lowered or "加密" in text:
            return "finance"
        if "南海" in text or "军情" in text or "军事" in text:
            return "military"
        return None
