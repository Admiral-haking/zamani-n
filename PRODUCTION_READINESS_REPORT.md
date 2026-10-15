# PRODUCTION READINESS REPORT - ZAMANI (B2B/Burger App)

**Generated:** 10/12/2026 13:45:38
**Source:** C:\Users\LOQ\Desktop\New folder (7)
**Project Type:** Django REST API (Backend) + Static HTML/JS Frontend

## 1. Project Architecture

### Backend
- **Framework:** Django 6.0.7 (Python 3.14 in dev env as noted)
- **API:** Django REST Framework 3.17.1 with JWT auth (SimpleJWT), drf-spectacular for Swagger
- **Database:** PostgreSQL (psycopg[binary]) configured via environment; also has db.sqlite3 and backup .sqlite files in repo
- **Auth:** Custom User model with roles (ADMIN, SECRETARY, DISTRIBUTOR, CUSTOMER), JWT authentication
- **Key Apps:** accounts, products, pricing, inventory, cart, orders, payments (Zarinpal), dashboard, tickets, customers, distributors, audit, returns, finance, notifications, reminders, sms, reports, cms, owner, etc.
- **CORS:** CORS_ALLOW_ALL_ORIGINS = True in settings (development-oriented)
- **Static/Media:** STATIC_ROOT/staticfiles, MEDIA_ROOT/media configured
- **WSGI/ASGI:** config.wsgi, config.asgi, passenger_wsgi.py present (hosted deployment hint)
- **Migrations:** Present across apps

### Frontend
- **Type:** Static HTML/CSS/JS (vanilla JS) in ront/ directory
- **Communication:** Uses JWT tokens, calls API at http://127.0.0.1:8000/api in dev or auto-detects based on origin
- **Assets:** css/, js/, image/, vendor/ (fontawesome, vazir), video/

### Project Layout
- backend/ (Django project + apps + manage.py + passenger_wsgi.py + requirements.txt + .env + .env.host.example)
- front/ (static frontend)
- database/ (backup sqlite files)
- zamani/ (folder in repo)
- AGENTS.md, backend_tree.txt

## 2. Current Deployment Blockers

**BLOCKERS (must fix/clarify):**
1. **Real secrets in repo**: ackend/.env contains DB_PASSWORD=Zm#2026!pg, and settings has hardcoded SECRET_KEY ('django-insecure-...'). Must not package these.
2. **CORS wide open**: CORS_ALLOW_ALL_ORIGINS = True - unsafe for production; needs trusted origins.
3. **DEBUG enabled by default**: DEBUG = os.environ.get('DJANGO_DEBUG','True') defaults to True.
4. **Database config defaults to dev values**: Defaults include dev password; needs production env.
5. **Frontend API base is dev-oriented**: JS auto-detects localhost; fine if served behind same origin or if API host configured. For production, must be correct.
6. **Local .env and sqlite3 present**: Could accidentally be packaged.
7. **Log files may exist**: ackend/logs/runserver.log present (dev artifact).
8. **CORS_ALLOW_ALL_ORIGINS + credentials implications**: Need to be explicit in production.

**POTENTIAL BLOCKERS:**
- Hosting must support Python/Django + Postgres (or allow SQLite but not recommended for multi-user). passenger_wsgi.py suggests cPanel/Passenger style.
- Static files need collection (collectstatic).
- Migrations must run on production DB.
- Some routes/endpoints exist; need to ensure health/checks if required.

## 3. Security Issues

**HIGH:**
- Hardcoded SECRET_KEY in settings.py (line ~70-80). Must load from env.
- Hardcoded DB credentials in settings defaults and present in .env. 
- .env file with real credentials exists in source - must exclude from deployment package.
- CORS_ALLOW_ALL_ORIGINS = True allows any origin.
- DEBUG=True by default is dangerous if env not set correctly.

**MEDIUM:**
- Frontend caches with no-store in index.html (good for dev) but consider normal caching for static assets in prod.
- JWT lifetimes are 60m/7d - review for prod needs.
- Swagger (/api/docs/) exposed if DEBUG or always - in prod should be behind auth or disabled? Currently only media/static added when DEBUG; docs routes are always registered.
- Error details in API responses follow DRF defaults; in DEBUG more verbose - with DEBUG off still need to ensure no sensitive leakage.
- File uploads via TicketAttachment - need validation (size/type), proper storage (MEDIA_ROOT writable). Also check permissions.
- No obvious explicit security headers middleware beyond Django defaults? (SecurityMiddleware present; CSP/HSTS/X-Content-Type-Options not explicitly configured) - may need per hosting.

