from datetime import datetime
from app.db.database import SessionLocal
from app.db.models import Job, Anomaly
from app.schemas import JobStatus
from app.worker.celery_app import celery_app
from app.cv.model import load_model
from app.cv.processor import process_video

model = load_model()


@celery_app.task
def process_video_task(job_id: str):
    db = SessionLocal()
    
    try:
        job = db.get(Job, job_id)
        if job is None:
            return 
        
        job.status = JobStatus.PROCESSING.value
        job.started_at = datetime.utcnow()
        db.commit()

        result = process_video(video_path = job.input_path, out_path = job.out_path, model = model)

        for anomaly_data in result["anomalies"]:
            anomaly = Anomaly(
                job_id = job.id,
                type = anomaly_data["type"],
                start_time = anomaly_data["start_time"],
                end_time = anomaly_data["end_time"]
            )

            db.add(anomaly)

        job.status = JobStatus.DONE.value
        job.count = result['count']
        
        job.finished_at = datetime.utcnow()
        db.commit()
        
    except Exception as e:
        job = db.get(Job, job_id)
        
        if job is not None:
            job.status = JobStatus.FAILED.value
            job.error = str(e)
            job.finished_at = datetime.utcnow()
            db.commit()

        raise

    finally:
        db.close()
        