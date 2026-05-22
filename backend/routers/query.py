from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import Document, Eval, get_db
from models import QueryRequest, QueryResponse, Source
from services.embeddings import FastEmbedEmbeddings
from services.generator import ClaudeGenerator
from services.retrieval import HybridRetriever
from services.vectorstore import ChromaStore


router = APIRouter()


@router.post("", response_model=QueryResponse)
async def query_documents(payload: QueryRequest, db: Session = Depends(get_db)) -> QueryResponse:
    document = db.get(Document, payload.doc_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    if document.status != "complete":
        raise HTTPException(status_code=409, detail=f"Document is not ready: {document.status}")

    query_embedding = await FastEmbedEmbeddings().embed_query(payload.question)
    chunks = await HybridRetriever(ChromaStore()).retrieve(payload.doc_id, payload.question, query_embedding)
    if not chunks:
        raise HTTPException(status_code=404, detail="No indexed chunks found for this document")

    answer = await ClaudeGenerator().answer(payload.question, chunks)
    sources = [to_source(chunk) for chunk in chunks]

    eval_record = Eval(
        doc_id=payload.doc_id,
        session_id=payload.session_id,
        question=payload.question,
        answer=answer,
        sources_count=len(sources),
        retrieval_scores=[source.score for source in sources],
    )
    db.add(eval_record)
    db.commit()

    return QueryResponse(answer=answer, sources=sources, session_id=payload.session_id, eval_id=eval_record.id)


def to_source(chunk: dict) -> Source:
    metadata = chunk["metadata"]
    page = metadata.get("page")
    return Source(
        text=chunk["text"],
        score=float(chunk["score"]),
        page=None if page in (None, -1) else int(page),
        filename=metadata["filename"],
    )
