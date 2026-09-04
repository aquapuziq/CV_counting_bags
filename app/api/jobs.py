from pathlib import Path
from uuid import uuid4
from fastapi import APIRouter, HTTPException, Depends, File, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models import Anomaly, Job
from app.schemas import AnomalyResponse, JobCreateResponse, JobResponse, JobStatus
from app.worker.tasks import process_video_task


router = APIRouter(
    prefix = "/jobs",
    tags = ['jobs']
)

DATA_DIR = Path("data")
INPUT_DIR = DATA_DIR / "input"
OUTPUT_DIR = DATA_DIR / "output"

INPUT_DIR.mkdir(parents = True, exist_ok = True)
OUTPUT_DIR.mkdir(parents = True, exist_ok = True)


@router.post(
    "",
    response_model = JobCreateResponse,
    status_code = status.HTTP_202_ACCEPTED
)

async def create_job(video: UploadFile = File(...), db: Session = Depends(get_db)):
    if not video.filename:
        raise HTTPException(
            status_code = 400,
            detail = "Miss filename"
        )

    suffix = Path(video.filename).suffix.lower()

    if suffix not in ".mp4":
        raise HTTPException(
            status_code = 400,
            detail = "Unsupp video format"
        )

    job_id = str(uuid4())

    input_path = INPUT_DIR / f"{job_id}.mp4"
    out_path = OUTPUT_DIR / f"{job_id}.mp4"

    try:
        with input_path.open("wb") as in_file:
            while chunk := await video.read(1024 * 1024):
                in_file.write(chunk)


    except Exception:
        if input_path.exists():
            input_path.unlink()

        raise HTTPException(
            status_code = 500,
            detail="Failed to save video"
        )

    job = Job(
        id = job_id,
        status = JobStatus.PENDING.value,
        input_path = str(input_path),
        out_path = str(out_path)
    )

    db.add(job)
    db.commit()

    process_video_task.delay(job_id)

    return JobCreateResponse(
        job_id = job.id,
        status = JobStatus(job.status)
    )


@router.get(
    "/{job_id}",
    response_model = JobResponse
)

def get_job(job_id: str, db: Session = Depends(get_db)):
    job = db.get(Job, job_id)

    if job is None:
        raise HTTPException(
            status_code = 400,
            detail = "Job not found"
        )

    anomalies = db.scalars(select(Anomaly).where(Anomaly.job_id == job_id)).all()

    return JobResponse(
        job_id = job.id,
        status = JobStatus(job.status),
        count = job.count,
        error = job.error,
        created_at = job.created_at,
        started_at = job.started_at,
        finished_at = job.finished_at,
        anomalies = [AnomalyResponse(
            type = anomaly.type,
            start_time = anomaly.start_time,
            end_time = anomaly.end_time
        ) for anomaly in anomalies]
    )


@router.get("/{job_id}/download")
def download_result(job_id: str, db: Session = Depends(get_db)):
    job = db.get(Job, job_id)

    if job is None:
        raise HTTPException(
            status_code = 404,
            detail = "Job not found"
        )

    if job.status != JobStatus.DONE.value:
        raise HTTPException(
            status_code = 409,
            detail = f"Job is not finished. Current status: {job.status}"
        )

    out_path = Path(job.out_path)

    if not out_path.exist():
        raise HTTPException(
            status_code = 404,
            detail = "Output video not found"
        )

    return FileResponse(
        path = output_path,
        filename = f"{job_id}.mp4"
    )










