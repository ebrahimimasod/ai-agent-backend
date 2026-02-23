from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from app.api.deps import verify_api_key
from app.db.session import SessionLocal
from app.db import crud

router = APIRouter(prefix="/v1/posts", tags=["posts"])


class PostItem(BaseModel):
    wp_post_id: int
    slug: str | None
    url: str | None
    title: str | None
    modified_gmt: str | None
    status: str | None
    last_ingested_at: str | None

    class Config:
        from_attributes = True


class PostsResponse(BaseModel):
    page: int
    per_page: int
    total: int
    items: list[PostItem]


@router.get("", response_model=PostsResponse)
def list_posts(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=200),
    _: str = Depends(verify_api_key)
):
    db = SessionLocal()
    try:
        items, total = crud.list_posts(db, page=page, per_page=per_page)
        
        return PostsResponse(
            page=page,
            per_page=per_page,
            total=total,
            items=[
                PostItem(
                    wp_post_id=p.wp_post_id,
                    slug=p.slug,
                    url=p.url,
                    title=p.title,
                    modified_gmt=p.modified_gmt,
                    status=p.status,
                    last_ingested_at=p.last_ingested_at.isoformat() if p.last_ingested_at else None,
                )
                for p in items
            ]
        )
    finally:
        db.close()
