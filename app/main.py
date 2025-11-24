import os
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from .database import engine, Base
from .api.v1.routes import router

# load .env for development convenience
load_dotenv()

# create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="PlanSphere API (Postgres)")

# Allow the front-end (same host) to call API; adjust origins if you open from other host
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # for dev only; in prod restrict this to your domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# include API router (this registers /v1/* routes)
app.include_router(router)

# Get the base directory (project root)
BASE_DIR = Path(__file__).resolve().parent.parent

# Serve static files (CSS, JS, images)
static_dir = BASE_DIR / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Serve images folder
images_dir = BASE_DIR / "images"
if images_dir.exists():
    app.mount("/images", StaticFiles(directory=str(images_dir)), name="images")

# Serve templates at /templates/* for AJAX loading
templates_dir = BASE_DIR / "templates"
if templates_dir.exists():
    app.mount("/templates", StaticFiles(directory=str(templates_dir), html=False), name="templates-api")

# Serve templates and other HTML files at root
if templates_dir.exists():
    app.mount("/", StaticFiles(directory=str(templates_dir), html=True), name="templates")

@app.get("/health")
def health_check():
    return {"message": "PlanSphere API running"}
