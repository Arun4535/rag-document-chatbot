from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from database import Eval, count_queries_by_day, get_db
from models import EvalDashboardResponse, EvalFeedbackRequest, EvalRow, QueriesPerDay


router = APIRouter()


@router.get("", response_model=EvalDashboardResponse)
async def get_evals(db: Session = Depends(get_db)) -> EvalDashboardResponse:
    total = db.query(func.count(Eval.id)).scalar() or 0
    avg_sources = db.query(func.avg(Eval.sources_count)).scalar() or 0
    positives = db.query(func.count(Eval.id)).filter(Eval.feedback == "positive").scalar() or 0
    feedback_total = db.query(func.count(Eval.id)).filter(Eval.feedback.isnot(None)).scalar() or 0
    positive_pct = (positives / feedback_total * 100) if feedback_total else 0.0

    recent_records = db.query(Eval).order_by(Eval.created_at.desc()).limit(20).all()
    recent = [
        EvalRow(
            id=row.id,
            question=truncate(row.question, 90),
            answer_preview=truncate(row.answer, 120),
            sources_count=row.sources_count,
            feedback=row.feedback,
            timestamp=row.created_at,
        )
        for row in recent_records
    ]

    return EvalDashboardResponse(
        total_queries=int(total),
        avg_sources=float(avg_sources),
        positive_feedback_pct=round(float(positive_pct), 2),
        queries_per_day=[QueriesPerDay(date=day, count=count) for day, count in count_queries_by_day(db)],
        recent=recent,
    )


@router.post("/{eval_id}/feedback")
async def update_feedback(eval_id: str, payload: EvalFeedbackRequest, db: Session = Depends(get_db)) -> dict[str, str]:
    record = db.get(Eval, eval_id)
    if not record:
        raise HTTPException(status_code=404, detail="Eval record not found")
    record.feedback = payload.feedback
    db.commit()
    return {"status": "updated"}


def truncate(text: str, length: int) -> str:
    return text if len(text) <= length else f"{text[: length - 1]}..."
