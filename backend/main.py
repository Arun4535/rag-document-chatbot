from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from database import init_db
from routers import agent, evals, ingest, query


app = FastAPI(title="DocSense API", version="1.0.0")

# The frontend is served by the same FastAPI process. CORS is permissive in
# development only to simplify direct API testing.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup() -> None:
    init_db()


@app.get("/api/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(ingest.router, prefix="/api/ingest", tags=["ingest"])
app.include_router(query.router, prefix="/api/query", tags=["query"])
app.include_router(agent.router, prefix="/api/agent", tags=["agent"])
app.include_router(evals.router, prefix="/api/evals", tags=["evals"])


FRONTEND_DIR = Path(__file__).resolve().parents[1] / "frontend"

if FRONTEND_DIR.exists():
    # Mounting the static app after API routes keeps /api/* handled by FastAPI
    # while every browser route falls back to the single-page frontend.
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
