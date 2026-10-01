# BoviCare AI

BoviCare AI is a clinical decision-support starter application for dairy cattle. It helps farmers record cattle symptoms, receive a clearly labelled preliminary risk assessment, and request veterinarian review. It is **not** a replacement for a veterinarian or a trained diagnostic model.

## Project layout

```text
BoviCare/
├── frontend/     React + Vite client
├── backend/      FastAPI API
├── ml_model/     Replaceable disease-prediction integration point
└── docs/         Project documentation
```

## Run the backend

Prerequisites: Python 3.10 or newer. PostgreSQL is optional for local development; SQLite is the default.

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn app.main:app --reload
```

The API runs at `http://localhost:8000`; interactive documentation is at `http://localhost:8000/docs`.

To use PostgreSQL, set `DATABASE_URL` in `backend/.env`:

```env
DATABASE_URL=postgresql+psycopg://bovicare:your_password@localhost:5432/bovicare
```

## Run the frontend

Open a second terminal:

```powershell
cd frontend
npm install
Copy-Item .env.example .env
npm run dev
```

Open the Vite URL (normally `http://localhost:5173`). The frontend sends requests to `VITE_API_BASE_URL`, which defaults to `http://localhost:8000/api/v1`.

## Prediction service

`ml_model/predictor.py` is a deliberately conservative placeholder interface. It makes no accuracy claims and does not replace a trained model. Integrate a validated model by replacing its `predict` implementation while preserving the service contract.
