from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional


def _extract_text(payload: Dict[str, Any]) -> str:
    if isinstance(payload.get("message"), dict):
        message = payload["message"]
        return str(message.get("text") or message.get("content") or "").strip()
    for key in ["text", "content", "query", "task"]:
        value = payload.get(key)
        if value:
            return str(value).strip()
    return ""


def normalize_task_request(payload: Dict[str, Any], default_source: str) -> Dict[str, Any]:
    text = _extract_text(payload)
    metadata = {
        "channel": payload.get("channel"),
        "sender": payload.get("sender"),
        "session_id": payload.get("session_id"),
        "raw_keys": sorted(payload.keys()),
    }
    return {
        "text": text,
        "auto_approve": bool(payload.get("auto_approve", False)),
        "source": str(payload.get("source", default_source)),
        "metadata": metadata,
    }


def normalize_review_request(payload: Dict[str, Any], default_source: str) -> Dict[str, Any]:
    return {
        "job_id": str(payload.get("job_id", "")).strip(),
        "stage": str(payload.get("stage", "")).strip(),
        "decision": str(payload.get("decision", "")).strip(),
        "note": str(payload.get("note", "")).strip(),
        "revision": int(payload.get("revision", 0)),
        "source": str(payload.get("source", default_source)),
    }


def normalize_conversation_info(payload: Dict[str, Any], default_channel: str) -> Dict[str, str]:
    return {
        "channel": str(payload.get("channel", default_channel)).strip(),
        "account_id": str(payload.get("account_id", payload.get("accountId", "default"))).strip(),
        "conversation_id": str(
            payload.get("conversation_id")
            or payload.get("conversationId")
            or payload.get("session_id")
            or "default"
        ).strip(),
    }


def parse_wechat_text_action(text: str) -> Dict[str, Optional[str]]:
    stripped = text.strip()
    lowered = stripped.lower()
    if not stripped:
        return {"action": "unknown", "note": None}

    if stripped in {"状态", "进度", "status"}:
        return {"action": "status", "note": None}
    if stripped in {"继续", "resume", "继续执行"}:
        return {"action": "resume", "note": None}
    if stripped in {"通过", "approve", "批准"}:
        return {"action": "approve", "note": None}
    if stripped in {"拒绝", "reject"}:
        return {"action": "reject", "note": None}
    if stripped.startswith("修改") or lowered.startswith("revise"):
        note = ""
        if ":" in stripped:
            note = stripped.split(":", 1)[1].strip()
        elif "：" in stripped:
            note = stripped.split("：", 1)[1].strip()
        return {"action": "revise", "note": note}
    return {"action": "task", "note": None}


def extract_text_from_weixin_item_list(item_list: List[Dict[str, Any]]) -> str:
    chunks: List[str] = []
    for item in item_list:
        if int(item.get("type", 0)) != 1:
            continue
        text_item = item.get("text_item", {})
        if isinstance(text_item, dict):
            text = str(text_item.get("text", "")).strip()
            if text:
                chunks.append(text)
    return "\n".join(chunks).strip()


def normalize_openclaw_weixin_events(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Normalize openclaw-weixin event payloads into text commands."""
    events: List[Dict[str, Any]] = []
    account_id = str(
        payload.get("account_id")
        or payload.get("accountId")
        or payload.get("to_user_id")
        or "default"
    ).strip()

    # Shape A: direct single message object under "msg"
    msg = payload.get("msg")
    if isinstance(msg, dict):
        text = extract_text_from_weixin_item_list(list(msg.get("item_list", [])))
        if text:
            events.append(
                {
                    "channel": "openclaw-weixin",
                    "account_id": account_id,
                    "conversation_id": str(
                        msg.get("session_id") or msg.get("from_user_id") or payload.get("conversation_id") or "default"
                    ).strip(),
                    "text": text,
                    "source": "openclaw_weixin_event",
                }
            )

    # Shape B: polling batch under "msgs"
    msgs = payload.get("msgs")
    if isinstance(msgs, list):
        for item in msgs:
            if not isinstance(item, dict):
                continue
            message_type = item.get("message_type")
            if message_type is not None and int(message_type) != 1:
                continue
            text = extract_text_from_weixin_item_list(list(item.get("item_list", [])))
            if not text:
                continue
            events.append(
                {
                    "channel": "openclaw-weixin",
                    "account_id": account_id,
                    "conversation_id": str(
                        item.get("session_id") or item.get("from_user_id") or payload.get("conversation_id") or "default"
                    ).strip(),
                    "text": text,
                    "source": "openclaw_weixin_event",
                }
            )

    # Shape C: already-flat payload with text-like fields
    if not events:
        text = _extract_text(payload)
        if text:
            conversation = normalize_conversation_info(payload, default_channel="openclaw-weixin")
            events.append(
                {
                    "channel": conversation["channel"],
                    "account_id": conversation["account_id"],
                    "conversation_id": conversation["conversation_id"],
                    "text": text,
                    "source": str(payload.get("source", "openclaw_weixin_event")),
                }
            )
    return events


def build_team_reply(result: Dict[str, Any]) -> str:
    final_status = result.get("final_status") or result.get("status") or "unknown"
    job_id = result.get("job_id", "unknown")
    if final_status == "needs_review":
        stage = result.get("review_stage", "unknown")
        return (
            f"任务 {job_id} 已进入审核节点：{stage}。"
            " 你可以提交 approve / revise / reject，然后继续推进团队工作。"
        )
    if final_status == "completed":
        artifacts = result.get("artifacts", [])
        interesting = [item.get("artifact_type") for item in artifacts if item.get("artifact_type")]
        summary = "、".join(interesting[:5]) or "内容产物"
        return f"任务 {job_id} 已完成，团队已经交付：{summary}。"
    if final_status == "rejected":
        return f"任务 {job_id} 已被拒绝，团队已停止当前流程。"
    return f"任务 {job_id} 当前状态：{final_status}。"


def build_job_summary(snapshot: Dict[str, Any]) -> Dict[str, Any]:
    state = snapshot.get("state", {})
    request = snapshot.get("request", {})
    result = snapshot.get("result", {})
    return {
        "job_id": snapshot.get("job_id"),
        "request_text": request.get("request_text"),
        "category": request.get("category"),
        "status": state.get("status"),
        "current_stage": state.get("current_stage"),
        "pending_review_stage": state.get("pending_review_stage"),
        "artifact_count": len(snapshot.get("artifacts", [])),
        "final_status": result.get("final_status"),
    }


def artifact_paths(snapshot: Dict[str, Any]) -> Iterable[str]:
    for item in snapshot.get("artifacts", []):
        path = item.get("path")
        if path:
            yield path
