from datetime import datetime, timezone
from django.core.paginator import Paginator
from rest_framework.decorators import api_view, authentication_classes
from rest_framework.response import Response
from rest_framework import status
from celery.result import AsyncResult

from .authentication import APIKeyAuthentication
from .models import Post, IngestJob
from .serializers import PostSerializer, ChatRequestSerializer
from .tasks import ingest_wordpress
from rag.embeddings import embed_texts
from rag.chroma_store import search_similar
from rag.prompt import build_rag_prompt
from rag.llm import generate_answer
from config.settings import settings


@api_view(['GET'])
def health(request):
    return Response({'ok': True})


@api_view(['POST'])
@authentication_classes([APIKeyAuthentication])
def run_ingest(request):
    full_resync = request.GET.get('full_resync', 'false').lower() == 'true'
    task = ingest_wordpress.delay(full_resync=full_resync)
    
    IngestJob.objects.create(
        celery_task_id=task.id,
        status='queued'
    )
    
    return Response({'job_id': task.id})


@api_view(['GET'])
@authentication_classes([APIKeyAuthentication])
def job_status(request, job_id):
    r = AsyncResult(job_id)
    task_status = str(r.status).lower()
    info = r.info if isinstance(r.info, (dict, str)) else None
    
    job, created = IngestJob.objects.get_or_create(
        celery_task_id=job_id,
        defaults={'status': task_status}
    )
    
    if not created:
        job.status = task_status
        job.message = str(info) if info else None
        
        if task_status == 'started' and not job.started_at:
            job.started_at = datetime.now(timezone.utc)
        
        if task_status in ('success', 'failure') and not job.finished_at:
            job.finished_at = datetime.now(timezone.utc)
        
        job.save()
    
    return Response({'job_id': job_id, 'status': task_status, 'info': info})


@api_view(['GET'])
@authentication_classes([APIKeyAuthentication])
def list_posts(request):
    page_num = int(request.GET.get('page', 1))
    per_page = int(request.GET.get('per_page', 20))
    
    if page_num < 1:
        page_num = 1
    if per_page < 1 or per_page > 200:
        per_page = 20
    
    posts = Post.objects.all()
    paginator = Paginator(posts, per_page)
    page_obj = paginator.get_page(page_num)
    
    serializer = PostSerializer(page_obj.object_list, many=True)
    
    return Response({
        'page': page_num,
        'per_page': per_page,
        'total': paginator.count,
        'items': serializer.data
    })


@api_view(['POST'])
@authentication_classes([APIKeyAuthentication])
def chat(request):
    serializer = ChatRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response({'detail': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    
    question = serializer.validated_data['question']
    
    q_emb = embed_texts([question])[0]
    hits = search_similar(query_embedding=q_emb, top_k=settings.TOP_K)
    hits = hits[:settings.MAX_CONTEXT_CHUNKS]
    
    prompt = build_rag_prompt(question=question, chunks=hits)
    answer = generate_answer(prompt=prompt)
    
    sources = []
    for h in hits:
        meta = h.get('meta', {}) or {}
        sources.append({
            'post_id': meta.get('post_id'),
            'title': meta.get('title'),
            'url': meta.get('url'),
            'chunk_index': meta.get('chunk_index'),
            'distance': h.get('distance'),
            'excerpt': (h.get('text') or '')[:300],
        })
    
    return Response({'answer': answer, 'sources': sources})
