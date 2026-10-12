from fastapi.testclient import TestClient
import pytest

from app import main
from app.main import app


@pytest.fixture(autouse=True)
def isolate_tests_from_configured_mongodb(monkeypatch):
    class OfflineMongoClient:
        admin = None

        def __init__(self, *args, **kwargs):
            self.admin = self

        async def command(self, *_args, **_kwargs):
            raise ConnectionError("Integration tests use isolated in-memory storage")

        def close(self):
            pass

    monkeypatch.setattr(main, "AsyncIOMotorClient", OfflineMongoClient)
    main.memory_suites.clear()
    main.memory_runs.clear()
    main.db = None
    yield
    main.memory_suites.clear()
    main.memory_runs.clear()
    main.db = None


def test_suite_case_run_history_and_comparison_flow():
    with TestClient(app) as client:
        suites = client.get("/api/suites").json()
        assert suites
        suite = client.post("/api/suites", json={"name": "API flow", "description": "Integration coverage"})
        assert suite.status_code == 201
        suite_id = suite.json()["id"]

        case = client.post(f"/api/suites/{suite_id}/cases", json={
            "name": "Shipping question",
            "input": "How long does shipping take?",
            "expected_behavior": "Give delivery estimate",
            "evaluation_criteria": [{"type": "contains", "value": "3–5 business days"}],
        })
        assert case.status_code == 200
        assert len(case.json()["cases"]) == 1

        first = client.post("/api/runs", json={"suite_id": suite_id})
        second = client.post("/api/runs", json={"suite_id": suite_id})
        assert first.status_code == second.status_code == 201
        run = first.json()
        assert run["metrics"]["total"] == 1
        assert run["metrics"]["passed"] == 1
        assert run["results"][0]["actual_response"]

        history = client.get("/api/runs").json()
        assert any(item["id"] == run["id"] for item in history)
        comparison = client.get("/api/compare", params={"baseline": run["id"], "candidate": second.json()["id"]})
        assert comparison.status_code == 200
        assert comparison.json()["unchanged_passed"] == ["Shipping question"]


def test_invalid_case_is_rejected_and_missing_suite_is_not_found():
    with TestClient(app) as client:
        invalid = client.post("/api/suites", json={"name": "Bad", "description": ""})
        assert invalid.status_code == 201
        suite_id = invalid.json()["id"]
        bad_case = client.post(f"/api/suites/{suite_id}/cases", json={
            "name": "Empty criterion", "input": "Hi", "expected_behavior": "Greet",
            "evaluation_criteria": [{"type": "contains", "value": "   "}],
        })
        assert bad_case.status_code == 422
        missing = client.post("/api/runs", json={"suite_id": "missing"})
        assert missing.status_code == 404