**LOW/REVIEW:**
- Some PII-like fields in models (phone, national_code). Ensure not logged.
- Permission classes look mostly present for admin/staff operations.

**NOTE:** Do not print actual secret values. File paths: ackend/.env, ackend/config/settings.py.

## 4. Missing Configuration

For production deployment, need:
- .env (production) with: SECRET_KEY, DJANGO_DEBUG=false, DJANGO_ALLOWED_HOSTS, DJANGO_CSRF_TRUSTED_ORIGINS, DB_* (production), optional ZARINPAL_* etc. Template exists: .env.host.example (MihanWebHost oriented).
- Proper CORS_ALLOWED_ORIGINS (or regex) instead of allow-all when DEBUG false.
- CSRF_TRUSTED_ORIGINS must match https domains in prod.
- Static files collected to staticfiles/ (dir configured). 
- MEDIA_ROOT writable by server process.
- Ensure ALLOWED_HOSTS/CSRF_TRUSTED_ORIGINS from env only (no localhost-only defaults in prod context).

## 5. Database Migration & Deployment Requirements

- Engine: PostgreSQL. Connection from env vars.
- Migrations exist for apps. Must run: python manage.py migrate (order is fine by Django).
- Initial data: ackend/scripts/create_users.py creates 4 users (admin/secretary/distributor/customer). Also AGENTS.md mentions seed users; useful post-migrate.
- SQLite files exist (dev/local). Do not deploy SQLite containing dev data. If hosting provides Postgres, create schema via migrations.
- Ensure psycopg[binary] compatible with host Python (Django 6.x needs recent Python).
- No destructive operations in migrations observed in quick scan; proceed carefully.

## 6. Hosting Requirements

Based on codebase:
- **Runtime:** Python >= 3.12 (passenger_wsgi.py notes >=3.12; Django 6.0.7). Recommend 3.12+.
- **WSGI:** passenger_wsgi.py provided for Passenger; also standard gunicorn/uwsgi possible.
- **Database:** PostgreSQL (required by default config). Hosting must provide Postgres service or allow external.
- **Static files:** collectstatic to ackend/staticfiles/, then serve via web server (Nginx/Apache) or whitenoise. Not using whitenoise currently.
- **Media:** ackend/media/ writable, served by web server.
- **Frontend:** Static files in ront/ - can be served as static site (separately) or copied under static; frontend is separate HTML/JS calling API. Common: serve front/ as static and backend as API under /api.
- **Dependencies:** pip install -r backend/requirements.txt (or split). psycopg[binary] included.
- **Environment:** Set env vars via control panel (as per .env.host.example).
- **Ports:** Binding handled by WSGI server (not runserver in prod). 
- **Writable dirs:** ackend/logs/, ackend/media/, ackend/staticfiles/ (if collectstatic writes there).
- **Background workers/scheduled tasks:** None obvious (no celery/beat found). Tickets/reminders apps exist but implementation may be sync; check before assuming.
- **HTTPS:** Required for secure cookies/tokens in prod; set CSRF_TRUSTED_ORIGINS with https.

## 7. Issues That Can Be Fixed Automatically

- Create production-ready settings env handling (no hardcoded secrets; safe defaults when DEBUG=false). 
- Generate .env.example (template without secrets).
- Fix CORS for production (use CORS_ALLOWED_ORIGINS from env when not allowing all).
- Add production .gitignore considerations (ensure no .env packaged). 
- Create staticfiles/ and media/ dirs if missing with .gitkeep? But exclude runtime files.
- Add deployment scripts docs (migrate, collectstatic, createsuperuser/users).
- Sanitize frontend if any localhost hardcodes beyond API detection (api.js already detects; check other files).
- Create deployment docs as requested.

## 8. Issues Requiring Input/Hosting Info

- Confirm hosting provider (shared/cPanel with Passenger vs VPS with Nginx+Gunicorn). Affects static serving and commands.
- Confirm domain(s) for ALLOWED_HOSTS/CSRF_TRUSTED_ORIGINS.
- Confirm Postgres credentials from hosting panel.
- Decide if frontend served from same origin as backend or separately (CORS/origin). 
- Whether to disable Swagger in prod or protect it.
- If Zarinpal is used in prod, need merchant ID and sandbox settings.
- Confirm Python version available on host.
- Whether media uploads need cloud storage (not present).

**Evidence collected:** settings.py, requirements.txt, .env.host.example, api.js, urls, apps structure, passenger_wsgi.py.
