# راهنمای مهاجرت از Flask به Django

این پروژه از Flask به Django 5.1 (آخرین نسخه) بازنویسی شده است.

## تغییرات اصلی

### ساختار پروژه

```
پروژه قبلی (Flask):          پروژه جدید (Django):
app/                          config/              # تنظیمات Django
├── api/                      ├── settings.py
├── core/                     ├── urls.py
├── db/                       ├── wsgi.py
├── rag/                      ├── asgi.py
├── tasks/                    └── celery.py
└── main.py                   
                              core/                # اپلیکیشن اصلی
                              ├── models.py
                              ├── views.py
                              ├── serializers.py
                              ├── authentication.py
                              ├── tasks.py
                              └── urls.py
                              
                              rag/                 # ماژول RAG
                              ├── chroma_store.py
                              ├── chunking.py
                              ├── embeddings.py
                              ├── llm.py
                              ├── prompt.py
                              └── wordpress.py
                              
                              manage.py            # CLI Django
```

### تغییرات فنی

1. **ORM**: SQLAlchemy → Django ORM
2. **API Framework**: Flask → Django REST Framework
3. **احراز هویت**: دکوراتور سفارشی → DRF Authentication Class
4. **مدل‌ها**: SQLAlchemy models → Django models
5. **مایگریشن**: Alembic → Django migrations
6. **تنظیمات**: Pydantic Settings (حفظ شده) + Django Settings

### فایل‌های جدید

- `manage.py`: CLI اصلی Django
- `config/settings.py`: تنظیمات Django
- `config/celery.py`: پیکربندی Celery برای Django
- `core/models.py`: مدل‌های Django
- `core/views.py`: APIView‌های Django
- `core/serializers.py`: سریالایزرهای DRF
- `core/authentication.py`: کلاس احراز هویت سفارشی

### دستورات مهاجرت

```bash
# ایجاد مایگریشن‌ها
python manage.py makemigrations

# اجرای مایگریشن‌ها
python manage.py migrate

# ایجاد superuser (اختیاری)
python manage.py createsuperuser

# اجرای سرور توسعه
python manage.py runserver

# اجرای Celery worker
celery -A config worker --loglevel=INFO
```

### تغییرات در Docker

- پورت API: 5000 → 8000
- دستور اجرا: `flask run` → `gunicorn config.wsgi:application`
- دستور worker: `celery -A app.tasks.celery_app` → `celery -A config worker`

### API Endpoints (بدون تغییر)

همه endpoint‌ها همانند قبل کار می‌کنند:
- `GET /health`
- `POST /v1/ingest/run`
- `GET /v1/ingest/jobs/{job_id}`
- `GET /v1/posts`
- `POST /v1/chat`

### نکات مهم

1. همه کدهای RAG (embeddings, chunking, chroma, llm) بدون تغییر باقی مانده‌اند
2. احراز هویت با `X-API-Key` header همچنان کار می‌کند
3. Celery tasks با همان نام‌ها ثبت می‌شوند
4. پایگاه داده PostgreSQL بدون تغییر است

### مزایای Django

- ORM قدرتمندتر و کامل‌تر
- Admin panel داخلی (در صورت نیاز)
- سیستم مایگریشن بهتر
- امنیت بیشتر به صورت پیش‌فرض
- اکوسیستم بزرگتر و پشتیبانی بهتر
- مستندات جامع‌تر

## نصب و اجرا

```bash
# نصب dependencies
pip install -r requirements.txt

# مایگریشن دیتابیس
python manage.py migrate

# اجرا با Docker
docker compose up -d --build
```

پروژه آماده استفاده است!
