# مهاجرت از FastAPI به Flask

این پروژه با موفقیت از FastAPI به Flask تبدیل شده است.

## تغییرات اصلی

### 1. فریمورک اصلی
- **قبل**: FastAPI با uvicorn
- **بعد**: Flask با flask-cors

### 2. ساختار Route ها
- **قبل**: استفاده از `APIRouter` و `@router.get/post`
- **بعد**: استفاده از `Blueprint` و `@bp.route`

### 3. Dependency Injection
- **قبل**: استفاده از `Depends()` برای authentication و database session
- **بعد**: استفاده از decorators (`@require_api_key`) و مدیریت دستی session

### 4. Request/Response Handling
- **قبل**: Pydantic models به صورت خودکار validate می‌شدند
- **بعد**: استفاده از `request.get_json()` و validation دستی با Pydantic

### 5. Response Format
- **قبل**: بازگشت مستقیم dictionary
- **بعد**: استفاده از `jsonify()` برای تبدیل به JSON response

### 6. Query Parameters
- **قبل**: استفاده از `Query()` با validation خودکار
- **بعد**: استفاده از `request.args.get()` با validation دستی

### 7. Path Parameters
- **قبل**: تعریف در decorator مثل `@router.get("/jobs/{job_id}")`
- **بعد**: تعریف در decorator مثل `@bp.route("/jobs/<job_id>")`

### 8. Error Handling
- **قبل**: `HTTPException` برای خطاها
- **بعد**: بازگشت tuple از `(jsonify(...), status_code)`

## فایل‌های تغییر یافته

1. `app/main.py` - تبدیل FastAPI app به Flask app
2. `app/api/deps.py` - تبدیل dependency به decorator
3. `app/api/routes_chat.py` - تبدیل router به blueprint
4. `app/api/routes_ingest.py` - تبدیل router به blueprint
5. `app/api/routes_posts.py` - تبدیل router به blueprint
6. `requirements.txt` - جایگزینی fastapi/uvicorn با flask/flask-cors
7. `docker-compose.yml` - تغییر command از uvicorn به flask
8. `README.md` - به‌روزرسانی مستندات

## نحوه اجرا

### Development
```bash
# نصب dependencies
pip install -r requirements.txt

# اجرای Flask app
flask run --host=0.0.0.0 --port=5000
```

### Production با Docker
```bash
docker compose up -d --build
```

API در آدرس `http://localhost:8001` در دسترس خواهد بود.

## نکات مهم

1. همه endpoint ها نیاز به header `X-API-Key` دارند
2. پورت پیش‌فرض از 8000 به 5000 تغییر کرده (داخل container)
3. پورت exposed همچنان 8001 است (خارج از container)
4. تمام functionality های قبلی حفظ شده‌اند
5. Celery worker بدون تغییر باقی مانده است

## تست API

```bash
# Health check
curl http://localhost:8001/health

# Ingest
curl -X POST "http://localhost:8001/v1/ingest/run?full_resync=true" \
  -H "X-API-Key: your-api-key"

# Chat
curl -X POST "http://localhost:8001/v1/chat" \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{"question": "سوال شما"}'
```
