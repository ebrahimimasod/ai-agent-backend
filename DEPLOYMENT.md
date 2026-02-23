# راهنمای نصب و راه‌اندازی روی سرور Ubuntu با Docker

این راهنما مراحل کامل نصب و راه‌اندازی پروژه RAG WordPress را روی سرور Ubuntu با استفاده از Docker و اتصال به یک دامنه توضیح می‌دهد.

## پیش‌نیازها

- سرور Ubuntu 20.04 یا بالاتر
- دسترسی SSH به سرور
- یک دامنه (مثلاً: `api.example.com`)
- دسترسی به تنظیمات DNS دامنه

## مرحله 1: اتصال به سرور

```bash
ssh root@YOUR_SERVER_IP
# یا
ssh your_user@YOUR_SERVER_IP
```

## مرحله 2: نصب Docker و Docker Compose

```bash
# به‌روزرسانی پکیج‌ها
sudo apt update
sudo apt upgrade -y

# نصب پیش‌نیازها
sudo apt install -y apt-transport-https ca-certificates curl software-properties-common

# اضافه کردن GPG key رسمی Docker
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# اضافه کردن repository Docker
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# نصب Docker
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# فعال‌سازی Docker
sudo systemctl start docker
sudo systemctl enable docker

# اضافه کردن کاربر به گروه docker (اختیاری)
sudo usermod -aG docker $USER

# بررسی نصب
docker --version
docker compose version
```

## مرحله 3: نصب Nginx (برای Reverse Proxy)

```bash
sudo apt install -y nginx

# فعال‌سازی Nginx
sudo systemctl start nginx
sudo systemctl enable nginx
```

## مرحله 4: نصب Certbot (برای SSL رایگان)

```bash
sudo apt install -y certbot python3-certbot-nginx
```

## مرحله 5: آپلود پروژه به سرور

### روش 1: با Git (توصیه می‌شود)

```bash
# نصب Git
sudo apt install -y git

# کلون کردن پروژه
cd /opt
sudo git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git rag-wordpress
cd rag-wordpress

# یا اگر repository خصوصی است:
sudo git clone https://YOUR_TOKEN@github.com/YOUR_USERNAME/YOUR_REPO.git rag-wordpress
```

### روش 2: با SCP (از کامپیوتر محلی)

```bash
# از کامپیوتر محلی اجرا کنید:
scp -r /path/to/project root@YOUR_SERVER_IP:/opt/rag-wordpress
```

## مرحله 6: تنظیمات پروژه

```bash
cd /opt/rag-wordpress

# کپی کردن فایل .env
sudo cp .env.example .env

# ویرایش فایل .env
sudo nano .env
```

محتوای `.env` را به این صورت تنظیم کنید:

```env
# App
APP_NAME=rag-wp
API_KEY=YOUR_STRONG_API_KEY_HERE_CHANGE_ME
LOG_LEVEL=INFO

# WordPress
WP_BASE_URL=https://your-wordpress-site.com
WP_POSTS_PATH=/wp-json/wp/v2/posts
WP_PER_PAGE=100
WP_USERNAME=
WP_APP_PASSWORD=

# DB
DATABASE_URL=postgresql+psycopg2://rag:rag@postgres:5432/rag

# Redis / Celery
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# Chroma
CHROMA_HOST=chroma
CHROMA_PORT=8000
CHROMA_COLLECTION=wp_posts

# RAG tuning
CHUNK_SIZE=1200
CHUNK_OVERLAP=180
TOP_K=6
MAX_CONTEXT_CHUNKS=6

# Providers
EMBEDDING_PROVIDER=openai
LLM_PROVIDER=openai

# OpenAI
OPENAI_API_KEY=sk-your-openai-key-here
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
OPENAI_RESPONSES_MODEL=gpt-4o-mini

# Gemini (اگر از Gemini استفاده می‌کنید)
# EMBEDDING_PROVIDER=gemini
# LLM_PROVIDER=gemini
# GEMINI_API_KEY=your-gemini-key-here
# GEMINI_EMBEDDING_MODEL=models/embedding-001
# GEMINI_GENERATE_MODEL=gemini-2.0-flash-exp
```

