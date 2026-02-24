from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.db import crud
from app.rag.wordpress import fetch_posts, html_to_text
from app.rag.chunking import chunk_text
from app.rag.embeddings import embed_texts
from app.rag.chroma_store import upsert_post_chunks
from app.tasks.celery_app import celery_app


@celery_app.task(name="ingest_wordpress")
def ingest_wordpress(full_resync: bool = False) -> dict:
    db: Session = SessionLocal()
    try:
        now = datetime.now(timezone.utc)

        modified_after = None
        if not full_resync:
            modified_after = crud.get_latest_modified_gmt(db)

        posts = fetch_posts(modified_after=modified_after)

        processed = 0
        skipped = 0
        for p in posts:
            wp_id = int(p["id"])
            slug = p.get("slug")
            status = p.get("status")
            modified_gmt = p.get("modified_gmt")

            # Check if post needs reprocessing (embedding)
            if not crud.should_reprocess_post(db, wp_id, modified_gmt):
                print(f"Skipping post {wp_id} - already up to date (modified_gmt: {modified_gmt})")
                skipped += 1
                continue

            title = (p.get("title") or {}).get("rendered") if isinstance(p.get("title"), dict) else p.get("title")
            link = p.get("link")
            content_html = (p.get("content") or {}).get("rendered") if isinstance(p.get("content"), dict) else ""

            text = html_to_text(content_html or "")
            chunks = chunk_text(text)
            
            # Filter out empty chunks
            chunks = [c for c in chunks if c and c.strip()]
            
            if not chunks:
                continue

            print(f"Processing post {wp_id} - creating embeddings for {len(chunks)} chunks")
            embeddings = embed_texts(chunks)
            
            # Ensure chunks and embeddings have the same length
            if len(chunks) != len(embeddings):
                print(f"Warning: chunks ({len(chunks)}) and embeddings ({len(embeddings)}) length mismatch for post {wp_id}")
                continue
            
            upsert_post_chunks(
                post_id=wp_id,
                title=html_to_text(title or ""),
                url=link,
                modified_gmt=modified_gmt,
                chunks=chunks,
                embeddings=embeddings,
            )

            crud.upsert_post(
                db,
                wp_post_id=wp_id,
                slug=slug,
                url=link,
                title=html_to_text(title or ""),
                modified_gmt=modified_gmt,
                status=status,
            )
            processed += 1

        return {"ok": True, "processed_posts": processed, "skipped_posts": skipped, "fetched_posts": len(posts), "finished_at": now.isoformat()}
    finally:
        db.close()
