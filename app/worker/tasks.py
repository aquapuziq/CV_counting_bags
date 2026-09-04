import time
from datetime import datetime
from app.db.database import SessionLocal
from app.db.models import Job
from app.schemas import JobStatus
from app.worker.celery_app import celery_app

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
        
        time.sleep(10)
        
        job.status = JobStatus.DONE.value
        job.count = 0
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
        