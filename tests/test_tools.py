from pathlib import Path

from core.orchestrator import MediaOrchestrator


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_all_tools_return_unified_structure(tmp_path):
    orchestrator = MediaOrchestrator(
        root_dir=PROJECT_ROOT,
        output_dir=tmp_path / "outputs",
        log_dir=tmp_path / "logs",
    )
    for tool_name in orchestrator.tools.list_tools():
        result = orchestrator.tools.execute(tool_name, {"query": "demo", "job_id": "demo"})
        assert set(result.keys()) == {"success", "tool", "data", "error", "meta"}
        assert result["tool"] == tool_name

    assert (tmp_path / "logs" / "tools.log").exists()
