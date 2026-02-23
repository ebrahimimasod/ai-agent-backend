from datetime import datetime, timezone
from celery import shared_task
from django.utils import timezone as django_tz
from django.db.models import Max

from .models import Post
from rag.wordpress import fetch_posts, html_to_text
from rag.chunking import chunk_text
from rag.embeddings import embed_texts
from rag.chroma_store import upsert_post_chunks


@shared_task(name='ingest_wordpress')
def ingest_wordpress(full_resync: bool = False) -> dict:
    now = datetime.now(timezone.utc)
    
    modified_after = None
    if not full_resync:
        latest = Post.objects.aggregate(Max('modified_gmt'))['modified_gmt__max']
        modified_after = latest
    
    posts = fetch_posts(modified_after=modified_after)
    
    processed = 0
    for p in posts:
        wp_id = int(p['id'])
        slug = p.get('slug')
        status_val = p.get('status')
        modified_gmt = p.get('modified_gmt')
        
        title = (p.get('title') or {}).get('rendered') if isinstance(p.get('title'), dict) else p.get('title')
        link = p.get('link')
        content_html = (p.get('content') or {}).get('rendered') if isinstance(p.get('content'), dict) else ''
        
        text = html_to_text(content_html or '')
        chunks = chunk_text(text)
        if not chunks:
            continue
        
        embeddings = embed_texts(chunks)
        upsert_post_chunks(
            post_id=wp_id,
            title=html_to_text(title or ''),
            url=link,
            modified_gmt=modified_gmt,
            chunks=chunks,
            embeddings=embeddings,
        )
        
        Post.objects.update_or_create(
            wp_post_id=wp_id,
            defaults={
                'slug': slug,
                'url': link,
                'title': html_to_text(title or ''),
                'modified_gmt': modified_gmt,
                'status': status_val,
                'last_ingested_at': django_tz.now(),
            }
        )
        processed += 1
    
    return {
        'ok': True,
        'processed_posts': processed,
        'fetched_posts': len(posts),
        'finished_at': now.isoformat()
    }
