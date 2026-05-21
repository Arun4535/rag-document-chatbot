from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class IngestStatusResponse(BaseModel):
    doc_id: str
    status: Literal["processing", "complete", "failed"]
    chunk_count: int = 0


class QueryRequest(BaseModel):
    question: str = Field(..., min_length=1)
    doc_id: str
    session_id: str


class Source(BaseModel):
    text: str
    score: float
    page: int | None = None
    filename: str


class QueryResponse(BaseModel):
    answer: str
    sources: list[Source]
    session_id: str
    eval_id: str


class ResearchRequest(BaseModel):
    topic: str = Field(..., min_length=2)


class EvalFeedbackRequest(BaseModel):
    feedback: Literal["positive", "negative"]


class EvalRow(BaseModel):
    id: str
    question: str
    answer_preview: str
    sources_count: int
    feedback: str | None
    timestamp: datetime


class QueriesPerDay(BaseModel):
    date: str
    count: int


class EvalDashboardResponse(BaseModel):
    total_queries: int
    avg_sources: float
    positive_feedback_pct: float
    queries_per_day: list[QueriesPerDay]
    recent: list[EvalRow]
