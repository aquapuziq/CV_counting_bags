from fastapi import FastAPI
from app.api.jobs import router as jobs_router
from app.db.database import Base, engine
from app.db import models


Base.metadata.create_all(bind = engine)

app = FastAPI(
    title = "Bag Counter",
    description = "Async video processing and bag counting",
    version = "1.0.0"
)

app.include_router(jobs_router)

@app.get("/health")
def health():
    return{
        "status": "ok"
    }

