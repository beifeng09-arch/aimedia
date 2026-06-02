from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from core.logging_utils import load_yaml


class SkillRunner:
    def __init__(self, root_dir: Path) -> None:
        self.root_dir = Path(root_dir)
        self.skill_config = load_yaml(self.root_dir / "config" / "skills.yaml", default={"skills": {}})
        self._metadata_cache: Dict[str, Dict[str, Any]] = {}

    def get_skill(self, skill_name: str) -> Dict[str, Any]:
        skill = self.skill_config.get("skills", {}).get(skill_name)
        if not isinstance(skill, dict):
            raise ValueError(f"Unknown skill: {skill_name}")
        return skill

    def resolve_skill_for_stage(self, category: str, stage: str) -> Optional[str]:
        for skill_name, payload in self.skill_config.get("skills", {}).items():
            if category not in payload.get("workflow_categories", []):
                continue
            if stage in payload.get("stages", []):
                return str(skill_name)
        return None

    def record_run(
        self,
        *,
        category: str,
        job_id: str,
        job_dir: Path,
        stage: str,
        skill_name: str,
        agent_name: str,
        payload: Dict[str, Any],
        output_paths: List[str],
    ) -> Dict[str, Any]:
        skill = self.get_skill(skill_name)
        metadata = self._load_skill_metadata(skill_name, skill)
        resolved_inputs = []
        for item in skill.get("reads", []):
            candidate = job_dir / str(item)
            resolved_inputs.append(
                {
                    "name": str(item),
                    "path": str(candidate) if candidate.exists() else None,
                }
            )
        return {
            "skill_name": skill_name,
            "display_name": metadata.get("display_name", skill_name),
            "description": metadata.get("description", ""),
            "stage": stage,
            "workflow_category": category,
            "job_id": job_id,
            "skill_path": self._resolve_skill_path(skill),
            "agent_name": agent_name,
            "virtual": bool(skill.get("virtual", False)) or not skill.get("path"),
            "review_gate": skill.get("review_gate"),
            "declared_reads": list(skill.get("reads", [])),
            "resolved_inputs": resolved_inputs,
            "declared_writes": list(skill.get("writes", [])),
            "resolved_outputs": list(output_paths),
            "payload_keys": sorted(payload.keys()),
            "invoked_at": datetime.utcnow().isoformat(),
        }

    def _load_skill_metadata(self, skill_name: str, skill: Dict[str, Any]) -> Dict[str, Any]:
        if skill_name in self._metadata_cache:
            return self._metadata_cache[skill_name]
        skill_dir = self.root_dir / str(skill.get("path", ""))
        skill_md = skill_dir / "SKILL.md"
        openai_yaml = skill_dir / "agents" / "openai.yaml"

        frontmatter = {}
        if skill_md.exists():
            content = skill_md.read_text(encoding="utf-8")
            match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
            if match:
                frontmatter = yaml.safe_load(match.group(1)) or {}

        openai_meta = load_yaml(openai_yaml)
        interface = openai_meta.get("interface", {})
        metadata = {
            "name": frontmatter.get("name", skill_name) or skill.get("display_name", skill_name),
            "description": frontmatter.get("description", "")
            or skill.get("description", "")
            or skill.get("short_description", ""),
            "display_name": interface.get("display_name")
            or skill.get("display_name")
            or skill_name,
            "short_description": interface.get("short_description")
            or skill.get("short_description", ""),
            "default_prompt": interface.get("default_prompt")
            or skill.get("default_prompt", ""),
        }
        self._metadata_cache[skill_name] = metadata
        return metadata

    @staticmethod
    def _resolve_skill_path(skill: Dict[str, Any]) -> str:
        skill_path = str(skill.get("path", "")).strip()
        if skill_path:
            return skill_path
        if skill.get("virtual"):
            return "virtual"
        return ""
