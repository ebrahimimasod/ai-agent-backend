from typing import Literal
import httpx
from config.settings import settings

Provider = Literal['openai', 'gemini']


def embed_texts(texts: list[str]) -> list[list[float]]:
    provider: Provider = settings.EMBEDDING_PROVIDER.lower()  # type: ignore
    if provider == 'gemini':
        return _embed_gemini(texts)
    return _embed_openai(texts)


def _embed_openai(texts: list[str]) -> list[list[float]]:
    if not settings.OPENAI_API_KEY:
        raise RuntimeError('OPENAI_API_KEY is missing')
    
    url = 'https://api.openai.com/v1/embeddings'
    headers = {'Authorization': f'Bearer {settings.OPENAI_API_KEY}', 'Content-Type': 'application/json'}
    payload = {'model': settings.OPENAI_EMBEDDING_MODEL, 'input': texts}
    
    with httpx.Client(timeout=60) as client:
        r = client.post(url, headers=headers, json=payload)
        r.raise_for_status()
        data = r.json()
    
    return [item['embedding'] for item in data['data']]


def _embed_gemini(texts: list[str]) -> list[list[float]]:
    if not settings.GEMINI_API_KEY:
        raise RuntimeError('GEMINI_API_KEY is missing')
    
    model = settings.GEMINI_EMBEDDING_MODEL
    url = f'https://generativelanguage.googleapis.com/v1beta/models/{model}:embedContent'
    headers = {'x-goog-api-key': settings.GEMINI_API_KEY, 'Content-Type': 'application/json'}
    
    payload = {'content': {'parts': [{'text': t} for t in texts]}}
    
    with httpx.Client(timeout=60) as client:
        r = client.post(url, headers=headers, json=payload)
        r.raise_for_status()
        data = r.json()
    
    if 'embeddings' in data:
        return [e['values'] for e in data['embeddings']]
    return [data['embedding']['values']]
