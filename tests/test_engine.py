from mosaic.engine import assess_demo, run_judge_demo
from mosaic.models import Verdict


def test_hero_assessment_is_critical_without_returning_rows() -> None:
    assessment = assess_demo()
    assert assessment.verdict is Verdict.VALIDATED_CRITICAL
    assert assessment.metrics is not None
    assert assessment.metrics.minimum_k == 1
    assert assessment.raw_rows_returned == 0
    assert assessment.mitigation is not None
    assert assessment.mitigation["status"] == "recommended"


def test_graph_value_is_nontrivial() -> None:
    report = run_judge_demo()
    value = report["graph_value"]
    assert value["status"] == "passed"
    assert value["graph_convergences"] > value["baseline_convergences"]
