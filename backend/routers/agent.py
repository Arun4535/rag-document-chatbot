from urllib.parse import unquote

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from models import ResearchRequest
from services.agent import ResearchAgent


router = APIRouter()


@router.post("/research")
async def research_agent(payload: ResearchRequest) -> StreamingResponse:
    return StreamingResponse(ResearchAgent().run(payload.topic), media_type="text/event-stream")


@router.get("/research/stream")
async def research_agent_stream(topic: str) -> StreamingResponse:
    decoded = unquote(topic).strip()
    if not decoded:
        raise HTTPException(status_code=400, detail="Topic is required")
    return StreamingResponse(ResearchAgent().run(decoded), media_type="text/event-stream")
