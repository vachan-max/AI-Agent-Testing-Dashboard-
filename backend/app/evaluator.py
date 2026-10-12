from collections.abc import Callable
from time import perf_counter

from .models import CaseResult, Criterion, RunMetrics, TestCase


def evaluate_criteria(response: str, criteria: list[Criterion]) -> tuple[bool, str]:
    """Evaluate every criterion; all checks must pass."""
    failures: list[str] = []
    for criterion in criteria:
        value = criterion.value
        if criterion.type == "contains":
            if not isinstance(value, str) or value.casefold() not in response.casefold():
                failures.append(f"Response does not contain “{value}”.")
        elif criterion.type == "exact":
            if not isinstance(value, str) or value.casefold().strip() != response.casefold().strip():
                failures.append("Response does not exactly match the expected text.")
        elif criterion.type == "required_keywords":
            words = value if isinstance(value, list) else [value]
            missing = [word for word in words if word.casefold() not in response.casefold()]
            if missing:
                failures.append(f"Missing required keywords: {', '.join(missing)}.")
        elif criterion.type == "forbidden_content":
            words = value if isinstance(value, list) else [value]
            found = [word for word in words if word.casefold() in response.casefold()]
            if found:
                failures.append(f"Forbidden content found: {', '.join(found)}.")
    return not failures, "All criteria passed." if not failures else " ".join(failures)


def calculate_metrics(results: list[CaseResult]) -> RunMetrics:
    total = len(results)
    passed = sum(result.passed for result in results)
    return RunMetrics(
        total=total,
        passed=passed,
        failed=total - passed,
        pass_rate=round(passed / total * 100, 1) if total else 0.0,
        average_latency_ms=round(sum(r.latency_ms for r in results) / total, 1) if total else 0.0,
    )


def execute_case(case: TestCase, agent: Callable[[str], str]) -> CaseResult:
    start = perf_counter()
    response = agent(case.input)
    latency = (perf_counter() - start) * 1000
    passed, reason = evaluate_criteria(response, case.evaluation_criteria)
    return CaseResult(case_id=case.id, case_name=case.name, input=case.input,
                      expected_behavior=case.expected_behavior, actual_response=response,
                      passed=passed, reason=reason, latency_ms=round(latency, 2))
