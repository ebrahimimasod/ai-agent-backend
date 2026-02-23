# RAG WordPress (FastAPI + Celery + Chroma)

یک سیستم کامل RAG (Retrieval-Augmented Generation) که پست‌های وردپرس را دریافت، تکه‌بندی، embedding و ذخیره در ChromaDB می‌کند و یک رابط چت برای پاسخ به سوالات فراهم می‌آورد.

## معماری

- **API**: FastAPI
- **Worker**: Celery
- **Broker/Backend**: Redis
- **Database**: PostgreSQL
- **Vector DB**: ChromaDB
- **Embedding Providers**: OpenAI یا Gemini
- **LLM Providers**: OpenAI یا Gemini

## نصب و راه‌اندازی سریع

### 1. تنظیمات محیطی

```bash
cp .env.example .env
```

فایل `.env` را ویرایش کنید:
```env
API_KEY=your-secret-api-key
WP_BASE_URL=https://your-wordpress-site.com
OPENAI_API_KEY=your-openai-key
# یا
GEMINI_API_KEY=your-gemini-key
```

### 2. اجرا با Docker

```bash
docker compose up -d --build
```

API در `http://localhost:8001` در دسترس است.

## API Endpoints

همه endpoint‌ها نیاز به هدر `X-API-Key` دارند.

### بررسی سلامت
```bash
GET /health
```

### دریافت پست‌های وردپرس
```bash
POST /v1/ingest/run?full_resync=false
```

**پاسخ:**
```json
{"job_id": "task-id"}
```

### بررسی وضعیت Job
```bash
GET /v1/ingest/jobs/{job_id}
```

### لیست پست‌ها
```bash
GET /v1/posts?page=1&per_page=20
```

### چت با RAG
```bash
POST /v1/chat
Content-Type: application/json

{
  "question": "سوال شما"
}
```

**پاسخ:**
```json
{
  "answer": "پاسخ به فارسی",
  "sources": [
    {
      "post_id": "123",
      "title": "عنوان پست",
      "url": "https://...",
      "chunk_index": 0,
      "distance": 0.234,
      "excerpt": "بخشی از متن..."
    }
  ]
}
```

## مثال استفاده

```bash
export API_KEY="your-api-key"

# اجرای ingest
curl -X POST "http://localhost:8001/v1/ingest/run?full_resync=true" \
  -H "X-API-Key: $API_KEY"

# پرسیدن سوال
curl -X POST "http://localhost:8001/v1/chat" \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"question": "این سایت درباره چیست؟"}'
```

## مستندات API

بعد از اجرا، مستندات تعاملی در دسترس است:
- Swagger UI: `http://localhost:8001/docs`
- ReDoc: `http://localhost:8001/redoc`

## توسعه

```bash
# مشاهده لاگ‌ها
docker compose logs -f api
docker compose logs -f worker

# توقف
docker compose down

# Rebuild
docker compose up -d --build
```

## ساختار پروژه

```
.
├── app/
│   ├── api/              # API routes
│   │   ├── routes_chat.py
│   │   ├── routes_ingest.py
│   │   ├── routes_posts.py
│   │   └── deps.py
│   ├── core/             # تنظیمات
│   │   └── config.py
│   ├── db/               # دیتابیس
│   │   ├── models.py
│   │   ├── crud.py
│   │   └── session.py
│   ├── rag/              # ماژول‌های RAG
│   │   ├── chroma_store.py
│   │   ├── chunking.py
│   │   ├── embeddings.py
│   │   ├── llm.py
│   │   ├── prompt.py
│   │   └── wordpress.py
│   ├── tasks/            # Celery tasks
│   │   ├── celery_app.py
│   │   └── ingest.py
│   └── main.py           # FastAPI app
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── README.md
```

## مجوز

MIT License
