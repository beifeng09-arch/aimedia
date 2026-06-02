import json
import threading
import urllib.request
from pathlib import Path

from interfaces.api_server import MediaAgentAPIServer


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _request_json(method: str, url: str, payload=None):
    data = None
    headers = {"Content-Type": "application/json"}
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    with opener.open(request, timeout=5) as response:
        return response.getcode(), json.loads(response.read().decode("utf-8"))


def test_api_task_and_job_status(tmp_path):
    server = MediaAgentAPIServer(
        root_dir=PROJECT_ROOT,
        host="127.0.0.1",
        port=0,
        output_dir=tmp_path / "outputs",
        log_dir=tmp_path / "logs",
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base_url = f"http://{server.httpd.server_address[0]}:{server.httpd.server_address[1]}"
    try:
        code, health = _request_json("GET", f"{base_url}/health")
        assert code == 200
        assert health["ok"] is True

        code, task_payload = _request_json(
            "POST",
            f"{base_url}/team/call",
            {"text": "做一期南海局势节目", "auto_approve": True},
        )
        assert code == 200
        assert task_payload["job"]["final_status"] == "completed"
        job_id = task_payload["job"]["job_id"]

        code, snapshot = _request_json("GET", f"{base_url}/jobs/{job_id}")
        assert code == 200
        assert snapshot["job"]["job_id"] == job_id
        assert snapshot["job"]["artifact_count"] >= 5
    finally:
        server.shutdown()
        thread.join(timeout=2)


def test_api_review_and_resume(tmp_path):
    server = MediaAgentAPIServer(
        root_dir=PROJECT_ROOT,
        host="127.0.0.1",
        port=0,
        output_dir=tmp_path / "outputs",
        log_dir=tmp_path / "logs",
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base_url = f"http://{server.httpd.server_address[0]}:{server.httpd.server_address[1]}"
    try:
        _, task_payload = _request_json(
            "POST",
            f"{base_url}/adapters/openclaw/task",
            {"message": {"text": "做一期比特币周报"}, "auto_approve": False, "channel": "wechat"},
        )
        assert task_payload["job"]["final_status"] == "needs_review"
        job_id = task_payload["job"]["job_id"]

        _, review_payload = _request_json(
            "POST",
            f"{base_url}/adapters/wechat/review",
            {"job_id": job_id, "stage": "plan", "decision": "approve", "revision": 0},
        )
        assert review_payload["saved"] is True

        _, resumed = _request_json("POST", f"{base_url}/jobs/{job_id}/resume", {})
        assert resumed["job"]["final_status"] == "needs_review"
        assert resumed["job"]["review_stage"] == "content_pack"
    finally:
        server.shutdown()
        thread.join(timeout=2)


def test_wechat_message_loop(tmp_path):
    server = MediaAgentAPIServer(
        root_dir=PROJECT_ROOT,
        host="127.0.0.1",
        port=0,
        output_dir=tmp_path / "outputs",
        log_dir=tmp_path / "logs",
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base_url = f"http://{server.httpd.server_address[0]}:{server.httpd.server_address[1]}"
    conversation_payload = {
        "channel": "openclaw-weixin",
        "account_id": "bot-account",
        "conversation_id": "wechat-room-42",
    }
    try:
        _, first = _request_json(
            "POST",
            f"{base_url}/adapters/wechat/message",
            {
                **conversation_payload,
                "message": {"text": "做一期南海局势节目"},
                "auto_approve": False,
            },
        )
        assert first["action"] == "task"
        assert first["job"]["final_status"] == "needs_review"

        _, status = _request_json(
            "POST",
            f"{base_url}/adapters/wechat/message",
            {**conversation_payload, "message": {"text": "状态"}},
        )
        assert status["action"] == "status"
        assert status["job"]["pending_review_stage"] == "plan"

        _, approved = _request_json(
            "POST",
            f"{base_url}/adapters/wechat/message",
            {**conversation_payload, "message": {"text": "通过"}},
        )
        assert approved["action"] == "approve"
        assert approved["job"]["final_status"] == "needs_review"
        assert approved["job"]["review_stage"] == "content_pack"

        _, revised = _request_json(
            "POST",
            f"{base_url}/adapters/wechat/message",
            {**conversation_payload, "message": {"text": "修改：结尾更聚焦观察点"}},
        )
        assert revised["action"] == "revise"
        assert revised["job"]["final_status"] == "needs_review"
        assert revised["job"]["review_stage"] == "content_pack"
    finally:
        server.shutdown()
        thread.join(timeout=2)


def test_openclaw_event_batch_bridge(tmp_path):
    server = MediaAgentAPIServer(
        root_dir=PROJECT_ROOT,
        host="127.0.0.1",
        port=0,
        output_dir=tmp_path / "outputs",
        log_dir=tmp_path / "logs",
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base_url = f"http://{server.httpd.server_address[0]}:{server.httpd.server_address[1]}"
    try:
        _, payload = _request_json(
            "POST",
            f"{base_url}/adapters/openclaw/event",
            {
                "account_id": "bot-account",
                "msgs": [
                    {
                        "message_type": 1,
                        "session_id": "room-a",
                        "item_list": [{"type": 1, "text_item": {"text": "做一期南海局势节目"}}],
                    },
                    {
                        "message_type": 1,
                        "session_id": "room-a",
                        "item_list": [{"type": 1, "text_item": {"text": "状态"}}],
                    },
                ],
                "auto_approve": False,
            },
        )
        assert payload["events_processed"] == 2
        assert payload["responses"][0]["result"]["action"] == "task"
        assert payload["responses"][1]["result"]["action"] == "status"
        assert payload["responses"][1]["result"]["job"]["pending_review_stage"] == "plan"
    finally:
        server.shutdown()
        thread.join(timeout=2)


def test_openclaw_event_single_msg_shape(tmp_path):
    server = MediaAgentAPIServer(
        root_dir=PROJECT_ROOT,
        host="127.0.0.1",
        port=0,
        output_dir=tmp_path / "outputs",
        log_dir=tmp_path / "logs",
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base_url = f"http://{server.httpd.server_address[0]}:{server.httpd.server_address[1]}"
    try:
        _, payload = _request_json(
            "POST",
            f"{base_url}/adapters/openclaw/weixin/event",
            {
                "account_id": "bot-account",
                "msg": {
                    "session_id": "room-b",
                    "item_list": [{"type": 1, "text_item": {"text": "做一期比特币周报"}}],
                },
                "auto_approve": False,
            },
        )
        assert payload["events_processed"] == 1
        assert payload["responses"][0]["result"]["action"] == "task"
        assert payload["responses"][0]["result"]["job"]["category"] == "finance"
    finally:
        server.shutdown()
        thread.join(timeout=2)
