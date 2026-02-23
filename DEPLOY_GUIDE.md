# راهنمای استفاده از اسکریپت Deploy

این پروژه شامل اسکریپت‌های خودکار deploy است که فرایند به‌روزرسانی و راه‌اندازی مجدد را ساده می‌کند.

## فایل‌های موجود

- `deploy.sh` - اسکریپت deploy برای Linux/Mac
- `deploy.bat` - اسکریپت deploy برای Windows

## استفاده در Linux/Mac

### نصب اولیه

```bash
# دادن مجوز اجرا به اسکریپت
chmod +x deploy.sh
```

### اجرای Deploy

```bash
# اجرای ساده
./deploy.sh

# یا با sudo (در صورت نیاز)
sudo ./deploy.sh
```

## استفاده در Windows

### اجرای Deploy

```cmd
# اجرا در Command Prompt
deploy.bat

# یا اجرا در PowerShell
.\deploy.bat
```

یا می‌توانید روی فایل `deploy.bat` دوبار کلیک کنید.

## عملکرد اسکریپت

اسکریپت deploy به صورت خودکار مراحل زیر را انجام می‌دهد:

1. **دریافت آخرین تغییرات از Git**
   - بررسی branch فعلی
   - دریافت تغییرات جدید با `git pull`
   - مدیریت تغییرات محلی (در صورت وجود)

2. **بررسی فایل .env**
   - اطمینان از وجود فایل تنظیمات
   - پیشنهاد کپی از `.env.example` در صورت نبود

3. **توقف سرویس‌های قبلی**
   - اجرای `docker compose down`
   - توقف تمام containerها

4. **Build و اجرای سرویس‌های جدید**
   - Build مجدد imageها با `--no-cache`
   - راه‌اندازی سرویس‌ها با `docker compose up -d`

5. **بررسی وضعیت**
   - نمایش وضعیت containerها
   - تست health endpoint
   - نمایش لاگ‌های اخیر

## پیش‌نیازها

قبل از اجرای اسکریپت، مطمئن شوید که موارد زیر نصب شده‌اند:

- Git
- Docker
- Docker Compose

## استفاده در سرور Production

### راه‌اندازی اولیه

```bash
# اتصال به سرور
ssh user@your-server.com

# رفتن به مسیر پروژه
cd /opt/rag-wordpress

# دادن مجوز اجرا
chmod +x deploy.sh
```

### Deploy دستی

```bash
# اجرای deploy
./deploy.sh
```

### Deploy خودکار با Webhook

می‌توانید یک webhook در GitHub/GitLab تنظیم کنید که بعد از هر push، deploy را اجرا کند:

```bash
# نصب webhook listener (مثال با webhook)
npm install -g webhook

# ایجاد فایل تنظیمات webhook
cat > hooks.json << 'EOF'
[
  {
    "id": "deploy-rag",
    "execute-command": "/opt/rag-wordpress/deploy.sh",
    "command-working-directory": "/opt/rag-wordpress",
    "response-message": "Deploying...",
    "trigger-rule": {
      "match": {
        "type": "payload-hash-sha1",
        "secret": "YOUR_SECRET_HERE",
        "parameter": {
          "source": "header",
          "name": "X-Hub-Signature"
        }
      }
    }
  }
]
EOF

# اجرای webhook listener
webhook -hooks hooks.json -verbose -port 9000
```

### Deploy خودکار با Cron

برای deploy خودکار در زمان‌های مشخص:

```bash
# ویرایش crontab
crontab -e

# اضافه کردن (مثال: هر روز ساعت 3 صبح)
0 3 * * * cd /opt/rag-wordpress && ./deploy.sh >> /var/log/rag-deploy.log 2>&1
```

## عیب‌یابی

### خطا: Permission Denied

```bash
# دادن مجوز اجرا
chmod +x deploy.sh
```

### خطا: Git Pull Failed

```bash
# بررسی تغییرات محلی
git status

# reset کردن تغییرات محلی
git reset --hard HEAD
git pull
```

### خطا: Docker Compose Failed

```bash
# بررسی لاگ‌ها
docker compose logs

# پاک کردن کامل و شروع مجدد
docker compose down -v
docker compose up -d --build
```

### خطا: .env Not Found

```bash
# کپی از نمونه
cp .env.example .env

# ویرایش تنظیمات
nano .env
```

## دستورات مفید بعد از Deploy

```bash
# مشاهده لاگ‌های زنده
docker compose logs -f

# مشاهده لاگ یک سرویس خاص
docker compose logs -f api
docker compose logs -f worker

# بررسی وضعیت سرویس‌ها
docker compose ps

# Restart یک سرویس خاص
docker compose restart api

# بررسی health
curl http://localhost:8001/health

# مشاهده مستندات API
# در مرورگر: http://localhost:8001/docs
```

## Rollback (بازگشت به نسخه قبل)

در صورت بروز مشکل، می‌توانید به نسخه قبل برگردید:

```bash
# مشاهده تاریخچه commit‌ها
git log --oneline

# برگشت به commit قبلی
git checkout COMMIT_HASH

# اجرای deploy
./deploy.sh

# برگشت به آخرین نسخه
git checkout main
./deploy.sh
```

## نکات امنیتی

1. همیشه فایل `.env` را در `.gitignore` نگه دارید
2. از API Key های قوی استفاده کنید
3. دسترسی SSH را محدود کنید
4. از Firewall استفاده کنید
5. لاگ‌های deploy را بررسی کنید

## پشتیبانی

در صورت بروز مشکل:

1. لاگ‌های Docker را بررسی کنید: `docker compose logs`
2. وضعیت سرویس‌ها را چک کنید: `docker compose ps`
3. به مستندات اصلی مراجعه کنید: `DEPLOYMENT.md`
