# RAG WordPress (Django + Celery + Chroma)

یک سیستم کامل RAG (Retrieval-Augmented Generation) که پست‌های وردپرس را دریافت، تکه‌بندی، embedding و ذخیره در ChromaDB می‌کند و یک رابط چت برای پاسخ به سوالات فراهم می‌آورد.

## معماری

- **API**: Django + Django REST Framework
- **Worker**: Celery
- **Broker/Backend**: Redis
- **Database**: PostgreSQL
- **Vector DB**: ChromaDB
- **Embedding Providers**: OpenAI یا Gemini
- **LLM Providers**: OpenAI یا Gemini

## نصب و راه‌اندازی

1. فایل `.env.example` را به `.env` کپی کنید:
   ```bash
   cp .env.example .env
   ```

2. فایل `.env` را ویرایش کرده و تنظیمات زیر را وارد کنید:
   - `API_KEY`: کلید API برای احراز هویت
   - `WP_BASE_URL`: آدرس سایت وردپرس شما
   - `OPENAI_API_KEY` یا `GEMINI_API_KEY`: کلید API ارائه‌دهنده LLM
   - سایر تنظیمات در صورت نیاز

3. مایگریشن‌های دیتابیس را اجرا کنید:
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

## اجرا

همه سرویس‌ها را با Docker Compose راه‌اندازی کنید:

```bash
docker compose up -d --build
```

API در آدرس `http://localhost:8001` در دسترس خواهد بود.

## API Endpoints

همه endpoint‌ها نیاز به هدر `X-API-Key` برای احراز هویت دارند.

### بررسی سلامت
```bash
GET /health
```

### دریافت پست‌های وردپرس
```bash
POST /v1/ingest/run?full_resync=false
```
برمی‌گرداند: `{"job_id": "..."}`

### بررسی وضعیت Job
```bash
GET /v1/ingest/jobs/{job_id}
```

### لیست پست‌ها
```bash
GET /v1/posts?page=1&per_page=20
```

### چت (RAG)
```bash
POST /v1/chat
Content-Type: application/json

{
  "question": "سوال شما اینجا"
}
```
برمی‌گرداند: `{"answer": "...", "sources": [...]}`

## مثال استفاده

```bash
# تنظیم API key
export API_KEY="your-api-key"

# اجرای ingest
curl -X POST "http://localhost:8001/v1/ingest/run?full_resync=true" \
  -H "X-API-Key: $API_KEY"

# پرسیدن سوال
curl -X POST "http://localhost:8001/v1/chat" \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"question": "این درباره چیست؟"}'
```

## توسعه

مشاهده لاگ‌ها:
```bash
docker compose logs -f api
docker compose logs -f worker
```

توقف سرویس‌ها:
```bash
docker compose down
```

rebuild بعد از تغییرات کد:
```bash
docker compose up -d --build
```

## تفاوت‌های اصلی با نسخه Flask

- استفاده از Django ORM به جای SQLAlchemy
- استفاده از Django REST Framework برای API
- سیستم احراز هویت Django
- مدیریت بهتر مایگریشن‌ها با Django migrations
- ساختار پروژه استاندارد Django
