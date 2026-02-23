#!/bin/bash

# اسکریپت Deploy خودکار
# این اسکریپت کد را از Git دریافت کرده و سرویس‌های Docker را restart می‌کند

set -e  # در صورت بروز خطا، اسکریپت متوقف شود

# رنگ‌ها برای خروجی
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}   شروع فرایند Deploy${NC}"
echo -e "${GREEN}========================================${NC}"

# بررسی اینکه آیا در مسیر صحیح هستیم
if [ ! -f "docker-compose.yml" ]; then
    echo -e "${RED}خطا: فایل docker-compose.yml یافت نشد!${NC}"
    echo -e "${RED}لطفاً این اسکریپت را در مسیر اصلی پروژه اجرا کنید.${NC}"
    exit 1
fi

# مرحله 1: دریافت آخرین تغییرات از Git
echo -e "\n${YELLOW}[1/5] دریافت آخرین تغییرات از Git...${NC}"
git fetch origin
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
echo -e "Branch فعلی: ${GREEN}$CURRENT_BRANCH${NC}"

# بررسی تغییرات محلی
if [[ -n $(git status -s) ]]; then
    echo -e "${YELLOW}هشدار: تغییرات ذخیره نشده محلی وجود دارد${NC}"
    read -p "آیا می‌خواهید تغییرات محلی را نادیده بگیرید و pull کنید؟ (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        git reset --hard HEAD
        echo -e "${GREEN}تغییرات محلی reset شد${NC}"
    else
        echo -e "${RED}Deploy لغو شد${NC}"
        exit 1
    fi
fi

git pull origin $CURRENT_BRANCH
echo -e "${GREEN}✓ کد با موفقیت به‌روزرسانی شد${NC}"

# مرحله 2: بررسی فایل .env
echo -e "\n${YELLOW}[2/5] بررسی فایل .env...${NC}"
if [ ! -f ".env" ]; then
    echo -e "${RED}خطا: فایل .env یافت نشد!${NC}"
    if [ -f ".env.example" ]; then
        echo -e "${YELLOW}آیا می‌خواهید از .env.example کپی بگیرید؟ (y/n): ${NC}"
        read -p "" -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            cp .env.example .env
            echo -e "${GREEN}✓ فایل .env ایجاد شد. لطفاً آن را ویرایش کنید و دوباره deploy کنید${NC}"
            exit 1
        else
            exit 1
        fi
    else
        exit 1
    fi
else
    echo -e "${GREEN}✓ فایل .env موجود است${NC}"
fi

# مرحله 3: توقف سرویس‌های قبلی
echo -e "\n${YELLOW}[3/5] توقف سرویس‌های قبلی...${NC}"
docker compose down
echo -e "${GREEN}✓ سرویس‌ها متوقف شدند${NC}"

# مرحله 4: Build و اجرای سرویس‌های جدید
echo -e "\n${YELLOW}[4/5] Build و اجرای سرویس‌های جدید...${NC}"
docker compose build --no-cache
docker compose up -d
echo -e "${GREEN}✓ سرویس‌ها با موفقیت راه‌اندازی شدند${NC}"

# مرحله 5: بررسی وضعیت سرویس‌ها
echo -e "\n${YELLOW}[5/5] بررسی وضعیت سرویس‌ها...${NC}"
sleep 5  # صبر برای راه‌اندازی کامل

echo -e "\n${GREEN}وضعیت Containers:${NC}"
docker compose ps

# بررسی health endpoint
echo -e "\n${YELLOW}بررسی Health Endpoint...${NC}"
sleep 10  # صبر بیشتر برای راه‌اندازی API

if command -v curl &> /dev/null; then
    HEALTH_CHECK=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8001/health || echo "000")
    if [ "$HEALTH_CHECK" = "200" ]; then
        echo -e "${GREEN}✓ API سالم است و در حال اجرا${NC}"
    else
        echo -e "${YELLOW}⚠ API هنوز آماده نیست (HTTP $HEALTH_CHECK)${NC}"
        echo -e "${YELLOW}لطفاً چند لحظه صبر کنید و لاگ‌ها را بررسی کنید${NC}"
    fi
else
    echo -e "${YELLOW}curl نصب نیست، بررسی health انجام نشد${NC}"
fi

# نمایش لاگ‌های اخیر
echo -e "\n${YELLOW}لاگ‌های اخیر API:${NC}"
docker compose logs --tail=20 api

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}   Deploy با موفقیت انجام شد! ✓${NC}"
echo -e "${GREEN}========================================${NC}"

echo -e "\n${YELLOW}دستورات مفید:${NC}"
echo -e "  • مشاهده لاگ‌ها:        ${GREEN}docker compose logs -f${NC}"
echo -e "  • مشاهده لاگ API:       ${GREEN}docker compose logs -f api${NC}"
echo -e "  • مشاهده لاگ Worker:    ${GREEN}docker compose logs -f worker${NC}"
echo -e "  • وضعیت سرویس‌ها:       ${GREEN}docker compose ps${NC}"
echo -e "  • Restart سرویس‌ها:     ${GREEN}docker compose restart${NC}"
echo -e "  • توقف سرویس‌ها:        ${GREEN}docker compose down${NC}"

echo -e "\n${YELLOW}API در دسترس است:${NC}"
echo -e "  • Health: ${GREEN}http://localhost:8001/health${NC}"
echo -e "  • Docs:   ${GREEN}http://localhost:8001/docs${NC}"
