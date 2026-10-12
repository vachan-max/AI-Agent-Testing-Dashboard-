from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator


def new_id() -> str:
    return str(uuid4())


class CaseCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    input: str = Field(min_length=1, max_length=4000)
    expected_behavior: str = Field(min_length=1, max_length=2000)
    evaluation_criteria: list["Criterion"] = Field(min_length=1, max_length=10)


class Criterion(BaseModel):
    type: Literal["contains", "exact", "required_keywords", "forbidden_content"]
    value: str | list[str] = Field(min_length=1)

    @field_validator("value")
    @classmethod
    def validate_nonempty_value(cls, value: str | list[str]):
        if isinstance(value, str) and not value.strip():
            raise ValueError("Criterion value cannot be empty")
        if isinstance(value, list) and (not value or any(not item.strip() for item in value)):
            raise ValueError("Criterion values must be non-empty")
        return value


class TestCase(CaseCreate):
    id: str = Field(default_factory=new_id)


class SuiteCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str = Field(default="", max_length=500)


class Suite(SuiteCreate):
    id: str = Field(default_factory=new_id)
    cases: list[TestCase] = Field(default_factory=list)
    is_seeded: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class CaseResult(BaseModel):
    case_id: str
    case_name: str
    input: str
    expected_behavior: str
    actual_response: str
    passed: bool
    reason: str
    latency_ms: float = Field(ge=0)


class RunMetrics(BaseModel):
    total: int
    passed: int
    failed: int
    pass_rate: float
    average_latency_ms: float


class Run(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=new_id)
    suite_id: str
    suite_name: str
    source: Literal["execution", "seeded"] = "execution"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metrics: RunMetrics
    results: list[CaseResult]


class RunRequest(BaseModel):
    suite_id: str


class CompareResponse(BaseModel):
    baseline_run_id: str
    candidate_run_id: str
    fixed: list[str]
    regressions: list[str]
    unchanged_passed: list[str]
    unchanged_failed: list[str]
