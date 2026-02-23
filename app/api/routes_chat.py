from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.api.deps import verify_api_key
from app.core.config import settings
from app.rag.embeddings import embed_texts
from app.rag.chroma_store import search_similar
from app.rag.prompt import build_rag_prompt
from app.rag.llm import generate_answer

router = APIRouter(prefix="/v1/chat", tags=["chat"])


class ChatRequest(BaseModel):
    question: str = Field(min_length=3, max_length=4000)


class ChatResponse(BaseModel):
    answer: str
    sources: list[dict]


@router.post("", response_model=ChatResponse)
def chat(request: ChatRequest, _: str = Depends(verify_api_key)):
    q_emb = embed_texts([request.question])[0]
    
    hits = search_similar(query_embedding=q_emb, top_k=settings.TOP_K)
    hits = hits[:settings.MAX_CONTEXT_CHUNKS]
    
    prompt = build_rag_prompt(question=request.question, chunks=hits)
    answer = generate_answer(prompt=prompt)
    
    sources = []
    for h in hits:
        meta = h.get("meta", {}) or {}
        sources.append({
            "post_id": meta.get("post_id"),
            "title": meta.get("title"),
            "url": meta.get("url"),
            "chunk_index": meta.get("chunk_index"),
            "distance": h.get("distance"),
            "excerpt": (h.get("text") or "")[:300],
        })
    
    return ChatResponse(answer=answer, sources=sources)
