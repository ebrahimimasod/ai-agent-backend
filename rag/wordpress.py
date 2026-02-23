import base64
from typing import Any
import httpx
from bs4 import BeautifulSoup
from config.settings import settings


def _basic_auth_header() -> str | None:
    if settings.WP_USERNAME and settings.WP_APP_PASSWORD:
        raw = f"{settings.WP_USERNAME}:{settings.WP_APP_PASSWORD}".encode('utf-8')
        return 'Basic ' + base64.b64encode(raw).decode('ascii')
    return None


def html_to_text(html: str) -> str:
    soup = BeautifulSoup(html or '', 'html.parser')
    for tag in soup(['script', 'style', 'noscript']):
        tag.decompose()
    text = soup.get_text(separator='\n')
    return '\n'.join([line.strip() for line in text.splitlines() if line.strip()])


def fetch_posts(*, modified_after: str | None = None) -> list[dict[str, Any]]:
    url = settings.WP_BASE_URL.rstrip('/') + settings.WP_POSTS_PATH
    headers = {}
    auth = _basic_auth_header()
    if auth:
        headers['Authorization'] = auth
    
    out: list[dict[str, Any]] = []
    page = 1
    per_page = settings.WP_PER_PAGE
    
    with httpx.Client(timeout=60) as client:
        while True:
            params = {'page': page, 'per_page': per_page, 'status': 'publish'}
            if modified_after:
                params['modified_after'] = modified_after
            
            resp = client.get(url, params=params, headers=headers)
            if resp.status_code == 400 and 'rest_post_invalid_page_number' in resp.text:
                break
            resp.raise_for_status()
            
            items = resp.json()
            if not items:
                break
            
            out.extend(items)
            page += 1
    
    return out
