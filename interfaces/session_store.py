from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional

from core.logging_utils import ensure_directory, load_json, write_json


class ConversationSessionStore:
    """Stores latest job mapping per external conversation."""

    def __init__(self, path: Path) -> None:
        self.path = Path(path)

    def _load(self) -> Dict[str, Dict[str, str]]:
        return load_json(self.path, default={"conversations": {}})

    def _save(self, payload: Dict[str, Dict[str, str]]) -> Path:
        ensure_directory(self.path.parent)
        return write_json(self.path, payload)

    @staticmethod
    def build_key(channel: str, account_id: str, conversation_id: str) -> str:
        return "::".join([channel.strip().lower(), account_id.strip(), conversation_id.strip()])

    def set_latest_job(
        self,
        channel: str,
        account_id: str,
        conversation_id: str,
        job_id: str,
    ) -> Path:
        payload = self._load()
        key = self.build_key(channel, account_id, conversation_id)
        payload.setdefault("conversations", {})[key] = {
            "channel": channel,
            "account_id": account_id,
            "conversation_id": conversation_id,
            "latest_job_id": job_id,
        }
        return self._save(payload)

    def get_latest_job(
        self,
        channel: str,
        account_id: str,
        conversation_id: str,
    ) -> Optional[str]:
        payload = self._load()
        key = self.build_key(channel, account_id, conversation_id)
        entry = payload.get("conversations", {}).get(key)
        if not entry:
            return None
        return entry.get("latest_job_id")
