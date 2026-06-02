from __future__ import annotations

import importlib
from typing import Any, Dict, List


class ToolRegistry:
    def __init__(self) -> None:
        self._tool_modules = {
            "web_search": "tools.web_search",
            "video_download": "tools.video_download",
            "transcript": "tools.transcript",
            "subtitle_generate": "tools.subtitle_generate",
            "ffmpeg_edit": "tools.ffmpeg_edit",
            "tts_generate": "tools.tts_generate",
            "avatar_presenter": "tools.avatar_presenter",
            "publish_output": "tools.publish_output",
        }

    def execute(self, tool_name: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        if tool_name not in self._tool_modules:
            raise ValueError(f"Unknown tool: {tool_name}")
        module = importlib.import_module(self._tool_modules[tool_name])
        return module.execute(input_data)

    def list_tools(self) -> List[str]:
        return list(self._tool_modules.keys())
