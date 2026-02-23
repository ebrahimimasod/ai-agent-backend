from config.settings import settings


def chunk_text(text: str) -> list[str]:
    text = (text or '').strip()
    if not text:
        return []
    
    size = max(200, settings.CHUNK_SIZE)
    overlap = max(0, min(settings.CHUNK_OVERLAP, size - 50))
    
    chunks: list[str] = []
    start = 0
    n = len(text)
    
    while start < n:
        end = min(n, start + size)
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= n:
            break
        start = end - overlap
    
    return chunks
