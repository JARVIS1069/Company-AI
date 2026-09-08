# Company AI — Multi-Agent Organization System

A role-based multi-agent AI organization that demonstrates how AI agents collaborate through **planning, execution, validation, approval, and release** — using a real Demand Forecasting & Inventory Optimization pipeline as the working example.

11 agents, each with real logic, RBAC-enforced permissions, structured message handoffs, and a full audit trail — from project kickoff to production release, backed by a real trained ML model and a live dashboard.

## What's actually real here

- **Real ML**: a LightGBM model is trained on real (synthetic but realistic) sales data, evaluated on a held-out time-based test split. Reported MAPE ≈ 12%.
- **Real validation**: QA re-reads the raw dataset directly, checks RMSE/MAE/MAPE against thresholds, and actually loads the saved model from disk to run a live prediction — not just trusting a status string.
- **Real permissions**: every agent's allowed actions are enforced by an RBAC layer, not just suggested by convention.
- **Real audit trail**: every message send/receive/denial is logged with a timestamp, viewable via the API or the dashboard.

## Organization roles

| Role | Responsibility |
|---|---|
| President | Approves project direction, budget/risk, and final release |
| VP | Turns the company goal into KPIs and oversees departments |
| Manager | Creates plans, milestones, tasks, deadlines, and assignments |
| Team Lead | Chooses the technical approach and coordinates working agents |
| Data Engineer | Collects, cleans, and prepares sales and inventory data |
| Data Scientist | Analyzes demand patterns and builds forecasting models |
| ML Engineer | Evaluates, packages, and deploys the best model |
| QA Validator | Tests data quality, forecast accuracy, and API correctness |
| Inventory Analyst | Turns forecasts into reorder and stockout recommendations |
| Reviewer | Checks evidence against requirements and requests changes |
| Release | Releases only after required approvals and quality gates |

## Workflow

```
Plan → Prepare Data → Forecast Demand → Optimize Inventory → Validate → Review → Approve → Release
```

## Project structure

```
company-ai/
├── backend/
│   ├── agents/          # All 11 agent classes, each inheriting from BaseAgent
│   ├── orchestrator/     # Event bus for inter-agent messaging
│   ├── permissions/       # RBAC role → allowed-actions map
│   ├── audit/             # Append-only audit log
│   ├── ml/                # Data cleaning, model training, inventory optimization, validation
│   ├── main.py            # FastAPI app — the live backend entrypoint
│   ├── demo_workflow.py   # Standalone script, no server needed
│   └── requirements.txt
├── frontend/               # React + Vite dashboard
├── datasets/                # Synthetic sales & inventory data generator + output CSVs
├── models/                   # Trained model artifact lands here (.joblib)
└── README.md
```

## How to run it

You'll need **two terminals** running at once (backend + frontend), plus Python 3.10+ and Node.js installed.

### 1. Backend setup (one-time)

```powershell
cd company-ai
pip install -r backend\requirements.txt
mkdir models
```

### 2. Start the backend

```powershell
python -m uvicorn backend.main:app --reload
```

Leave this running. It serves the API at `http://127.0.0.1:8000`. Visit `http://127.0.0.1:8000/docs` for an interactive API explorer.

### 3. Frontend setup (one-time, in a new terminal)

```powershell
cd company-ai\frontend
npm install
```

### 4. Start the frontend

```powershell
npm run dev
```

Open `http://localhost:5173` in your browser.

### 5. Run the pipeline

Click **Start Project** in the dashboard. This triggers the full chain — President through Release — including real model training, and takes a few seconds.

Alternatively, run it without any server at all:

```powershell
python -m backend.demo_workflow
```

This prints the full cascade, audit trail, and proves both the happy path and the failure-handling paths (QA blocking bad data, Release blocking forged approvals, Reviewer catching bad math) directly in your terminal.

## API endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/org` | GET | Full org chart with roles and permissions |
| `/kickoff` | POST | Triggers the entire pipeline end-to-end |
| `/audit-log` | GET | Full audit trail |
| `/message` | POST | Send a single RBAC-checked message between two agents |
| `/history` | GET | Raw event bus message history |

## Tech stack

- **Backend**: Python, FastAPI, scikit-learn, LightGBM, pandas
- **Frontend**: React, Vite
- **Data**: synthetic sales/inventory data with real seasonality, trend, missing values, and outliers (see `datasets/generate_synthetic_data.py`)

## Notes on current limitations

- No persistence — all agent state and audit history reset when the backend restarts (in-memory only)
- No authentication — fine for local use, not for public deployment
- Single synthetic dataset — swapping in real data is a drop-in file replacement (same schema), no code changes required
