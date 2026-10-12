# AgentBench Lite

A small agent evaluation and regression testing dashboard. The bundled support agent is deterministic and runs locally without an external model API key. Suite runs execute the actual demo agent and evaluate its responses against declared criteria; dashboard metrics are calculated from persisted run results.

## Stack

- **Frontend:** React, Vite, TypeScript, Tailwind CSS, Lucide icons
- **Backend:** Python, FastAPI, Pydantic
- **Persistence:** MongoDB when available; in-memory development fallback otherwise

## Run locally

Requirements: Python 3.11+ and Node 20+; MongoDB is optional.

1. Start the API:

   ```powershell
   cd backend
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   Copy-Item .env.example .env
   python -m pip install -r requirements.txt
   python -m uvicorn app.main:app --reload --port 8000
   ```

   On macOS/Linux, activate the environment with `source .venv/bin/activate`. If MongoDB is unavailable, the API reports `storage: memory`; run history lasts only until the backend restarts. To persist history, configure `MONGODB_URI` in `backend/.env` and run a reachable MongoDB instance. The backend seeds the example suite on an empty database (or on first in-memory startup).

2. In another terminal, start the frontend:

   ```powershell
   cd frontend
   npm install
   npm run dev
   ```

   Open <http://localhost:5173>. Set `VITE_API_URL` in the frontend environment if the API is hosted somewhere other than `http://localhost:8000/api`.

The seeded **Customer support basics** suite contains eight example cases. The app labels seeded suites as examples and run results as demo-agent executions. The support agent is intentionally rule-based and key-free so evaluations are repeatable. A model-as-judge provider is not implemented in this MVP; optional judge settings in `.env.example` are reserved and do not affect evaluation.

## API

Interactive API documentation is available at <http://localhost:8000/docs>.

- `GET /api/health`, `GET /api/suites`, `POST /api/suites`
- `POST /api/suites/{suite_id}/cases`
- `GET /api/runs`, `GET /api/runs/{run_id}`, `POST /api/runs`
- `GET /api/compare?baseline={id}&candidate={id}`

Supported criteria are `contains`, `exact`, `required_keywords`, and `forbidden_content`. Text matching is case-insensitive. All criteria on a test case must pass.

## Test and build

From the project root, run the backend tests with the backend virtual environment:

```powershell
.\backend\.venv\Scripts\python.exe -m pytest -q
```

Or, if the backend virtual environment is activated:

```powershell
python -m pytest -q
```

Then build the frontend:

```powershell
cd frontend
npm run build
```

The root `pytest.ini` makes test imports work from the project root or the `backend` directory.

## Deployment

Deploy the frontend static build from `frontend/dist` to a static host and set `VITE_API_URL` to your HTTPS API base URL (including `/api`). Run the backend with an ASGI server such as Uvicorn, configure `MONGODB_URI`, `MONGODB_DATABASE`, and `FRONTEND_ORIGIN`, and use a managed MongoDB deployment for persistent shared history. Restrict CORS to the deployed frontend origin. No API credentials are required by this MVP.
