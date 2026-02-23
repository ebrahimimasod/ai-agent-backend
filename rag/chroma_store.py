import chromadb
from chromadb.api.models.Collection import Collection
from config.settings import settings


def get_collection() -> Collection:
    client = chromadb.HttpClient(host=settings.CHROMA_HOST, port=settings.CHROMA_PORT)
    return client.get_or_create_collection(name=settings.CHROMA_COLLECTION)


def upsert_post_chunks(
    *,
    post_id: int,
    title: str | None,
    url: str | None,
    modified_gmt: str | None,
    chunks: list[str],
    embeddings: list[list[float]],
) -> None:
    col = get_collection()
    
    col.delete(where={'post_id': str(post_id)})
    
    ids = [f"{post_id}:{i}" for i in range(len(chunks))]
    metadatas = [
        {
            'post_id': str(post_id),
            'title': (title or '')[:500],
            'url': (url or '')[:2000],
            'modified_gmt': (modified_gmt or '')[:64],
            'chunk_index': i,
        }
        for i in range(len(chunks))
    ]
    
    col.add(ids=ids, documents=chunks, embeddings=embeddings, metadatas=metadatas)


def search_similar(*, query_embedding: list[float], top_k: int) -> list[dict]:
    col = get_collection()
    res = col.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        include=['documents', 'metadatas', 'distances', 'ids'],
    )
    docs = res.get('documents', [[]])[0]
    metas = res.get('metadatas', [[]])[0]
    dists = res.get('distances', [[]])[0]
    ids = res.get('ids', [[]])[0]
    
    out = []
    for i in range(len(docs)):
        out.append({'id': ids[i], 'text': docs[i], 'meta': metas[i], 'distance': dists[i]})
    return out
