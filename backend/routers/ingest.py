import asyncio
from io import BytesIO

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile
from PyPDF2 import PdfReader
from sqlalchemy.orm import Session

from database import Document, SessionLocal, get_db
from models import IngestStatusResponse
from services.chunker import RecursiveTextSplitter
from services.embeddings import FastEmbedEmbeddings
from services.vectorstore import ChromaStore


router = APIRouter()


@router.post("")
async def ingest_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    if not file.filename:
        raise HTTPException(status_code=400, detail="Missing filename")
    if not file.filename.lower().endswith((".pdf", ".txt")):
        raise HTTPException(status_code=400, detail="Only PDF and TXT files are supported")

    content = await file.read()
    document = Document(filename=file.filename, status="processing", chunk_count=0)
    db.add(document)
    db.commit()

    background_tasks.add_task(process_document, document.id, file.filename, content)
    return {"doc_id": document.id, "status": "processing"}


@router.get("/status/{doc_id}", response_model=IngestStatusResponse)
async def ingest_status(doc_id: str, db: Session = Depends(get_db)) -> IngestStatusResponse:
    document = db.get(Document, doc_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return IngestStatusResponse(doc_id=document.id, status=document.status, chunk_count=document.chunk_count)


async def process_document(doc_id: str, filename: str, content: bytes) -> None:
    db = SessionLocal()
    try:
        pages = await asyncio.to_thread(extract_pages, filename, content)
        chunks = RecursiveTextSplitter(chunk_size=500, overlap=50).split_pages(pages)
        embeddings = await FastEmbedEmbeddings().embed_documents([chunk.text for chunk in chunks])
        await ChromaStore().add_chunks(doc_id, filename, chunks, embeddings)

        document = db.get(Document, doc_id)
        if document:
            document.status = "complete"
            document.chunk_count = len(chunks)
            db.commit()
    except Exception:
        document = db.get(Document, doc_id)
        if document:
            document.status = "failed"
            db.commit()
        raise
    finally:
        db.close()


def extract_pages(filename: str, content: bytes) -> list[tuple[str, int | None]]:
    if filename.lower().endswith(".txt"):
        return [(content.decode("utf-8", errors="ignore"), None)]

    reader = PdfReader(BytesIO(content))
    pages = []
    for index, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        if text.strip():
            pages.append((text, index))
    return pages
