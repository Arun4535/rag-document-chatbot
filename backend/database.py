from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text, create_engine, func
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, relationship, sessionmaker

from config import get_settings


class Base(DeclarativeBase):
    pass


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    chunk_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="processing", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    evals: Mapped[list["Eval"]] = relationship(back_populates="document")


class Eval(Base):
    __tablename__ = "evals"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    doc_id: Mapped[str] = mapped_column(String(36), ForeignKey("documents.id"), nullable=False)
    session_id: Mapped[str] = mapped_column(String(100), nullable=False)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    sources_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    retrieval_scores: Mapped[list[float]] = mapped_column(JSON, default=list, nullable=False)
    feedback: Mapped[str | None] = mapped_column(String(16), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    document: Mapped[Document] = relationship(back_populates="evals")


settings = get_settings()

# QueuePool is used by default for PostgreSQL. pool_pre_ping avoids stale Render connections
# after idle periods, which is common on managed database services.
engine = create_engine(settings.database_url, pool_pre_ping=True, pool_size=5, max_overflow=10)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


def init_db() -> None:
    Base.metadata.create_all(bind=engine)


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def count_queries_by_day(db: Session) -> list[tuple[str, int]]:
    rows = (
        db.query(func.date(Eval.created_at), func.count(Eval.id))
        .group_by(func.date(Eval.created_at))
        .order_by(func.date(Eval.created_at))
        .all()
    )
    return [(str(day), int(count)) for day, count in rows]
