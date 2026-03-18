# E-Commerce Platform

A full-stack e-commerce platform built as a 3-tier microservices application.

| Layer | Technology | Port |
|-------|-----------|------|
| user-ui | Next.js 14 | 3000 |
| admin-ui | Next.js 14 | 3001 |
| api | Django REST Framework | 8000 |
| db | PostgreSQL 16 | 5432 |
| cache | Redis 7 | 6379 |

---

## Project structure

```
ecommerce-platform/
├── api/                  # Django REST API
│   ├── apps/
│   │   ├── core/         # health checks, shared exceptions, permissions
│   │   ├── account/      # user model, JWT auth
│   │   ├── store/        # products & categories
│   │   ├── basket/       # Redis-backed cart
│   │   ├── orders/       # order management
│   │   └── payment/      # Stripe integration
│   ├── config/
│   │   ├── settings/
│   │   │   ├── base.py
│   │   │   ├── development.py
│   │   │   └── production.py
│   │   ├── urls.py
│   │   ├── wsgi.py
│   │   └── asgi.py
│   ├── manage.py
│   ├── requirements.txt
│   ├── .env.example
│   └── entrypoint.sh
├── user-ui/              # Next.js customer app  (Phase 4)
├── admin-ui/             # Next.js admin app     (Phase 5)
├── nginx/                # Reverse proxy config  (Phase 6)
├── k8s/                  # Kubernetes manifests  (Phase 7)
├── docker-compose.yml
└── .gitignore
```

---

## Prerequisites

- Python 3.13+
- Docker Desktop (for PostgreSQL + Redis)
- Node.js 20+ (for front-ends, Phase 4 onwards)

---

## Phase 1 — Local API setup

### 1. Clone the repo

```bash
git clone <your-repo-url>
cd ecommerce-platform
```

### 2. Start PostgreSQL and Redis

```bash
docker compose up db redis -d
```

Verify both are healthy:

```bash
docker compose ps
```

Both services should show `healthy`.

### 3. Set up the Python virtual environment

```bash
cd api
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure environment variables

```bash
cp .env.example .env
```

The default `.env` already matches the Docker Compose credentials — no changes needed for local development.

### 5. Run migrations

```bash
python manage.py migrate
```

### 6. Create a superuser

```bash
python manage.py createsuperuser
```

When prompted, provide an email, username and password.
Because `is_active` defaults to `False`, you must manually activate the superuser:

```bash
python manage.py shell -c "
from apps.account.models import UserBase
u = UserBase.objects.get(email='your@email.com')
u.is_active = True
u.save()
print('Activated.')
"
```

### 7. Start the development server

```bash
python manage.py runserver
```

### 8. Verify everything works

| URL | Expected response |
|-----|------------------|
| http://localhost:8000/api/v1/health/ | `{"status": "ok"}` |
| http://localhost:8000/api/v1/ready/ | `{"status": "ok", "db": "ok", "cache": "ok"}` |
| http://localhost:8000/api/docs/ | Swagger UI |
| http://localhost:8000/api/redoc/ | ReDoc UI |
| http://localhost:8000/django-admin/ | Django admin login |

---

## Running tests

```bash
cd api
pytest
```

With coverage:

```bash
pytest --cov=apps --cov-report=term-missing
```

---

## Environment variables reference

See `api/.env.example` for the full list with descriptions.

Key variables:

| Variable | Description | Default (dev) |
|----------|-------------|---------------|
| `SECRET_KEY` | Django secret key | dev value in `.env` |
| `DATABASE_URL` | PostgreSQL connection string | `postgres://ecom_user:ecom_pass@localhost:5432/ecommerce_db` |
| `REDIS_URL` | Redis connection string | `redis://localhost:6379/0` |
| `DEBUG` | Debug mode | `True` |
| `STRIPE_SECRET_KEY` | Stripe secret key | empty |

---

## API documentation

Once the server is running, interactive docs are available at:

- **Swagger UI** — http://localhost:8000/api/docs/
- **ReDoc** — http://localhost:8000/api/redoc/
- **OpenAPI schema (JSON)** — http://localhost:8000/api/schema/

---

## Development workflow

```
Phase 1  ✅  Django API foundation (settings, auth, health)
Phase 2  🔲  Core API endpoints (products, basket, orders, payment)
Phase 3  🔲  Admin API + OpenAPI docs
Phase 4  🔲  user-ui (Next.js)
Phase 5  🔲  admin-ui (Next.js)
Phase 6  🔲  Docker containerisation
Phase 7  🔲  Kubernetes (minikube → AWS EKS)
```
