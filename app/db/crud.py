from datetime import datetime, timezone
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.db.models import Post, IngestJob


def upsert_post(
    db: Session,
    *,
    wp_post_id: int,
    slug: str | None,
    url: str | None,
    title: str | None,
    modified_gmt: str | None,
    status: str | None,
) -> Post:
    post = db.scalar(select(Post).where(Post.wp_post_id == wp_post_id))
    if not post:
        post = Post(wp_post_id=wp_post_id)
        db.add(post)

    post.slug = slug
    post.url = url
    post.title = title
    post.modified_gmt = modified_gmt
    post.status = status
    post.last_ingested_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(post)
    return post


def list_posts(db: Session, *, page: int, per_page: int) -> tuple[list[Post], int]:
    total = db.scalar(select(func.count()).select_from(Post)) or 0
    items = db.scalars(
        select(Post)
        .order_by(Post.updated_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
    ).all()
    return items, total


def get_latest_modified_gmt(db: Session) -> str | None:
    return db.scalar(select(func.max(Post.modified_gmt)))


def create_ingest_job(db: Session, celery_task_id: str) -> IngestJob:
    job = IngestJob(celery_task_id=celery_task_id, status="queued")
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def update_ingest_job(
    db: Session,
    celery_task_id: str,
    *,
    status: str,
    message: str | None = None,
    started_at=None,
    finished_at=None,
) -> None:
    job = db.scalar(select(IngestJob).where(IngestJob.celery_task_id == celery_task_id))
    if not job:
        return
    job.status = status
    job.message = message
    if started_at is not None:
        job.started_at = started_at
    if finished_at is not None:
        job.finished_at = finished_at
    db.commit()
