# ShopNow — E-Commerce Platform

> A production-grade, cloud-native e-commerce platform built as a microservices
> architecture. Demonstrates full-stack development, containerisation, Kubernetes
> orchestration, GitOps, and security best practices end-to-end.

🌐 **Live demo:** https://shopnow.johnisah.com
📦 **Admin panel:** https://shopnow.johnisah.com/admin-panel/
📖 **API docs:** https://shopnow.johnisah.com/api/docs/

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend API** | Django 5.1 + Django REST Framework |
| **Customer UI** | Next.js 16 (App Router, SSR) |
| **Admin UI** | Next.js 16 + Recharts |
| **Database** | PostgreSQL 16 (StatefulSet + PVC) |
| **Cache / Queue** | Redis 7 |
| **Payments** | Stripe |
| **Auth** | JWT (SimpleJWT) + Email activation |
| **Container runtime** | Docker + Gunicorn |
| **Orchestration** | Kubernetes (Minikube) |
| **GitOps** | ArgoCD (App of Apps pattern, raw manifests) |
| **CI/CD** | GitHub Actions |
| **Secret management** | Infisical (operator + auto-sync) |
| **TLS** | cert-manager + Let's Encrypt |
| **Ingress** | Traefik Ingress Controller |
| **Image registry** | GitHub Container Registry (ghcr.io) |
| **Security scanning** | Trivy |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    GitHub Repository                         │
│  k8s/<service>/  ← raw manifests (source of truth)          │
│  k8s/argocd/     ← ArgoCD Applications                       │
└─────────────────┬───────────────────────────────────────────┘
                  │  git push → ArgoCD auto-syncs
                  ▼
┌─────────────────────────────────────────────────────────────┐
│              Kubernetes Cluster (Minikube)                   │
│                                                              │
│  Infisical Operator ──► api-secret (auto-synced)            │
│                                                              │
│  Traefik Ingress ──► /api/     → Django API  (2 replicas)  │
│                  ──► /          → User UI     (2 replicas) │
│                  ──► /admin-panel → Admin UI (1 replica)   │
│                                                              │
│  PostgreSQL StatefulSet + PVC (Retain policy)               │
│  Redis StatefulSet + PVC                                     │
│                                                              │
│  cert-manager + Let's Encrypt (HTTPS)                       │
└─────────────────────────────────────────────────────────────┘
```

---

## Features

### Customer Storefront
- Browse products by category with filtering and search
- Product detail pages with image gallery
- Shopping basket (Redis-backed, persists across sessions)
- Stripe payment integration
- JWT authentication with email activation flow
- Password reset via email
- Order history and account dashboard

### Admin Panel
- Dashboard with revenue charts and stock alerts
- Full product CRUD with image upload
- Category management
- Order management with status tracking
- Manual payment confirmation
- User management with deactivation

### API
- RESTful API with OpenAPI/Swagger documentation
- JWT authentication with refresh token rotation
- Health and readiness endpoints (used by K8s probes)
- Django admin interface

---

## Project Structure

```
ecommerce-platform/
├── api/                          # Django REST API
│   ├── apps/
│   │   ├── account/              # Custom user model, JWT auth
│   │   ├── core/                 # Health checks, permissions, email
│   │   ├── store/                # Products, categories, images
│   │   ├── basket/               # Redis-backed shopping basket
│   │   ├── orders/               # Order lifecycle management
│   │   └── payment/              # Stripe webhook integration
│   ├── config/
│   │   └── settings/
│   │       ├── base.py
│   │       ├── development.py
│   │       ├── production.py
│   │       └── local.py          # Minikube (no SSL redirect)
│   ├── Dockerfile
│   ├── entrypoint.sh
│   └── requirements.txt
│
├── user-ui/                      # Next.js customer storefront
│   ├── src/
│   │   ├── app/                  # App Router pages
│   │   ├── components/           # Reusable UI components
│   │   ├── lib/                  # API client, utilities
│   │   └── store/                # Zustand state management
│   ├── next.config.ts            # API proxy rewrites
│   └── Dockerfile
│
├── admin-ui/                     # Next.js admin dashboard
│   ├── src/
│   │   ├── app/(admin)/          # Dashboard, products, orders, users
│   │   ├── components/
│   │   └── lib/
│   ├── next.config.ts            # basePath + API proxy
│   └── Dockerfile
│
├── k8s/                           # Raw manifests — source of truth ArgoCD syncs from
│   ├── postgres/                 # StatefulSet + Service
│   ├── redis/                    # StatefulSet + Service
│   ├── api/                      # Deployment + Service + Migrate Job
│   ├── user-ui/                  # Deployment + Service
│   ├── admin-ui/                 # Deployment + Service
│   ├── ingress/                  # Ingress (path-based routing on one host)
│   ├── cert-manager/             # ClusterIssuer
│   ├── infisical/                # InfisicalSecret CRD
│   ├── policies/                 # NetworkPolicy, ResourceQuota, LimitRange, PDB
│   │
│   ├── argocd/                   # GitOps configuration
│   │   ├── project.yaml          # AppProject (RBAC)
│   │   ├── root-app.yaml         # App-of-Apps root
│   │   └── app-*.yaml            # One Application per service
│   │
│   └── storage/                  # StorageClass with Retain policy
│
└── .github/
    └── workflows/
        ├── api.yml               # Validate → lint/test → build → scan → push → update-manifest
        ├── user-ui.yml           # Validate → lint/typecheck → build → scan → push → update-manifest
        ├── admin-ui.yml          # Validate → lint/typecheck → build → scan → push → update-manifest
        ├── all-services.yml      # Runs all 3 pipelines + creates a GitHub Release
        ├── pr-checks.yml         # Fast lint/typecheck/test gate on every PR
        ├── iac-scan.yml          # Trivy config scan over k8s/
        ├── secret-scan.yml       # gitleaks
        └── argocd-sync.yml       # Manual ArgoCD sync trigger
