from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from celery.result import AsyncResult

from app.api.deps import verify_api_key
from app.db.session import SessionLocal
from app.db import crud
from app.tasks.ingest import ingest_wordpress

router = APIRouter(prefix="/v1/ingest", tags=["ingest"])


class IngestResponse(BaseModel):
    job_id: str


class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    info: dict | str | None


@router.post("/run", response_model=IngestResponse)
def run_ingest(
    full_resync: bool = Query(False),
    _: str = Depends(verify_api_key)
):
    db = SessionLocal()
    try:
        task = ingest_wordpress.delay(full_resync=full_resync)
        crud.create_ingest_job(db, task.id)
        return IngestResponse(job_id=task.id)
    finally:
        db.close()


@router.get("/jobs/{job_id}", response_model=JobStatusResponse)
def job_status(job_id: str, _: str = Depends(verify_api_key)):
    db = SessionLocal()
    try:
        r = AsyncResult(job_id)
        status = str(r.status).lower()
        info = r.info if isinstance(r.info, (dict, str)) else None
        
        crud.update_ingest_job(
            db,
            job_id,
            status=status,
            message=str(info) if info else None,
            started_at=datetime.now(timezone.utc) if status == "started" else None,
            finished_at=datetime.now(timezone.utc) if status in ("success", "failure") else None,
        )
        
        return JobStatusResponse(job_id=job_id, status=status, info=info)
    finally:
        db.close()
