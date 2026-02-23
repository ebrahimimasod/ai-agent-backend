from typing import Literal
import httpx

from app.core.config import settings

Provider = Literal["openai", "gemini"]


def embed_texts(texts: list[str]) -> list[list[float]]:
    provider: Provider = settings.EMBEDDING_PROVIDER.lower()  # type: ignore
    if provider == "gemini":
        return _embed_gemini(texts)
    return _embed_openai(texts)


def _embed_openai(texts: list[str]) -> list[list[float]]:
    if not settings.OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY is missing")

    url = "https://api.openai.com/v1/embeddings"
    headers = {"Authorization": f"Bearer {settings.OPENAI_API_KEY}", "Content-Type": "application/json"}
    payload = {"model": settings.OPENAI_EMBEDDING_MODEL, "input": texts}

    with httpx.Client(timeout=60) as client:
        r = client.post(url, headers=headers, json=payload)
        r.raise_for_status()
        data = r.json()

    return [item["embedding"] for item in data["data"]]


def _embed_gemini(texts: list[str]) -> list[list[float]]:
    if not settings.GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY is missing")

    model = settings.GEMINI_EMBEDDING_MODEL
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:embedContent"
    
    embeddings = []
    with httpx.Client(timeout=60) as client:
        for text in texts:
            # Skip empty or whitespace-only texts
            if not text or not text.strip():
                continue
            
            # Gemini has a limit of ~20k characters per request
            text = text[:20000] if len(text) > 20000 else text
            
            payload = {
                "model": f"models/{model}",
                "content": {
                    "parts": [{"text": text}]
                }
            }
            
            params = {"key": settings.GEMINI_API_KEY}
            
            try:
                r = client.post(url, params=params, json=payload)
                r.raise_for_status()
                data = r.json()
                embeddings.append(data["embedding"]["values"])
            except httpx.HTTPStatusError as e:
                # Log the error with more details
                print(f"Error embedding text (length: {len(text)}): {e}")
                print(f"Response: {e.response.text if hasattr(e, 'response') else 'No response'}")
                raise

    return embeddings
