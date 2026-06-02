from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import List, Optional

from core.logging_utils import ensure_directory, load_yaml, write_text, write_yaml
from core.models import ReviewDecision, ReviewDecisionType, ReviewTicket, to_serializable


class ReviewManager:
    def __init__(self, output_dir: Path, channels: Optional[List[str]] = None) -> None:
        self.output_dir = Path(output_dir)
        self.channels = channels or ["local_file"]

    def request_review(
        self,
        job_id: str,
        stage: str,
        artifact_paths: List[str],
        instructions: str = "",
        revision: int = 0,
    ) -> ReviewTicket:
        review_dir = ensure_directory(self.output_dir / job_id / "reviews")
        prefix = f"{stage}_r{revision}"
        ticket_path = review_dir / f"{prefix}_ticket.yaml"
        decision_path = review_dir / f"{prefix}_decision.yaml"
        markdown_path = review_dir / f"{prefix}_ticket.md"

        ticket = ReviewTicket(
            job_id=job_id,
            stage=stage,
            revision=revision,
            artifact_paths=artifact_paths,
            channels=self.channels,
            instructions=instructions,
            ticket_path=str(ticket_path),
            decision_path=str(decision_path),
        )
        write_yaml(ticket_path, to_serializable(ticket))
        if not decision_path.exists():
            write_yaml(
                decision_path,
                {
                    "job_id": job_id,
                    "stage": stage,
                    "revision": revision,
                    "decision": ReviewDecisionType.PENDING.value,
                    "note": "",
                    "source": "local_file",
                    "decided_at": None,
                },
            )
        write_text(markdown_path, self._render_markdown(ticket))
        return ticket

    def submit_decision(
        self,
        job_id: str,
        stage: str,
        decision: str,
        note: str = "",
        source: str = "local_file",
        revision: int = 0,
    ) -> Path:
        review_dir = ensure_directory(self.output_dir / job_id / "reviews")
        decision_path = review_dir / f"{stage}_r{revision}_decision.yaml"
        payload = {
            "job_id": job_id,
            "stage": stage,
            "revision": revision,
            "decision": decision,
            "note": note,
            "source": source,
            "decided_at": datetime.utcnow().isoformat(),
        }
        return write_yaml(decision_path, payload)

    def consume_decision(
        self,
        job_id: str,
        stage: str,
        revision: int = 0,
    ) -> ReviewDecision:
        decision_path = self.output_dir / job_id / "reviews" / f"{stage}_r{revision}_decision.yaml"
        payload = load_yaml(decision_path)
        if not payload:
            return ReviewDecision(stage=stage, revision=revision, decision=ReviewDecisionType.PENDING.value)
        return ReviewDecision(
            stage=payload.get("stage", stage),
            revision=int(payload.get("revision", revision)),
            decision=payload.get("decision", ReviewDecisionType.PENDING.value),
            note=payload.get("note", ""),
            source=payload.get("source", "local_file"),
            decided_at=payload.get("decided_at"),
        )

    def _render_markdown(self, ticket: ReviewTicket) -> str:
        artifact_lines = "\n".join(f"- `{path}`" for path in ticket.artifact_paths)
        channel_lines = "\n".join(f"- `{channel}`" for channel in ticket.channels)
        return f"""# Review Ticket

- Job ID: `{ticket.job_id}`
- Stage: `{ticket.stage}`
- Revision: `{ticket.revision}`
- Status: `{ticket.status}`

## Artifacts
{artifact_lines or "- None"}

## Instructions
{ticket.instructions or "Please review the generated artifacts and record approve / revise / reject."}

## Channels
{channel_lines or "- local_file"}

## Simulated WeChat Payload
```json
{{
  "job_id": "{ticket.job_id}",
  "stage": "{ticket.stage}",
  "revision": {ticket.revision},
  "actions": ["approve", "revise", "reject"]
}}
```

## Local Decision Command
```bash
python3 main.py review {ticket.job_id} {ticket.stage} approve --revision {ticket.revision}
```
"""
