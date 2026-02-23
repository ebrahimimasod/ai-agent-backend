@echo off

echo Setting up Django project...

REM Install dependencies
pip install -r requirements.txt

REM Create migrations
python manage.py makemigrations

REM Run migrations
python manage.py migrate

echo Django setup complete!
echo To run the server: python manage.py runserver
echo To run celery worker: celery -A config worker --loglevel=INFO
