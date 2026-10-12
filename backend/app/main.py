from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient

from .demo_agent import support_agent
from .evaluator import calculate_metrics, execute_case
from .models import CaseCreate, CaseResult, CompareResponse, Run, RunMetrics, RunRequest, Suite, SuiteCreate, TestCase
from .seed import seed_suites
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    mongodb_uri: str = "mongodb://localhost:27017"
    mongodb_database: str = "agentbench_lite"
    frontend_origin: str = "http://localhost:5173"
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
memory_suites: dict[str, Suite] = {}
memory_runs: dict[str, Run] = {}
mongo_client: AsyncIOMotorClient | None = None
db = None


@asynccontextmanager
async def lifespan(_: FastAPI):
    global mongo_client, db
    try:
        mongo_client = AsyncIOMotorClient(settings.mongodb_uri, serverSelectionTimeoutMS=700)
        await mongo_client.admin.command("ping")
        db = mongo_client[settings.mongodb_database]
        if await db.suites.count_documents({}) == 0:
            await db.suites.insert_many([s.model_dump(mode="json") for s in seed_suites()])
    except Exception:
        if mongo_client:
            mongo_client.close()
        mongo_client = None
        db = None
    if db is None and not memory_suites:
        memory_suites.update({s.id: s for s in seed_suites()})
    yield
    if mongo_client:
        mongo_client.close()


app = FastAPI(title="AgentBench Lite API", version="1.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=[settings.frontend_origin], allow_methods=["*"], allow_headers=["*"])


async def get_suites() -> list[Suite]:
    if db is not None:
        docs = await db.suites.find({}, {"_id": 0}).to_list(500)
        return [Suite(id=d["id"], name=d["name"], description=d.get("description", ""), cases=d.get("cases", []), is_seeded=d.get("is_seeded", False), created_at=d["created_at"]) for d in docs]
    return list(memory_suites.values())


async def get_runs() -> list[Run]:
    if db is not None:
        docs = await db.runs.find({}, {"_id": 0}).sort("created_at", -1).to_list(500)
        return [Run(id=d["id"], suite_id=d["suite_id"], suite_name=d["suite_name"], source=d.get("source", "execution"), created_at=d["created_at"], metrics=RunMetrics.model_validate(d["metrics"]), results=[CaseResult.model_validate(r) for r in d["results"]]) for d in docs]
    return sorted(memory_runs.values(), key=lambda r: r.created_at, reverse=True)


async def save_suite(suite: Suite) -> None:
    if db is not None:
        await db.suites.insert_one(suite.model_dump(mode="json"))
    else:
        memory_suites[suite.id] = suite


async def save_run(run: Run) -> None:
    if db is not None:
        await db.runs.insert_one(run.model_dump(mode="json"))
    else:
        memory_runs[run.id] = run


@app.get("/api/health")
async def health():
    return {"status": "ok", "storage": "mongodb" if db is not None else "memory"}


@app.get("/api/suites", response_model=list[Suite])
async def list_suites():
    return await get_suites()


@app.post("/api/suites", response_model=Suite, status_code=201)
async def create_suite(payload: SuiteCreate):
    suite = Suite(**payload.model_dump())
    await save_suite(suite)
    return suite


@app.post("/api/suites/{suite_id}/cases", response_model=Suite)
async def add_case(suite_id: str, payload: CaseCreate):
    suites = await get_suites()
    suite = next((s for s in suites if s.id == suite_id), None)
    if suite is None:
        raise HTTPException(404, "Suite not found")
    suite.cases.append(TestCase(**payload.model_dump()))
    if db is not None:
        doc = suite.model_dump(mode="json")
        doc.pop("_id", None)
        await db.suites.replace_one({"id": suite.id}, doc)
    else:
        memory_suites[suite.id] = suite
    return suite


@app.get("/api/runs", response_model=list[Run])
async def list_runs():
    return await get_runs()


@app.get("/api/runs/{run_id}", response_model=Run)
async def get_run(run_id: str):
    run = next((r for r in await get_runs() if r.id == run_id), None)
    if run is None:
        raise HTTPException(404, "Run not found")
    return run


@app.get("/api/suites/{suite_id}", response_model=Suite)
async def get_suite(suite_id: str):
    suite = next((s for s in await get_suites() if s.id == suite_id), None)
    if suite is None:
        raise HTTPException(404, "Suite not found")
    return suite


@app.post("/api/runs", response_model=Run, status_code=201)
async def run_suite(payload: RunRequest):
    suite = next((s for s in await get_suites() if s.id == payload.suite_id), None)
    if suite is None:
        raise HTTPException(404, "Suite not found")
    results = [execute_case(case, support_agent) for case in suite.cases]
    run = Run(suite_id=suite.id, suite_name=suite.name, results=results, metrics=calculate_metrics(results))
    await save_run(run)
    return run


@app.get("/api/compare", response_model=CompareResponse)
async def compare_runs(baseline: str, candidate: str):
    runs = await get_runs()
    before = next((r for r in runs if r.id == baseline), None)
    after = next((r for r in runs if r.id == candidate), None)
    if not before or not after:
        raise HTTPException(404, "Both runs must exist")
    old = {r.case_id: r for r in before.results}
    new = {r.case_id: r for r in after.results}
    fixed, regressions, unchanged_passed, unchanged_failed = [], [], [], []
    for case_id in old.keys() & new.keys():
        label = new[case_id].case_name
        if not old[case_id].passed and new[case_id].passed:
            fixed.append(label)
        elif old[case_id].passed and not new[case_id].passed:
            regressions.append(label)
        elif new[case_id].passed:
            unchanged_passed.append(label)
        else:
            unchanged_failed.append(label)
    return CompareResponse(baseline_run_id=baseline, candidate_run_id=candidate, fixed=sorted(fixed),
                          regressions=sorted(regressions), unchanged_passed=sorted(unchanged_passed),
                          unchanged_failed=sorted(unchanged_failed))
