#!/bin/sh
# entrypoint.sh — runs inside the Docker container
# Waits for DB to be ready, runs migrations, then starts Gunicorn.

set -e

echo "==> Waiting for PostgreSQL..."
until pg_isready -h "${DB_HOST:-db}" -p "${DB_PORT:-5432}" -U "${DB_USER:-ecom_user}"; do
  echo "    PostgreSQL is unavailable — sleeping 2s"
  sleep 2
done
echo "==> PostgreSQL is up."

echo "==> Running migrations..."
python manage.py migrate --noinput

echo "==> Collecting static files..."
python manage.py collectstatic --noinput

echo "==> Starting Gunicorn..."
exec gunicorn config.wsgi:application \
  --bind 0.0.0.0:8000 \
  --workers "${GUNICORN_WORKERS:-4}" \
  --timeout "${GUNICORN_TIMEOUT:-120}" \
  --access-logfile - \
  --error-logfile -
