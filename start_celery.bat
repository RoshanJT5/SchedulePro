@echo off
echo Starting Celery Worker...
echo Ensure Redis is running on localhost:6379!
celery -A app_with_navigation.celery worker --loglevel=info --pool=solo
