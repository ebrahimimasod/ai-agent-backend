from flask import Blueprint, request, jsonify
from pydantic import BaseModel, Field, ValidationError

from app.api.deps import require_api_key
from app.core.config import settings
from app.rag.embeddings import embed_texts
from app.rag.chroma_store import search_similar
from app.rag.prompt import build_rag_prompt
from app.rag.llm import generate_answer

chat_bp = Blueprint("chat", __name__, url_prefix="/v1/chat")


class ChatRequest(BaseModel):
    question: str = Field(min_length=3, max_length=4000)


@chat_bp.route("", methods=["POST"])
@require_api_key
def chat():
    try:
        data = request.get_json()
        req = ChatRequest(**data)
    except ValidationError as e:
        return jsonify({"detail": e.errors()}), 400

    q_emb = embed_texts([req.question])[0]

    hits = search_similar(query_embedding=q_emb, top_k=settings.TOP_K)
    hits = hits[: settings.MAX_CONTEXT_CHUNKS]

    prompt = build_rag_prompt(question=req.question, chunks=hits)
    answer = generate_answer(prompt=prompt)

    sources = []
    for h in hits:
        meta = h.get("meta", {}) or {}
        sources.append(
            {
                "post_id": meta.get("post_id"),
                "title": meta.get("title"),
                "url": meta.get("url"),
                "chunk_index": meta.get("chunk_index"),
                "distance": h.get("distance"),
                "excerpt": (h.get("text") or "")[:300],
            }
        )

    return jsonify({"answer": answer, "sources": sources})
