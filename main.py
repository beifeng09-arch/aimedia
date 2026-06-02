from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from core.models import to_serializable
from core.orchestrator import MediaOrchestrator
from integrations.openclaw_binding import OpenClawBindingManager
from interfaces.api_server import MediaAgentAPIServer
from scheduler.scheduler import JobScheduler


def _print_result(result) -> None:
    print(json.dumps(to_serializable(result), ensure_ascii=False, indent=2))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="OpenClaw Media Agent Team MVP")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Run a new request")
    run_parser.add_argument("text", help="Natural language task input")
    run_parser.add_argument("--auto-approve", action="store_true", help="Auto approve all review gates")

    resume_parser = subparsers.add_parser("resume", help="Resume an existing job")
    resume_parser.add_argument("job_id", help="Job identifier")
    resume_parser.add_argument("--auto-approve", action="store_true", help="Auto approve pending review gates")

    review_parser = subparsers.add_parser("review", help="Submit a review decision")
    review_parser.add_argument("job_id", help="Job identifier")
    review_parser.add_argument("stage", help="Review stage, for example plan or content_pack")
    review_parser.add_argument("decision", choices=["approve", "revise", "reject"], help="Review decision")
    review_parser.add_argument("--note", default="", help="Optional note for revise or reject")
    review_parser.add_argument("--revision", type=int, default=0, help="Revision number")

    demo_parser = subparsers.add_parser("demo", help="Run both demo requests")
    demo_parser.add_argument("--auto-approve", action="store_true", help="Auto approve all review gates")

    serve_parser = subparsers.add_parser("serve", help="Start the local API server")
    serve_parser.add_argument("--host", default=None, help="Bind host")
    serve_parser.add_argument("--port", type=int, default=None, help="Bind port")

    bind_parser = subparsers.add_parser("bind-openclaw", help="Bind OpenClaw to this project and current Codex thread")
    bind_parser.add_argument("--thread-id", default=None, help="Codex thread id. Defaults to CODEX_THREAD_ID.")
    bind_parser.add_argument("--workspace-dir", default=None, help="Workspace directory to bind")
    bind_parser.add_argument("--channel", default="openclaw-weixin", help="Conversation channel to target")
    bind_parser.add_argument("--conversation-id", default=None, help="Explicit OpenClaw conversation id")
    bind_parser.add_argument("--no-restart", action="store_true", help="Do not restart the OpenClaw gateway after binding")

    schedule_list_parser = subparsers.add_parser("schedule-list", help="List scheduler jobs and latest run state")
    schedule_list_parser.add_argument("--jobs-file", default=None, help="Optional custom jobs YAML path")

    schedule_due_parser = subparsers.add_parser("schedule-run-due", help="Run all due scheduler jobs")
    schedule_due_parser.add_argument("--jobs-file", default=None, help="Optional custom jobs YAML path")

    schedule_job_parser = subparsers.add_parser("schedule-run-job", help="Run one scheduler job immediately")
    schedule_job_parser.add_argument("job_id", help="Scheduler job id")
    schedule_job_parser.add_argument("--jobs-file", default=None, help="Optional custom jobs YAML path")
    schedule_job_parser.add_argument(
        "--respect-time",
        action="store_true",
        help="When set, do not run if the job is not due yet.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    orchestrator = MediaOrchestrator(root_dir=Path(__file__).resolve().parent)

    if args.command == "run":
        result = orchestrator.run_request(args.text, auto_approve=args.auto_approve)
        _print_result(result)
        return 0

    if args.command == "resume":
        result = orchestrator.resume(args.job_id, auto_approve=args.auto_approve)
        _print_result(result)
        return 0

    if args.command == "review":
        decision_path = orchestrator.submit_review_decision(
            job_id=args.job_id,
            stage=args.stage,
            decision=args.decision,
            note=args.note,
            revision=args.revision,
        )
        print(f"Review decision saved to {decision_path}")
        return 0

    if args.command == "demo":
        military = orchestrator.run_request("做一期南海局势节目", auto_approve=args.auto_approve)
        finance = orchestrator.run_request("做一期比特币周报", auto_approve=args.auto_approve)
        _print_result({"military": military, "finance": finance})
        return 0

    if args.command == "serve":
        server = MediaAgentAPIServer(
            root_dir=Path(__file__).resolve().parent,
            host=args.host,
            port=args.port,
        )
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            server.shutdown()
        return 0

    if args.command == "bind-openclaw":
        manager = OpenClawBindingManager()
        thread_id = args.thread_id or os.getenv("CODEX_THREAD_ID")
        if not thread_id:
            raise SystemExit("Missing thread id. Set CODEX_THREAD_ID or pass --thread-id.")
        workspace_dir = args.workspace_dir or str(Path(__file__).resolve().parent)
        backup_path = manager.backup_state()
        target = manager.infer_target(
            preferred_channel=args.channel,
            conversation_id=args.conversation_id,
        )
        binding = manager.bind_thread(
            thread_id=thread_id,
            workspace_dir=workspace_dir,
            target=target,
        )
        payload = {
            "backup_path": str(backup_path),
            "binding": binding,
            "gateway_restarted": False,
        }
        if not args.no_restart:
            restart_result = manager.restart_gateway()
            payload["gateway_restarted"] = restart_result.returncode == 0
            payload["gateway_stdout"] = restart_result.stdout.strip()
            payload["gateway_stderr"] = restart_result.stderr.strip()
        _print_result(payload)
        return 0

    if args.command == "schedule-list":
        scheduler = JobScheduler(
            orchestrator=orchestrator,
            jobs_path=Path(args.jobs_file) if args.jobs_file else None,
        )
        _print_result({"jobs": scheduler.list_jobs()})
        return 0

    if args.command == "schedule-run-due":
        scheduler = JobScheduler(
            orchestrator=orchestrator,
            jobs_path=Path(args.jobs_file) if args.jobs_file else None,
        )
        _print_result(scheduler.run_due())
        return 0

    if args.command == "schedule-run-job":
        scheduler = JobScheduler(
            orchestrator=orchestrator,
            jobs_path=Path(args.jobs_file) if args.jobs_file else None,
        )
        _print_result(scheduler.run_job(args.job_id, force=not args.respect_time))
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