ذخیره کنید: `Ctrl+X` سپس `Y` سپس `Enter`

## مرحله 7: تنظیم DNS

در پنل مدیریت دامنه خود، یک رکورد A اضافه کنید:

```
Type: A
Name: api (یا @ برای root domain)
Value: YOUR_SERVER_IP
TTL: 3600
```

بررسی کنید که DNS تنظیم شده:
```bash
nslookup api.example.com
```

## مرحله 8: تنظیم Nginx

```bash
# ایجاد فایل تنظیمات Nginx
sudo nano /etc/nginx/sites-available/rag-wordpress
```

محتوای فایل:

```nginx
server {
    listen 80;
    server_name api.example.com;  # دامنه خود را وارد کنید

    client_max_body_size 100M;

    location / {
        proxy_pass http://localhost:8001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        
        # Timeout settings
        proxy_connect_timeout 600;
        proxy_send_timeout 600;
        proxy_read_timeout 600;
        send_timeout 600;
    }
}
```

ذخیره و فعال‌سازی:

```bash
# ایجاد symlink
sudo ln -s /etc/nginx/sites-available/rag-wordpress /etc/nginx/sites-enabled/

# حذف تنظیمات پیش‌فرض (اختیاری)
sudo rm /etc/nginx/sites-enabled/default

# بررسی تنظیمات
sudo nginx -t

# Restart Nginx
sudo systemctl restart nginx
```

## مرحله 9: دریافت SSL Certificate (HTTPS)

```bash
sudo certbot --nginx -d api.example.com

# در حین نصب:
# - ایمیل خود را وارد کنید
# - شرایط را بپذیرید
# - گزینه Redirect را انتخاب کنید (توصیه می‌شود)
```

تمدید خودکار SSL:
```bash
# بررسی تمدید خودکار
sudo certbot renew --dry-run
```

## مرحله 10: اجرای پروژه با Docker

```bash
cd /opt/rag-wordpress

# Build و اجرای containers
sudo docker compose up -d --build

# بررسی وضعیت
sudo docker compose ps

# مشاهده لاگ‌ها
sudo docker compose logs -f
```

## مرحله 11: بررسی عملکرد

```bash
# بررسی health endpoint
curl https://api.example.com/health

# باید پاسخ دهد: {"ok":true}
```

مستندات API:
- Swagger UI: `https://api.example.com/docs`
- ReDoc: `https://api.example.com/redoc`

## مرحله 12: تست API

```bash
# تنظیم API Key
export API_KEY="YOUR_API_KEY_FROM_ENV_FILE"

# تست ingest
curl -X POST "https://api.example.com/v1/ingest/run?full_resync=true" \
  -H "X-API-Key: $API_KEY"

# تست chat
curl -X POST "https://api.example.com/v1/chat" \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"question": "این سایت درباره چیست؟"}'
```

## دستورات مفید

### مدیریت Docker Containers

```bash
# مشاهده لاگ‌ها
sudo docker compose logs -f api
sudo docker compose logs -f worker

# Restart همه سرویس‌ها
sudo docker compose restart

# Restart یک سرویس خاص
sudo docker compose restart api

# توقف همه سرویس‌ها
sudo docker compose down

# اجرای مجدد
sudo docker compose up -d

# حذف volumes (احتیاط: داده‌ها پاک می‌شود)
sudo docker compose down -v
```

### به‌روزرسانی پروژه

```bash
cd /opt/rag-wordpress

# دریافت آخرین تغییرات
sudo git pull

# Rebuild و اجرا
sudo docker compose down
sudo docker compose up -d --build
```

### مشاهده منابع سیستم

