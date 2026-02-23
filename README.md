# RAG WordPress (Django + Celery + Chroma)

یک سیستم کامل RAG (Retrieval-Augmented Generation) که پست‌های وردپرس را دریافت، تکه‌بندی، embedding و ذخیره در ChromaDB می‌کند و یک رابط چت برای پاسخ به سوالات فراهم می‌آورد.

## معماری

- **API**: Django 5.1 + Django REST Framework
- **Worker**: Celery
- **Broker/Backend**: Redis
- **Database**: PostgreSQL
- **Vector DB**: ChromaDB
- **Embedding Providers**: OpenAI یا Gemini
- **LLM Providers**: OpenAI یا Gemini

## نصب و راه‌اندازی

### 1. تنظیمات محیطی

فایل `.env.example` را به `.env` کپی کنید:
```bash
cp .env.example .env
```

فایل `.env` را ویرایش کرده و تنظیمات زیر را وارد کنید:
```env
# App
API_KEY=your-secret-api-key
SECRET_KEY=django-secret-key-change-in-production

# WordPress
WP_BASE_URL=https://your-wordpress-site.com

# Database
DATABASE_URL=postgresql+psycopg2://rag:rag@postgres:5432/rag

# Redis
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# AI Provider (OpenAI or Gemini)
EMBEDDING_PROVIDER=openai
LLM_PROVIDER=openai
OPENAI_API_KEY=your-openai-api-key

# یا برای استفاده از Gemini:
# EMBEDDING_PROVIDER=gemini
# LLM_PROVIDER=gemini
# GEMINI_API_KEY=your-gemini-api-key
```

### 2. اجرا با Docker (توصیه می‌شود)

```bash
docker compose up -d --build
```

API در آدرس `http://localhost:8001` در دسترس خواهد بود.

### 3. اجرای دستی (برای توسعه)

```bash
# نصب dependencies
pip install -r requirements.txt

# مایگریشن دیتابیس
python manage.py makemigrations
python manage.py migrate

# اجرای سرور
python manage.py runserver

# در ترمینال دیگر: اجرای Celery worker
celery -A config worker --loglevel=INFO
```

## API Endpoints

همه endpoint‌ها نیاز به هدر `X-API-Key` برای احراز هویت دارند.

### بررسی سلامت سیستم
```bash
GET /health
```

**پاسخ:**
```json
{"ok": true}
```

### دریافت و پردازش پست‌های وردپرس
```bash
POST /v1/ingest/run?full_resync=false
```

**پارامترها:**
- `full_resync` (اختیاری): `true` برای دریافت مجدد همه پست‌ها، `false` برای فقط پست‌های جدید (پیش‌فرض)

**پاسخ:**
```json
{"job_id": "celery-task-id"}
```

### بررسی وضعیت Job
```bash
GET /v1/ingest/jobs/{job_id}
```

**پاسخ:**
```json
{
  "job_id": "celery-task-id",
  "status": "success",
  "info": {
    "ok": true,
    "processed_posts": 42,
    "fetched_posts": 42,
    "finished_at": "2026-02-23T12:00:00"
  }
}
```

### لیست پست‌های ذخیره شده
```bash
GET /v1/posts?page=1&per_page=20
```

**پارامترها:**
- `page` (اختیاری): شماره صفحه (پیش‌فرض: 1)
- `per_page` (اختیاری): تعداد آیتم در هر صفحه (پیش‌فرض: 20، حداکثر: 200)

**پاسخ:**
```json
{
  "page": 1,
  "per_page": 20,
  "total": 100,
  "items": [
    {
      "wp_post_id": 123,
      "slug": "post-slug",
      "url": "https://example.com/post",
      "title": "عنوان پست",
      "modified_gmt": "2026-02-23T10:00:00",
      "status": "publish",
      "last_ingested_at": "2026-02-23T12:00:00"
    }
  ]
}
```

### چت با RAG
```bash
POST /v1/chat
Content-Type: application/json

{
  "question": "سوال شما اینجا"
}
```

**پاسخ:**
```json
{
  "answer": "پاسخ به زبان فارسی براساس محتوای پست‌ها",
  "sources": [
    {
      "post_id": "123",
      "title": "عنوان پست",
      "url": "https://example.com/post",
      "chunk_index": 0,
      "distance": 0.234,
      "excerpt": "بخشی از متن پست که مرتبط است..."
    }
  ]
}
```

## مثال‌های استفاده

### با cURL

