from datetime import datetime, timezone
from flask import Blueprint, request, jsonify
from celery.result import AsyncResult

from app.api.deps import require_api_key
from app.db.session import SessionLocal
from app.db import crud
from app.tasks.ingest import ingest_wordpress

ingest_bp = Blueprint("ingest", __name__, url_prefix="/v1/ingest")


@ingest_bp.route("/run", methods=["POST"])
@require_api_key
def run_ingest():
    db = SessionLocal()
    try:
        full_resync = request.args.get("full_resync", "false").lower() == "true"
        task = ingest_wordpress.delay(full_resync=full_resync)
        crud.create_ingest_job(db, task.id)
        return jsonify({"job_id": task.id})
    finally:
        db.close()


@ingest_bp.route("/jobs/<job_id>", methods=["GET"])
@require_api_key
def job_status(job_id):
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

        return jsonify({"job_id": job_id, "status": status, "info": info})
    finally:
        db.close()
