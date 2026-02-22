from flask import Blueprint, request, jsonify

from app.api.deps import require_api_key
from app.db.session import SessionLocal
from app.db import crud

posts_bp = Blueprint("posts", __name__, url_prefix="/v1/posts")


@posts_bp.route("", methods=["GET"])
@require_api_key
def list_posts():
    db = SessionLocal()
    try:
        page = int(request.args.get("page", 1))
        per_page = int(request.args.get("per_page", 20))
        
        if page < 1:
            page = 1
        if per_page < 1 or per_page > 200:
            per_page = 20

        items, total = crud.list_posts(db, page=page, per_page=per_page)
        return jsonify({
            "page": page,
            "per_page": per_page,
            "total": total,
            "items": [
                {
                    "wp_post_id": p.wp_post_id,
                    "slug": p.slug,
                    "url": p.url,
                    "title": p.title,
                    "modified_gmt": p.modified_gmt,
                    "status": p.status,
                    "last_ingested_at": p.last_ingested_at.isoformat() if p.last_ingested_at else None,
                }
                for p in items
            ],
        })
    finally:
        db.close()
