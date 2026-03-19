#!/bin/sh
set -e
until pg_isready -h db -p 5432 -U ecom_user; do sleep 2; done
python manage.py migrate --noinput
python manage.py collectstatic --noinput
exec gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 4 --timeout 120 --access-logfile - --error-logfile -