```bash
# تنظیم API key
export API_KEY="your-api-key"

# اجرای ingest (دریافت همه پست‌ها)
curl -X POST "http://localhost:8001/v1/ingest/run?full_resync=true" \
  -H "X-API-Key: $API_KEY"

# بررسی وضعیت job
curl -X GET "http://localhost:8001/v1/ingest/jobs/TASK-ID" \
  -H "X-API-Key: $API_KEY"

# لیست پست‌ها
curl -X GET "http://localhost:8001/v1/posts?page=1&per_page=10" \
  -H "X-API-Key: $API_KEY"

# پرسیدن سوال
curl -X POST "http://localhost:8001/v1/chat" \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"question": "این سایت درباره چیست؟"}'
```

### با Python

```python
import requests

API_KEY = "your-api-key"
BASE_URL = "http://localhost:8001"
headers = {"X-API-Key": API_KEY}

# اجرای ingest
response = requests.post(
    f"{BASE_URL}/v1/ingest/run?full_resync=true",
    headers=headers
)
job_id = response.json()["job_id"]
print(f"Job ID: {job_id}")

# پرسیدن سوال
response = requests.post(
    f"{BASE_URL}/v1/chat",
    headers=headers,
    json={"question": "چگونه می‌توانم شروع کنم؟"}
)
result = response.json()
print(f"پاسخ: {result['answer']}")
print(f"منابع: {len(result['sources'])} پست")
```

## توسعه و دیباگ

### مشاهده لاگ‌ها

```bash
# لاگ API
docker compose logs -f api

# لاگ Worker
docker compose logs -f worker

# لاگ همه سرویس‌ها
docker compose logs -f
```

### توقف سرویس‌ها

```bash
docker compose down
```

### Rebuild بعد از تغییرات

```bash
docker compose up -d --build
```

### دسترسی به Django Admin (اختیاری)

```bash
# ایجاد superuser
docker compose exec api python manage.py createsuperuser

# سپس به آدرس http://localhost:8001/admin بروید
```

## تنظیمات RAG

می‌توانید پارامترهای RAG را در فایل `.env` تنظیم کنید:

```env
# اندازه هر chunk از متن (کاراکتر)
CHUNK_SIZE=1200

# همپوشانی بین chunk‌ها (کاراکتر)
CHUNK_OVERLAP=180

# تعداد chunk‌های مشابه برای جستجو
TOP_K=6

# حداکثر chunk‌ها برای context
MAX_CONTEXT_CHUNKS=6
```

## ساختار پروژه

```
.
├── config/              # تنظیمات Django
│   ├── settings.py      # تنظیمات اصلی
│   ├── urls.py          # URL routing
│   ├── celery.py        # پیکربندی Celery
│   └── wsgi.py          # WSGI application
│
├── core/                # اپلیکیشن اصلی Django
│   ├── models.py        # مدل‌های دیتابیس
│   ├── views.py         # API views
│   ├── serializers.py   # DRF serializers
│   ├── authentication.py # احراز هویت
│   ├── tasks.py         # Celery tasks
│   └── urls.py          # URL patterns
│
├── rag/                 # ماژول‌های RAG
│   ├── chroma_store.py  # مدیریت ChromaDB
│   ├── chunking.py      # تکه‌بندی متن
│   ├── embeddings.py    # ایجاد embeddings
│   ├── llm.py           # تولید پاسخ با LLM
│   ├── prompt.py        # ساخت prompt
│   └── wordpress.py     # دریافت از WordPress
│
├── manage.py            # Django CLI
├── requirements.txt     # Dependencies
├── docker-compose.yml   # Docker services
├── Dockerfile           # Docker image
└── README.md            # این فایل
```

## عیب‌یابی

### خطای اتصال به ChromaDB
اطمینان حاصل کنید که سرویس Chroma در حال اجراست:
```bash
docker compose ps chroma
```

### خطای اتصال به PostgreSQL
بررسی کنید که `DATABASE_URL` در `.env` صحیح است و PostgreSQL در حال اجراست.

### Celery task اجرا نمی‌شود
مطمئن شوید که worker در حال اجراست:
```bash
docker compose ps worker
docker compose logs worker
```

### خطای API Key
مطمئن شوید که هدر `X-API-Key` را با مقدار صحیح ارسال می‌کنید.

## مجوز

این پروژه تحت مجوز MIT منتشر شده است.

## پشتیبانی

برای گزارش مشکلات یا پیشنهادات، لطفاً یک Issue ایجاد کنید.
