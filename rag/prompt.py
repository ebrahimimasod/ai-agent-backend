def build_rag_prompt(*, question: str, chunks: list[dict]) -> str:
    lines: list[str] = []
    lines.append('You will answer the user\'s question using the provided context snippets.')
    lines.append('If the context does not contain the answer, say you don\'t know.')
    lines.append('')
    lines.append('Question:')
    lines.append(question.strip())
    lines.append('')
    lines.append('Context snippets:')
    for i, ch in enumerate(chunks, start=1):
        meta = ch.get('meta', {}) or {}
        title = meta.get('title', '')
        url = meta.get('url', '')
        lines.append(f"\n[{i}] Title: {title}\nURL: {url}\nSnippet:\n{ch.get('text','')}")
    lines.append('\nAnswer in Persian:')
    return '\n'.join(lines)
