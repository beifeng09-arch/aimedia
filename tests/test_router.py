from pathlib import Path

from core.router import TaskRouter


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_classify_military():
    router = TaskRouter(PROJECT_ROOT)
    assert router.classify_task("做一期南海局势节目").value == "military"


def test_classify_finance():
    router = TaskRouter(PROJECT_ROOT)
    assert router.classify_task("做一期比特币周报").value == "finance"


def test_classify_rwa():
    router = TaskRouter(PROJECT_ROOT)
    assert router.classify_task("做本周 RWA 深度研究").value == "rwa"


def test_classify_system():
    router = TaskRouter(PROJECT_ROOT)
    assert router.classify_task("帮我调整系统配置和微信接入").value == "system"


def test_classify_mixed():
    router = TaskRouter(PROJECT_ROOT)
    assert router.classify_task("做一期地缘经济与比特币联动专题").value == "mixed"


def test_build_execution_plan_contains_steps():
    router = TaskRouter(PROJECT_ROOT)
    plan = router.build_execution_plan(router.classify_task("做一期南海局势节目"), "做一期南海局势节目")
    assert plan.workflow_name == "southeast_military_pipeline"
    assert len(plan.steps) >= 5


def test_build_rwa_execution_plan_contains_steps():
    router = TaskRouter(PROJECT_ROOT)
    plan = router.build_execution_plan(router.classify_task("生成本周 RWA 周报"), "生成本周 RWA 周报")
    assert plan.workflow_name == "rwa_weekly_deep_research_pipeline"
    assert plan.review_points == ["research_report_review", "content_pack_review"]
    assert len(plan.steps) >= 7