```bash
# استفاده از CPU و RAM
sudo docker stats

# فضای دیسک
df -h

# لاگ‌های Nginx
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### Backup دیتابیس

```bash
# Backup PostgreSQL
sudo docker compose exec postgres pg_dump -U rag rag > backup_$(date +%Y%m%d).sql

# Restore
sudo docker compose exec -T postgres psql -U rag rag < backup_20260223.sql
```

## امنیت

### 1. تنظیم Firewall

```bash
# نصب UFW
sudo apt install -y ufw

# اجازه دسترسی به پورت‌های ضروری
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS

# فعال‌سازی
sudo ufw enable

# بررسی وضعیت
sudo ufw status
```

### 2. تغییر پورت SSH (اختیاری اما توصیه می‌شود)

```bash
sudo nano /etc/ssh/sshd_config

# تغییر خط:
# Port 22
# به:
Port 2222

# Restart SSH
sudo systemctl restart sshd

# اجازه پورت جدید در firewall
sudo ufw allow 2222/tcp
```

### 3. غیرفعال کردن login با root

```bash
sudo nano /etc/ssh/sshd_config

# تغییر:
PermitRootLogin no

sudo systemctl restart sshd
```

### 4. نصب Fail2ban (محافظت در برابر حملات brute force)

```bash
sudo apt install -y fail2ban
sudo systemctl start fail2ban
sudo systemctl enable fail2ban
```

## مانیتورینگ

### نصب htop (مشاهده منابع)

```bash
sudo apt install -y htop
htop
```

### لاگ‌های سیستمی

```bash
# لاگ‌های Docker
sudo journalctl -u docker -f

# لاگ‌های Nginx
sudo tail -f /var/log/nginx/error.log
```

## عیب‌یابی

### مشکل: API پاسخ نمی‌دهد

```bash
# بررسی وضعیت containers
sudo docker compose ps

# بررسی لاگ‌ها
sudo docker compose logs api

# بررسی Nginx
sudo nginx -t
sudo systemctl status nginx
```

### مشکل: SSL کار نمی‌کند

```bash
# بررسی certificate
sudo certbot certificates

# تمدید دستی
sudo certbot renew
```

### مشکل: دیتابیس متصل نمی‌شود

```bash
# بررسی PostgreSQL
sudo docker compose exec postgres psql -U rag -d rag -c "SELECT 1;"

# Restart PostgreSQL
sudo docker compose restart postgres
```

### مشکل: Worker کار نمی‌کند

```bash
# بررسی لاگ worker
sudo docker compose logs worker

# Restart worker
sudo docker compose restart worker
```

## پشتیبان‌گیری خودکار

ایجاد اسکریپت backup:

```bash
sudo nano /opt/backup-rag.sh
```

محتوا:

```bash
#!/bin/bash
BACKUP_DIR="/opt/backups"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Backup PostgreSQL
docker compose -f /opt/rag-wordpress/docker-compose.yml exec -T postgres \
  pg_dump -U rag rag > $BACKUP_DIR/db_$DATE.sql

# Backup .env
cp /opt/rag-wordpress/.env $BACKUP_DIR/env_$DATE

# حذف backup‌های قدیمی (بیش از 7 روز)
find $BACKUP_DIR -name "*.sql" -mtime +7 -delete

echo "Backup completed: $DATE"
```

اجرای خودکار با cron:

```bash
sudo chmod +x /opt/backup-rag.sh

# ویرایش crontab
sudo crontab -e

# اضافه کردن (backup روزانه ساعت 2 صبح):
0 2 * * * /opt/backup-rag.sh >> /var/log/rag-backup.log 2>&1
```

## خلاصه

پروژه شما اکنون در دسترس است:
- **API**: `https://api.example.com`
- **Docs**: `https://api.example.com/docs`
- **Health**: `https://api.example.com/health`

برای پشتیبانی و سوالات، به مستندات پروژه مراجعه کنید.
