from datetime import datetime
from enum import Enum
from pydantic import BaseModel

class JobStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    DONE = "done"
    FAILED = "failed"


class JobCreateResponse(BaseModel):
    job_id: str
    status: JobStatus


class AnomalyResponse(BaseModel):
    type: str
    start_time: float
    end_time: float | None


class JobResponse(BaseModel):
    job_id: str
    status: JobStatus

    count: int | None = None
    error: str | None = None

    created_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None

    anomalies: list[AnomalyResponse] = []


