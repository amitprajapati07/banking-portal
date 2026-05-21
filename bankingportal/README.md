# 🏦 Enterprise Banking Portal Backend

A production-ready, ultra-stable, and scalable banking backend built with Django, PostgreSQL, and Redis. Engineered for high concurrency, fault tolerance, and data integrity.

---

## 🚀 Quick Start (Dockerized)

Ensure you have **Docker** and **Docker Compose** installed.

1. **Clone and Enter Directory**
   ```bash
   git clone https://github.com/amitprajapati07/banking-portal.git
   cd banking-portal/bankingportal
   ```

2. **Set Up Credentials (.env)**
   Ensure you have a `.env` file configured. Provide your desired admin credentials:
   ```env
   ADMIN_USERNAME=admin
   ADMIN_EMAIL=admin@example.com
   ADMIN_PASSWORD=adminpassword123
   ```
   > 💡 **Zero-Touch Setup**: There are **no manual commands** required for database migrations, static file collection, or superuser creation! Everything is automated on startup.

3. **Start the Stack**
   ```bash
   docker compose up --build
   ```

4. **Access the Application**
   - **Admin Dashboard**: [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/) *(Log in with the credentials from your `.env`)*
   - **Main API**: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
   - **Swagger Docs**: [http://127.0.0.1:8000/api/schema/swagger-ui/](http://127.0.0.1:8000/api/schema/swagger-ui/)
   - **Redoc Docs**: [http://127.0.0.1:8000/api/schema/redoc/](http://127.0.0.1:8000/api/schema/redoc/)

---

## 🏛️ System Architecture

### 🛡️ Concurrency Control
Implements a dual-locking strategy to handle high-frequency balance updates:
- **Pessimistic Locking**: Uses `select_for_update()` in `TransferService` to lock accounts during transfers.
- **Optimistic Locking**: Every `Account` has a `version` field. Updates fail if the version has changed since it was read, preventing stale data writes.

### 🆔 Idempotency
Prevents double-spending and duplicate transactions using a Redis-backed `IdempotencyService`. Post requests requiring an `Idempotency-Key` header will return cached responses for 24 hours if the same key is reused.

### ⚡ Performance & Caching
- **Redis Caching**: Account balances and frequently accessed profiles are cached in Redis.
- **Optimized Queries**: Uses `select_related` and `prefetch_related` across all repositories to eliminate N+1 query problems.
- **Database Routing**: Configured with a `ReadWriteRouter` for PostgreSQL primary/replica support.

---

## 📖 API Documentation (Spectacular)

The project uses `drf-spectacular` for automated OpenAPI 3.0 schema generation.

| Endpoint | Description |
|----------|-------------|
| `/api/schema/` | Raw YAML/JSON OpenAPI Schema |
| `/api/schema/swagger-ui/` | Interactive API testing interface |
| `/api/schema/redoc/` | Clean, readable documentation |

---

## ⚙️ Configuration & Security

### Allowed Hosts
In production, `ALLOWED_HOSTS` is restricted for security. Currently configured to allow:
- `127.0.0.1`
- `localhost`
- `0.0.0.0` (Docker internal routing)

### Environment Variables (.env)
Key configurations are managed via `.env`:
- `SECRET_KEY`: Django security key.
- `DEBUG`: Set to `False` in production.
- `DB_NAME`, `DB_USER`, `DB_PASSWORD`: PostgreSQL credentials.
- `REDIS_URL`: Connection string for Redis cache and Celery broker.
- `RUN_MIGRATIONS`: Set to `true` on the web service to handle DB initialization.

---

## 🛠️ Tech Stack
- **Framework**: Django 4.2.16 (LTS)
- **API**: Django REST Framework + SimpleJWT
- **Database**: PostgreSQL 15
- **Task Queue**: Celery + Redis
- **Docs**: drf-spectacular
- **Server**: Gunicorn + WhiteNoise (Post-processed Static Files)
- **UI**: Django Jazzmin (Admin Theme)

---

## 🔍 Troubleshooting: Local Access

### `127.0.0.1` vs `localhost`
If you cannot access the portal via `http://localhost:8000`, use `http://127.0.0.1:8000` instead.

**Why?**
Modern browsers often enforce **HSTS (HTTPS Strict Transport Security)** on `localhost` if it has ever been used with HTTPS before. Since the local Docker environment uses `http` (no SSL), the browser may block the connection. Browsers typically do not enforce HSTS on IP addresses like `127.0.0.1`, making it the most reliable way to access the local development environment.

### Admin Dashboard Styling
If the Admin dashboard looks like standard Django (and not the premium Jazzmin theme), ensure you have run `docker compose up --build`. The `collectstatic` command runs automatically on startup to serve the theme files via WhiteNoise.
