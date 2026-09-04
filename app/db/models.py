from datetime import datetime
from sqlalchemy import (DateTime,  ForeignKey, Float, Integer, String, Text)
from sqlalchemy.orm import Mapped, mapped_column
from app.db.database import Base


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[str] = mapped_column(
        String,
        primary_key = True
    )

    status: Mapped[str] = mapped_column(
        String,
        nullable = False
    )

    input_path: Mapped[str] = mapped_column(
        String,
        nullable = False
    )

    out_path: Mapped[str] = mapped_column(
        String,
        nullable = False
    )

    count: Mapped[int | None] = mapped_column(
        Integer,
        nullable = True
    )

    error: Mapped[str | None] = mapped_column(
        Text,
        nullable = True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default = datetime.utcnow
    )

    started_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable = True
    )

    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable = True
    )


class Anomaly(Base):
    __tablename__ = "anomalies"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key = True,
        autoincrement = True
    )

    job_id: Mapped[str] = mapped_column(
        ForeignKey("jobs.id"),
        nullable = False
    )

    type: Mapped[str] = mapped_column(
        String,
        nullable = False
    )

    start_time: Mapped[float] = mapped_column(
        Float,
        nullable = False
    )

    end_time: Mapped[float | None] = mapped_column(
        Float,
        nullable = True
    )