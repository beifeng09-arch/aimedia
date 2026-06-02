from __future__ import annotations

import json
import os
import shutil
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional


def _now_ms() -> int:
    return int(time.time() * 1000)


@dataclass
class BindingTarget:
    channel: str
    account_id: str
    conversation_id: str
    parent_conversation_id: Optional[str] = None

    def to_dict(self) -> Dict[str, str]:
        payload = {
            "channel": self.channel,
            "accountId": self.account_id,
            "conversationId": self.conversation_id,
        }
        if self.parent_conversation_id:
            payload["parentConversationId"] = self.parent_conversation_id
        return payload


class OpenClawBindingManager:
    def __init__(self, state_path: Optional[Path] = None) -> None:
        self.state_path = Path(
            state_path or Path.home() / ".openclaw" / "openclaw-codex-app-server" / "state.json"
        )

    def load_state(self) -> Dict[str, Any]:
        if not self.state_path.exists():
            raise FileNotFoundError(f"OpenClaw binding state not found: {self.state_path}")
        with self.state_path.open("r", encoding="utf-8") as handle:
            return json.load(handle)

    def save_state(self, payload: Dict[str, Any]) -> Path:
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        with self.state_path.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
        return self.state_path

    def backup_state(self) -> Path:
        backup_path = self.state_path.with_suffix(f".json.bak.{int(time.time())}")
        shutil.copy2(self.state_path, backup_path)
        return backup_path

    def list_bindings(self) -> List[Dict[str, Any]]:
        state = self.load_state()
        return list(state.get("bindings", []))

    def infer_target(
        self,
        preferred_channel: str = "openclaw-weixin",
        conversation_id: Optional[str] = None,
    ) -> BindingTarget:
        bindings = self.list_bindings()
        candidates = []
        for item in bindings:
            conversation = item.get("conversation", {})
            if conversation.get("channel") != preferred_channel:
                continue
            if conversation_id and conversation.get("conversationId") != conversation_id:
                continue
            candidates.append(item)

        if not candidates:
            raise ValueError(
                f"No existing OpenClaw binding found for channel={preferred_channel}"
                + (f" conversation_id={conversation_id}" if conversation_id else "")
            )

        selected = sorted(candidates, key=lambda item: item.get("updatedAt", 0), reverse=True)[0]
        conversation = selected["conversation"]
        return BindingTarget(
            channel=conversation["channel"],
            account_id=conversation["accountId"],
            conversation_id=conversation["conversationId"],
            parent_conversation_id=conversation.get("parentConversationId"),
        )

    def bind_thread(
        self,
        thread_id: str,
        workspace_dir: str,
        target: BindingTarget,
    ) -> Dict[str, Any]:
        state = self.load_state()
        bindings = list(state.get("bindings", []))
        updated_binding = {
            "conversation": target.to_dict(),
            "sessionKey": f"openclaw-codex-app-server:thread:{thread_id}",
            "threadId": thread_id,
            "workspaceDir": workspace_dir,
            "updatedAt": _now_ms(),
        }
        normalized_key = self._conversation_key(target.to_dict())
        replaced = False
        next_bindings = []
        for item in bindings:
            if self._conversation_key(item.get("conversation", {})) == normalized_key:
                next_bindings.append(updated_binding)
                replaced = True
            else:
                next_bindings.append(item)
        if not replaced:
            next_bindings.append(updated_binding)

        state["bindings"] = next_bindings
        self.save_state(state)
        return updated_binding

    @staticmethod
    def restart_gateway() -> subprocess.CompletedProcess:
        uid = str(os.getuid())
        return subprocess.run(
            ["launchctl", "kickstart", "-k", f"gui/{uid}/ai.openclaw.gateway"],
            check=False,
            capture_output=True,
            text=True,
        )

    @staticmethod
    def _conversation_key(conversation: Dict[str, Any]) -> str:
        return "::".join(
            [
                str(conversation.get("channel", "")).strip().lower(),
                str(conversation.get("accountId", "")).strip(),
                str(conversation.get("conversationId", "")).strip(),
                str(conversation.get("parentConversationId", "")).strip(),
            ]
        )
