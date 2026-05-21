from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import init_db
from routers import agent, evals, ingest, query


app = FastAPI(title="DocSense API", version="1.0.0")

# The deployed frontend talks to the backend through the same-origin Nginx
# proxy. CORS is permissive in development only to simplify direct API testing.
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
