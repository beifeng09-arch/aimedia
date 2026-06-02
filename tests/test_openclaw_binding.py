import json
from pathlib import Path

from integrations.openclaw_binding import OpenClawBindingManager


def _write_state(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "version": 1,
        "bindings": [
            {
                "conversation": {
                    "channel": "openclaw-weixin",
                    "accountId": "bot-account",
                    "conversationId": "wechat-room-1",
                    "parentConversationId": "wechat-room-1",
                },
                "sessionKey": "openclaw-codex-app-server:thread:old-thread",
                "threadId": "old-thread",
                "workspaceDir": "/tmp/old-workspace",
                "updatedAt": 100,
            }
        ],
        "pendingBinds": [],
        "pendingRequests": [],
        "callbacks": [],
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def test_bind_thread_updates_existing_conversation(tmp_path):
    state_path = tmp_path / "state.json"
    _write_state(state_path)
    manager = OpenClawBindingManager(state_path=state_path)

    target = manager.infer_target()
    binding = manager.bind_thread(
        thread_id="thread-123",
        workspace_dir="/Users/heyu/Documents/Projects/AI Media",
        target=target,
    )

    updated = manager.load_state()
    assert binding["threadId"] == "thread-123"
    assert binding["workspaceDir"] == "/Users/heyu/Documents/Projects/AI Media"
    assert updated["bindings"][0]["sessionKey"] == "openclaw-codex-app-server:thread:thread-123"


def test_bind_thread_appends_when_conversation_missing(tmp_path):
    state_path = tmp_path / "state.json"
    _write_state(state_path)
    manager = OpenClawBindingManager(state_path=state_path)

    target = manager.infer_target()
    target.conversation_id = "wechat-room-2"
    binding = manager.bind_thread(
        thread_id="thread-xyz",
        workspace_dir="/tmp/new-workspace",
        target=target,
    )

    updated = manager.load_state()
    assert len(updated["bindings"]) == 2
    assert updated["bindings"][-1]["threadId"] == "thread-xyz"
    assert binding["workspaceDir"] == "/tmp/new-workspace"
