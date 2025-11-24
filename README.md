# PlanSphere (Timetable Generator)

This repository contains a simple full-stack timetable generator. The backend is a FastAPI app that serves the frontend static files and exposes a REST API under `/v1`.

Quick start (local, without Docker)

1. Create and activate a virtual environment (PowerShell):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Install dependencies:

```powershell
pip install -r requirements.txt
```

3. (Optional) Set environment variables. You can copy `.env.example` to `.env` and edit values.

4. Run the app from the project root:

```powershell
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Open http://localhost:8000/ to view the frontend. API is served under `/v1` (e.g., `/v1/health`).

Running with Docker Compose

1. Build and start services:

```powershell
docker compose up --build
```

2. After startup, the backend will be available at http://localhost:8000/ (it serves the frontend files).

Notes
- The project expects a PostgreSQL database by default. For quick development you can install Postgres locally or use the included Docker Compose which creates a `plansphere` DB with user/password `plansphere`.
- Update `SECRET_KEY` before deploying to production.
