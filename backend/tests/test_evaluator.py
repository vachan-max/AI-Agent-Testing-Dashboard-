from app.evaluator import calculate_metrics, evaluate_criteria
from app.models import CaseResult, Criterion


def test_contains_and_keyword_checks_are_case_insensitive():
    passed, reason = evaluate_criteria("Hello ORDER number", [Criterion(type="contains", value="hello"), Criterion(type="required_keywords", value=["order", "number"])])
    assert passed and reason == "All criteria passed."


def test_exact_and_forbidden_content_fail_with_reason():
    passed, reason = evaluate_criteria("Refund guaranteed", [Criterion(type="exact", value="Refund granted"), Criterion(type="forbidden_content", value="guaranteed")])
    assert not passed
    assert "exactly match" in reason and "Forbidden content" in reason


def test_metrics_are_calculated_from_results():
    results = [CaseResult(case_id="1", case_name="a", input="", expected_behavior="", actual_response="", passed=True, reason="ok", latency_ms=10),
               CaseResult(case_id="2", case_name="b", input="", expected_behavior="", actual_response="", passed=False, reason="no", latency_ms=30)]
    metrics = calculate_metrics(results)
    assert (metrics.total, metrics.passed, metrics.failed, metrics.pass_rate, metrics.average_latency_ms) == (2, 1, 1, 50, 20)


def test_empty_metrics_are_safe():
    metrics = calculate_metrics([])
    assert metrics.total == metrics.passed == metrics.failed == 0
    assert metrics.pass_rate == metrics.average_latency_ms == 0
