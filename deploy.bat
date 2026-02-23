@echo off
REM اسکریپت Deploy خودکار برای Windows
REM این اسکریپت کد را از Git دریافت کرده و سرویس‌های Docker را restart می‌کند

echo ========================================
echo    شروع فرایند Deploy
echo ========================================

REM بررسی وجود docker-compose.yml
if not exist "docker-compose.yml" (
    echo [خطا] فایل docker-compose.yml یافت نشد!
    echo لطفاً این اسکریپت را در مسیر اصلی پروژه اجرا کنید.
    exit /b 1
)

REM مرحله 1: دریافت آخرین تغییرات از Git
echo.
echo [1/5] دریافت آخرین تغییرات از Git...
git fetch origin
git pull origin main
if errorlevel 1 (
    echo [خطا] دریافت تغییرات از Git با مشکل مواجه شد
    exit /b 1
)
echo [موفق] کد با موفقیت به‌روزرسانی شد

REM مرحله 2: بررسی فایل .env
echo.
echo [2/5] بررسی فایل .env...
if not exist ".env" (
    echo [خطا] فایل .env یافت نشد!
    if exist ".env.example" (
        echo آیا می‌خواهید از .env.example کپی بگیرید؟ (Y/N)
        set /p REPLY=
        if /i "%REPLY%"=="Y" (
            copy .env.example .env
            echo [موفق] فایل .env ایجاد شد. لطفاً آن را ویرایش کنید و دوباره deploy کنید
            exit /b 1
        ) else (
            exit /b 1
        )
    ) else (
        exit /b 1
    )
) else (
    echo [موفق] فایل .env موجود است
)

REM مرحله 3: توقف سرویس‌های قبلی
echo.
echo [3/5] توقف سرویس‌های قبلی...
docker compose down
echo [موفق] سرویس‌ها متوقف شدند

REM مرحله 4: Build و اجرای سرویس‌های جدید
echo.
echo [4/5] Build و اجرای سرویس‌های جدید...
docker compose build --no-cache
docker compose up -d
if errorlevel 1 (
    echo [خطا] راه‌اندازی سرویس‌ها با مشکل مواجه شد
    exit /b 1
)
echo [موفق] سرویس‌ها با موفقیت راه‌اندازی شدند

REM مرحله 5: بررسی وضعیت سرویس‌ها
echo.
echo [5/5] بررسی وضعیت سرویس‌ها...
timeout /t 5 /nobreak >nul

echo.
echo وضعیت Containers:
docker compose ps

echo.
echo بررسی Health Endpoint...
timeout /t 10 /nobreak >nul

curl -s -o nul -w "HTTP Status: %%{http_code}" http://localhost:8001/health
echo.

REM نمایش لاگ‌های اخیر
echo.
echo لاگ‌های اخیر API:
docker compose logs --tail=20 api

echo.
echo ========================================
echo    Deploy با موفقیت انجام شد!
echo ========================================

echo.
echo دستورات مفید:
echo   • مشاهده لاگ‌ها:        docker compose logs -f
echo   • مشاهده لاگ API:       docker compose logs -f api
echo   • مشاهده لاگ Worker:    docker compose logs -f worker
echo   • وضعیت سرویس‌ها:       docker compose ps
echo   • Restart سرویس‌ها:     docker compose restart
echo   • توقف سرویس‌ها:        docker compose down

echo.
echo API در دسترس است:
echo   • Health: http://localhost:8001/health
echo   • Docs:   http://localhost:8001/docs

pause