```

---

## CI/CD Pipeline

```
git tag v1.0.0 && git push origin v1.0.0
        │
        ▼
GitHub Actions — Full Platform Release
├── API Pipeline
│   ├── pytest + flake8
│   ├── docker build
│   ├── trivy security scan
│   └── docker push → johnitopaisah/ecommerce-api:v1.0.0
│
├── User UI Pipeline
│   ├── eslint + next build (type-check)
│   ├── docker build
│   ├── trivy scan
│   └── docker push → johnitopaisah/ecommerce-user-ui:v1.0.0
│
└── Admin UI Pipeline (same pattern)

Each pipeline commits its new image tag straight to
k8s/<service>/deployment.yaml on merge — no separate deploy step.
ArgoCD picks up the change from there.
```

---

## GitOps Flow (ArgoCD)

```
git push to develop
      │
      ▼
ArgoCD detects the manifest change (polls every 3 min or webhook)
      │
      ▼
ArgoCD diffs live state vs. k8s/<service>/*.yaml in git
      │
      ▼
selfHeal + prune apply the diff directly (no Helm release involved)
      │
      ▼
Kubernetes applies changes → ArgoCD marks Healthy ✅
```

---

## Security Highlights

| Feature | Implementation |
|---------|---------------|
| **Zero secrets in git** | Infisical operator syncs secrets from cloud into K8s |
| **HTTPS** | cert-manager + Let's Encrypt — auto-renews |
| **Image scanning** | Trivy scans every Docker image in CI |
| **JWT auth** | Short-lived access tokens + rotating refresh tokens |
| **Data persistence** | PVC with `reclaimPolicy: Retain` — survives Deployment/StatefulSet deletion |
| **Non-root containers** | Django runs as uid 1001 |

---

## Running Locally

### Prerequisites
- Python 3.13+
- Node.js 20+
- Docker

### Quick start

```bash
git clone https://github.com/johnitopaisah/ecommerce-platform.git
cd ecommerce-platform

# Start infrastructure
docker compose up db redis -d

# API
cd api
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py seed_db
python manage.py runserver

# User UI (new terminal)
cd user-ui && npm install && npm run dev

# Admin UI (new terminal)
cd admin-ui && npm install && npm run dev -- --port 3001
```

| Service | URL |
|---------|-----|
| User storefront | http://localhost:3000 |
| Admin panel | http://localhost:3001 |
| API | http://localhost:8000/api/v1/ |
| Swagger docs | http://localhost:8000/api/docs/ |

**Test credentials:**
- Admin: `admin@test.com` / `Admin1234!`
- Customer: `customer@test.com` / `Customer1234!`

---

## Kubernetes Deployment

ShopNow runs on the same shared Minikube cluster as this author's other
projects — ArgoCD, cert-manager, Traefik, and the Infisical operator are
already installed cluster-wide and are not part of this repo. Onboarding
ShopNow onto that cluster is a one-time bootstrap:

```bash
# 1. Create the AppProject (RBAC boundary for shopnow-* Applications)
kubectl apply -f k8s/argocd/project.yaml

# 2. Create the App-of-Apps root — ArgoCD then discovers every
#    app-*.yaml under k8s/argocd/ on its own
kubectl apply -f k8s/argocd/root-app.yaml

# 3. Watch it sync
kubectl get applications -n argocd -l app.kubernetes.io/part-of=shopnow
```

Images are public on ghcr.io, so no image-pull secret is needed. The
Infisical machine-identity credentials for the `ecommerce` namespace are
created once, by hand, and are intentionally kept out of git — see
`k8s/infisical/infisical-secret.yaml` for the CRD shape.

---

## Key Design Decisions

**Next.js API proxy rewrites** — instead of baking the API URL into the JavaScript bundle at build time (`NEXT_PUBLIC_API_URL`), both UIs use Next.js server-side rewrites. The browser calls `/api/v1/...` (relative), Next.js proxies it to `http://api:8000` server-side. The same Docker image works on localhost, any IP, or any domain without rebuilding.

**Infisical over Kubernetes Secrets** — raw K8s secrets are base64, not encrypted. Infisical stores secrets encrypted at rest and in transit, with audit logs and RBAC. The operator syncs them into native K8s secrets automatically so pods consume them the standard way.

**StatefulSet for databases** — StatefulSets give each pod a stable DNS name (`postgres-0.postgres.ecommerce`) and a dedicated PVC. Combined with `reclaimPolicy: Retain`, data survives pod crashes, node reboots, and even the StatefulSet itself being deleted.

**App of Apps pattern** — a single ArgoCD Application watches `k8s/argocd/apps/`. Adding a new application to git automatically deploys it. No manual bootstrapping after the initial setup.

---

## What I Built

This project was built from scratch across 7 phases:

1. **Django API foundation** — custom user model, JWT auth, settings layers
2. **Core API** — products, basket (Redis), orders, Stripe payments
3. **Admin API** — staff-only endpoints, OpenAPI docs, image upload
4. **Customer UI** — Next.js storefront with SSR, Zustand state, Stripe
5. **Admin UI** — dashboard with charts, full CRUD, order management
6. **Containerisation** — multi-stage Dockerfiles, docker-compose, Nginx
7. **Kubernetes** — Minikube, raw manifests, ArgoCD GitOps

---

## Author

**John Itopa Isah**
- GitHub: [@johnitopaisah](https://github.com/johnitopaisah)
- LinkedIn: [linkedin.com/in/johnitopaisah](https://linkedin.com/in/johnitopaisah)
- Email: johnitopaisah@gmail.com
