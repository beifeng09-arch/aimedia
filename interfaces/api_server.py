from __future__ import annotations

import json
import os
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, Optional
from urllib.parse import urlparse

from core.models import to_serializable
from core.orchestrator import MediaOrchestrator
from interfaces.contracts import (
    artifact_paths,
    build_job_summary,
    build_team_reply,
    normalize_conversation_info,
    normalize_openclaw_weixin_events,
    normalize_review_request,
    normalize_task_request,
    parse_wechat_text_action,
)
from interfaces.session_store import ConversationSessionStore


class MediaAgentAPIServer:
    def __init__(
        self,
        root_dir: Optional[Path] = None,
        host: Optional[str] = None,
        port: Optional[int] = None,
        output_dir: Optional[Path] = None,
        log_dir: Optional[Path] = None,
    ) -> None:
        self.root_dir = Path(root_dir or Path(__file__).resolve().parents[1])
        self.orchestrator = MediaOrchestrator(
            root_dir=self.root_dir,
            output_dir=output_dir,
            log_dir=log_dir,
        )
        service_cfg = self.orchestrator.app_config.get("service", {})
        resolved_host = host if host is not None else os.getenv("MEDIA_AGENT_API_HOST") or service_cfg.get("host", "127.0.0.1")
        resolved_port = (
            port
            if port is not None
            else int(os.getenv("MEDIA_AGENT_API_PORT") or service_cfg.get("port", 8787))
        )
        self.host = resolved_host
        self.port = int(resolved_port)
        self.httpd = ThreadingHTTPServer((self.host, self.port), self._build_handler())

    def serve_forever(self) -> None:
        bound_host, bound_port = self.httpd.server_address
        print(f"Media agent API listening on http://{bound_host}:{bound_port}")
        self.httpd.serve_forever()

    def shutdown(self) -> None:
        self.httpd.shutdown()
        self.httpd.server_close()

    def _build_handler(self):
        orchestrator = self.orchestrator
        session_store = ConversationSessionStore(orchestrator.output_dir / "_session_index.json")

        class Handler(BaseHTTPRequestHandler):
            def _handle_wechat_text(
                self,
                conversation: Dict[str, str],
                text: str,
                source: str,
                auto_approve: bool,
            ) -> Dict[str, Any]:
                action = parse_wechat_text_action(text)

                if action["action"] == "task":
                    result = orchestrator.run_request(
                        text,
                        auto_approve=auto_approve,
                        source=source,
                    )
                    serialized = to_serializable(result)
                    session_store.set_latest_job(
                        channel=conversation["channel"],
                        account_id=conversation["account_id"],
                        conversation_id=conversation["conversation_id"],
                        job_id=result.job_id,
                    )
                    return {
                        "action": "task",
                        "job": serialized,
                        "reply_text": build_team_reply(serialized),
                        "artifacts": [path for path in artifact_paths(orchestrator.get_job_snapshot(result.job_id))],
                    }

                latest_job_id = session_store.get_latest_job(
                    channel=conversation["channel"],
                    account_id=conversation["account_id"],
                    conversation_id=conversation["conversation_id"],
                )
                if not latest_job_id:
                    raise ValueError("No latest job found for this conversation. Send a new task first.")

                snapshot = orchestrator.get_job_snapshot(latest_job_id)
                pending_stage = snapshot.get("state", {}).get("pending_review_stage")

                if action["action"] == "status":
                    return {
                        "action": "status",
                        "job": build_job_summary(snapshot),
                        "reply_text": (
                            f"当前任务 {latest_job_id} 状态：{snapshot.get('state', {}).get('status')}。"
                            f"待审核节点：{pending_stage or '无'}。"
                        ),
                    }

                if action["action"] == "resume":
                    result = orchestrator.resume(latest_job_id, auto_approve=False)
                    serialized = to_serializable(result)
                    return {"action": "resume", "job": serialized, "reply_text": build_team_reply(serialized)}

                if action["action"] in {"approve", "revise", "reject"}:
                    if not pending_stage:
                        raise ValueError(f"Job {latest_job_id} has no pending review stage.")
                    state = snapshot.get("state", {})
                    revision = int(state.get("stage_revisions", {}).get(pending_stage, 0))
                    decision = action["action"]
                    note = action.get("note") or ""
                    orchestrator.submit_review_decision(
                        job_id=latest_job_id,
                        stage=pending_stage,
                        decision=decision,
                        note=note,
                        source="wechat_auto",
                        revision=revision,
                    )
                    result = orchestrator.resume(latest_job_id, auto_approve=False)
                    serialized = to_serializable(result)
                    return {"action": decision, "job": serialized, "reply_text": build_team_reply(serialized)}

                raise ValueError("Unsupported wechat command")

            def do_GET(self) -> None:  # noqa: N802
                parsed = urlparse(self.path)
                segments = [segment for segment in parsed.path.split("/") if segment]
                try:
                    if parsed.path == "/health":
                        self._write_json(
                            HTTPStatus.OK,
                            {
                                "ok": True,
                                "service": "openclaw-media-agent",
                                "host": self.server.server_address[0],
                                "port": self.server.server_address[1],
                            },
                        )
                        return

                    if parsed.path == "/jobs":
                        jobs = orchestrator.list_jobs()
                        self._write_json(HTTPStatus.OK, {"jobs": jobs, "count": len(jobs)})
                        return

                    if len(segments) == 2 and segments[0] == "jobs":
                        snapshot = orchestrator.get_job_snapshot(segments[1])
                        self._write_json(
                            HTTPStatus.OK,
                            {
                                "job": build_job_summary(snapshot),
                                "snapshot": snapshot,
                                "reply_text": build_team_reply(snapshot.get("result") or snapshot.get("state") or {}),
                            },
                        )
                        return

                    self._write_json(HTTPStatus.NOT_FOUND, {"error": "Not found"})
                except FileNotFoundError as exc:
                    self._write_json(HTTPStatus.NOT_FOUND, {"error": str(exc)})
                except Exception as exc:  # pragma: no cover
                    self._write_json(HTTPStatus.INTERNAL_SERVER_ERROR, {"error": str(exc)})

            def do_POST(self) -> None:  # noqa: N802
                parsed = urlparse(self.path)
                segments = [segment for segment in parsed.path.split("/") if segment]
                try:
                    payload = self._read_json()

                    if parsed.path in ("/tasks", "/team/call"):
                        normalized = normalize_task_request(payload, default_source="api")
                        if not normalized["text"]:
                            self._write_json(HTTPStatus.BAD_REQUEST, {"error": "Missing task text"})
                            return
                        result = orchestrator.run_request(
                            normalized["text"],
                            auto_approve=normalized["auto_approve"],
                            source=normalized["source"],
                        )
                        self._write_json(
                            HTTPStatus.OK,
                            {
                                "job": to_serializable(result),
                                "reply_text": build_team_reply(to_serializable(result)),
                            },
                        )
                        return

                    if parsed.path == "/adapters/wechat/message":
                        normalized = normalize_task_request(payload, default_source="wechat")
                        conversation = normalize_conversation_info(payload, default_channel="openclaw-weixin")
                        if not normalized["text"]:
                            self._write_json(HTTPStatus.BAD_REQUEST, {"error": "Missing task text"})
                            return
                        result_payload = self._handle_wechat_text(
                            conversation=conversation,
                            text=normalized["text"],
                            source=normalized["source"],
                            auto_approve=normalized["auto_approve"],
                        )
                        self._write_json(HTTPStatus.OK, result_payload)
                        return

                    if parsed.path in ("/adapters/openclaw/event", "/adapters/openclaw/weixin/event"):
                        events = normalize_openclaw_weixin_events(payload)
                        if not events:
                            self._write_json(
                                HTTPStatus.BAD_REQUEST,
                                {"error": "No text events found in openclaw payload."},
                            )
                            return
                        responses = []
                        for event in events:
                            try:
                                responses.append(
                                    {
                                        "conversation_id": event["conversation_id"],
                                        "result": self._handle_wechat_text(
                                            conversation={
                                                "channel": event["channel"],
                                                "account_id": event["account_id"],
                                                "conversation_id": event["conversation_id"],
                                            },
                                            text=event["text"],
                                            source=event.get("source", "openclaw_event"),
                                            auto_approve=bool(payload.get("auto_approve", False)),
                                        ),
                                    }
                                )
                            except ValueError as exc:
                                responses.append(
                                    {
                                        "conversation_id": event["conversation_id"],
                                        "error": str(exc),
                                        "hint": "可用命令：状态 / 继续 / 通过 / 修改:意见 / 拒绝 / 新任务描述",
                                    }
                                )
                        self._write_json(
                            HTTPStatus.OK,
                            {"events_processed": len(events), "responses": responses},
                        )
                        return

                    if parsed.path == "/adapters/openclaw/task":
                        normalized = normalize_task_request(payload, default_source="openclaw")
                        if not normalized["text"]:
                            self._write_json(HTTPStatus.BAD_REQUEST, {"error": "Missing task text"})
                            return
                        result = orchestrator.run_request(
                            normalized["text"],
                            auto_approve=normalized["auto_approve"],
                            source=normalized["source"],
                        )
                        serialized = to_serializable(result)
                        conversation = normalize_conversation_info(payload, default_channel="openclaw-weixin")
                        session_store.set_latest_job(
                            channel=conversation["channel"],
                            account_id=conversation["account_id"],
                            conversation_id=conversation["conversation_id"],
                            job_id=result.job_id,
                        )
                        self._write_json(
                            HTTPStatus.OK,
                            {
                                "normalized_request": normalized,
                                "job": serialized,
                                "reply_text": build_team_reply(serialized),
                                "artifacts": [path for path in artifact_paths(orchestrator.get_job_snapshot(result.job_id))],
                            },
                        )
                        return

                    if parsed.path == "/adapters/wechat/review":
                        normalized = normalize_review_request(payload, default_source="wechat")
                        self._validate_review(normalized)
                        decision_path = orchestrator.submit_review_decision(
                            job_id=normalized["job_id"],
                            stage=normalized["stage"],
                            decision=normalized["decision"],
                            note=normalized["note"],
                            source=normalized["source"],
                            revision=normalized["revision"],
                        )
                        self._write_json(
                            HTTPStatus.OK,
                            {
                                "saved": True,
                                "decision_path": str(decision_path),
                                "reply_text": (
                                    f"已记录审核动作：{normalized['decision']}，"
                                    f"任务 {normalized['job_id']} 可继续推进。"
                                ),
                            },
                        )
                        return

                    if len(segments) == 3 and segments[0] == "jobs" and segments[2] == "resume":
                        auto_approve = bool(payload.get("auto_approve", False))
                        result = orchestrator.resume(segments[1], auto_approve=auto_approve)
                        serialized = to_serializable(result)
                        self._write_json(
                            HTTPStatus.OK,
                            {"job": serialized, "reply_text": build_team_reply(serialized)},
                        )
                        return

                    if len(segments) == 3 and segments[0] == "jobs" and segments[2] == "review":
                        normalized = normalize_review_request(dict(payload, job_id=segments[1]), default_source="api")
                        self._validate_review(normalized)
                        decision_path = orchestrator.submit_review_decision(
                            job_id=normalized["job_id"],
                            stage=normalized["stage"],
                            decision=normalized["decision"],
                            note=normalized["note"],
                            source=normalized["source"],
                            revision=normalized["revision"],
                        )
                        self._write_json(
                            HTTPStatus.OK,
                            {"saved": True, "decision_path": str(decision_path)},
                        )
                        return

                    self._write_json(HTTPStatus.NOT_FOUND, {"error": "Not found"})
                except ValueError as exc:
                    self._write_json(
                        HTTPStatus.BAD_REQUEST,
                        {
                            "error": str(exc),
                            "hint": "可用命令：状态 / 继续 / 通过 / 修改:意见 / 拒绝 / 新任务描述",
                        },
                    )
                except FileNotFoundError as exc:
                    self._write_json(HTTPStatus.NOT_FOUND, {"error": str(exc)})
                except Exception as exc:  # pragma: no cover
                    self._write_json(HTTPStatus.INTERNAL_SERVER_ERROR, {"error": str(exc)})

            def log_message(self, format: str, *args: Any) -> None:  # noqa: A003
                return

            def _read_json(self) -> Dict[str, Any]:
                length = int(self.headers.get("Content-Length", "0"))
                raw = self.rfile.read(length) if length > 0 else b"{}"
                if not raw:
                    return {}
                return json.loads(raw.decode("utf-8"))

            def _write_json(self, status: HTTPStatus, payload: Dict[str, Any]) -> None:
                body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
                self.send_response(status.value)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            @staticmethod
            def _validate_review(payload: Dict[str, Any]) -> None:
                required = ["job_id", "stage", "decision"]
                missing = [key for key in required if not payload.get(key)]
                if missing:
                    raise ValueError(f"Missing review fields: {', '.join(missing)}")
                if payload["decision"] not in {"approve", "revise", "reject"}:
                    raise ValueError("Review decision must be approve, revise, or reject")

        return Handler
