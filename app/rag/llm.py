import httpx
from app.core.config import settings


def generate_answer(*, prompt: str) -> str:
    provider = settings.LLM_PROVIDER.lower()
    if provider == "gemini":
        return _gen_gemini(prompt)
    return _gen_openai(prompt)


def _gen_openai(prompt: str) -> str:
    if not settings.OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY is missing")

    url = "https://api.openai.com/v1/responses"
    headers = {"Authorization": f"Bearer {settings.OPENAI_API_KEY}", "Content-Type": "application/json"}

    payload = {
        "model": settings.OPENAI_RESPONSES_MODEL,
        "instructions": "You are a helpful assistant. Answer in the same language as the user's question. Use the provided context only when relevant. If unknown, say you don't know.",
        "input": prompt,
    }

    with httpx.Client(timeout=90) as client:
        r = client.post(url, headers=headers, json=payload)
        r.raise_for_status()
        data = r.json()

    if isinstance(data, dict) and data.get("output_text"):
        return str(data["output_text"])

    text_parts: list[str] = []
    for item in data.get("output", []) or []:
        if item.get("type") == "message":
            for c in item.get("content", []) or []:
                if c.get("type") == "output_text" and c.get("text"):
                    text_parts.append(c["text"])
    return "\n".join(text_parts).strip() or ""


def _gen_gemini(prompt: str) -> str:
    if not settings.GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY is missing")

    model = settings.GEMINI_GENERATE_MODEL
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    headers = {"x-goog-api-key": settings.GEMINI_API_KEY, "Content-Type": "application/json"}
    payload = {"contents": [{"role": "user", "parts": [{"text": prompt}]}]}

    with httpx.Client(timeout=90) as client:
        r = client.post(url, headers=headers, json=payload)
        r.raise_for_status()
        data = r.json()

    candidates = data.get("candidates", []) or []
    if not candidates:
        return ""
    parts = candidates[0].get("content", {}).get("parts", []) or []
    return "".join([p.get("text", "") for p in parts]).strip()
