# ============================================================
#  ShopNow — Makefile shortcuts
#  Usage: make <target>
# ============================================================

.PHONY: help dev up down restart logs \
        up-db up-api up-user up-admin \
        build rebuild rebuild-api rebuild-user rebuild-admin rebuild-db rebuild-user-api rebuild-admin-api \
        migrate seed superuser \
        status clean

# ── Default ──────────────────────────────────────────────────
help:
	@echo ""
	@echo "  ShopNow — available commands"
	@echo ""
	@echo "  make dev             		Start db + redis only (for native api/user-ui/admin-ui dev servers)"
	@echo "  make up             		Build & start all services (db, redis, api, user-ui, admin-ui, nginx)"
	@echo "  make down          		Stop all services"
	@echo "  make restart        		Stop then start all services"
	@echo "  make rebuild        		Force rebuild all images then start"
	@echo "  make rebuild-api		 		Force rebuild only the API image then start"
	@echo "  make rebuild-user-api 	Force rebuild only the API and User UI images then start"
	@echo "  make rebuild-admin-api 	Force rebuild only the API and Admin UI images then start"
	@echo "  make rebuild-user	 		Force rebuild only the User UI image then start"
	@echo "  make rebuild-admin	 		Force rebuild only the Admin UI image then start"
	@echo "  make rebuild-db		 		Force rebuild only the DB image then start"
	@echo "  make migrate        		Run Django migrations (requires API to be running)"
	@echo "  make seed           		Run database seed script (requires API to be running)"
	@echo "  make superuser      		Create a Django admin superuser (interactive)"
	@echo "  make logs           		Tail logs from all services"
	@echo "  make status         		Show running container status"
	@echo ""
	@echo "  make up-db          		Start only the database"
	@echo "  make up-api         		Start db + redis + api"
	@echo "  make up-user        		Start db + redis + api + user-ui"
	@echo "  make up-admin       		Start db + redis + api + admin-ui"
	@echo ""
	@echo "  make clean          Remove all containers, volumes, and images"
	@echo ""

# ── Local dev (native api/user-ui/admin-ui, containerised db+redis) ──
dev:
	docker compose -f docker-compose.dev.yml up -d
	@echo ""
	@echo "  🚀  db + redis running:"
	@echo "  db     → localhost:5432"
	@echo "  redis  → localhost:6379"
	@echo ""
	@echo "  Now run api/user-ui/admin-ui natively — see README 'Running Locally'"

# ── Core lifecycle ───────────────────────────────────────────
up:
	docker compose up --build -d
	@echo ""
	@echo "  🚀  Services starting up:"
	@echo "  nginx     → http://localhost"
	@echo "  user-ui   → http://localhost:3000"
	@echo "  admin-ui  → http://localhost:3001"
	@echo "  api       → http://localhost:8000"
	@echo "  db        → localhost:5432"
	@echo ""
	@echo "  Run 'make logs' to watch startup logs"

down:
	docker compose down

restart: down up

rebuild:
	docker compose down
	docker compose build --no-cache
	docker compose up -d

rebuild-api:
	docker compose build --no-cache api
	docker compose up -d api

rebuild-user:
	docker compose build --no-cache user-ui
	docker compose up -d user-ui

rebuild-admin:
	docker compose build --no-cache admin-ui
	docker compose up -d admin-ui

rebuild-db:
	docker compose build --no-cache db
	docker compose up -d db

rebuild-user-api:
	docker compose build --no-cache api user-ui
	docker compose up -d api user-ui

rebuild-admin-api:
	docker compose build --no-cache api admin-ui
	docker compose up -d api admin-ui

logs:
	docker compose logs -f

status:
	docker compose ps

# ── Individual services ──────────────────────────────────────
up-db:
	docker compose up --build -d db

up-api:
	docker compose up --build -d db redis api

up-user:
	docker compose up --build -d db redis api user-ui

up-admin:
	docker compose up --build -d db redis api admin-ui

# ── Django management ────────────────────────────────────────
migrate:
	docker compose exec api python manage.py migrate

seed:
	docker compose exec api python manage.py seed_db

superuser:
	docker compose exec api python manage.py createsuperuser

# ── Utilities ────────────────────────────────────────────────
clean:
	@echo "⚠️  This removes ALL containers, volumes and images for this project."
	@read -p "  Are you sure? [y/N] " confirm; \
	if [ "$$confirm" = "y" ]; then \
		docker compose down -v --rmi all --remove-orphans; \
		echo "✅  Clean done"; \
	else \
		echo "  Aborted"; \
	fi
