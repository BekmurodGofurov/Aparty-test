# Aparty

Aparty is a monorepo for a student housing platform. The current project has:

- `backend/` - FastAPI API, SQLAlchemy models, Alembic migrations, uploads, and demo data scripts.
- `client/` - React + Vite frontend.
- `database/` - standalone database helpers and raw SQL examples.
- `bot/` - Telegram bot registration flow.

## Requirements

- Python 3.11+ recommended
- Node.js 20+ recommended
- PostgreSQL database, currently configured through `backend/.env`

## Backend Setup

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Backend runs at:

```text
http://127.0.0.1:8000
```

Health check:

```bash
curl http://127.0.0.1:8000/api/v1/health
```

Expected response:

```json
{"status":"ok"}
```

## Client Setup

```bash
cd client
npm install
npm run dev
```

Client runs at Vite's local URL, usually:

```text
http://localhost:5173
```

The client uses this API base URL by default:

```text
http://localhost:8000/api/v1
```

To override it, create `client/.env`:

```env
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

## Environment

`backend/.env` is used by `app.config.Settings`. Main variables:

```env
DATABASE_URL=postgresql+asyncpg://...
SYNC_DATABASE_URL=postgresql+psycopg://...
JWT_SECRET_KEY=change-me
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_MINUTES=10080
DB_CONNECT_TIMEOUT_SECONDS=5
COOKIE_SECURE=false
GEMINI_API_KEY=
```

Do not commit real secrets.

## Database And Migrations

Alembic is configured in `backend/alembic.ini`.

```bash
cd backend
source .venv/bin/activate
alembic upgrade head
```

Useful database files:

- `database/sql/create_tables.sql`
- `database/sql/insert_seed.sql`
- `database/sql/select_examples.sql`
- `database/sql/update_examples.sql`
- `backend/scripts/demo_data.py`
- `backend/scripts/fast_seed.py`

The current demo database contains listings, users, roles, favorites, payments, reviews, rentals, subscriptions, and listing payments.

## Demo Accounts

Use these accounts only for local/demo testing.

Owner:

```text
phone: +998903330000
password: password123
```

Makler/Broker:

```text
phone: +998902220000
password: password123
```

Admin:

```text
phone: +998900000001
password: admin123
```

Admin must log in through the admin portal:

```text
http://localhost:5173/login?admin=true
```

If an admin uses the normal login page, the backend intentionally returns `403 Forbidden` with:

```text
Admin panelga kirish uchun maxsus portal'dan foydalaning
```

## Main API Routes

Base URL:

```text
/api/v1
```

Auth:

- `POST /auth/register`
- `POST /auth/login`
- `POST /auth/admin-login`
- `POST /auth/refresh`
- `POST /auth/logout`
- `GET /auth/me`
- `GET /users/me`

Listings:

- `GET /listings/search`
- `GET /listings/me`
- `GET /listings/{listing_id}`
- `POST /listings/`
- `PUT /listings/{listing_id}`
- `PATCH /listings/{listing_id}`
- `POST /listings/{listing_id}/upgrade-to-premium`

Other modules:

- `GET /favorites/me`
- `POST /favorites/{listing_id}`
- `POST /reviews/`
- `GET /reviews/listing/{listing_id}`
- `GET /subscriptions/me`
- `POST /subscriptions/{plan_id}`
- `POST /upload/image`
- `POST /ai/chat`
- `GET /admin/dashboard`
- `GET /admin/users`
- `GET /admin/listings`

## Roles

Current role names:

- `student`
- `owner`
- `makler`
- `admin`

Listing creation is allowed for:

- `owner`
- `makler`

Admin login is separated from normal login by design.

## Frontend Routes

Public:

- `/`
- `/search`
- `/listing/:id`
- `/login`
- `/register`

User:

- `/profile`
- `/my-room`

Owner:

- `/owner`
- `/owner/create`
- `/owner/listing/:id/edit`

Makler:

- `/makler`
- `/makler/create`
- `/makler/subscription`

Admin:

- `/admin`
- `/admin/listings`
- `/admin/users`
- `/admin/complaints`
- `/admin/revenue`

## Telegram Bot

Bot setup:

```bash
cd bot
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

Bot settings are loaded from `bot/.env`.

## Development Checks

Backend import/OpenAPI smoke check:

```bash
cd backend
source .venv/bin/activate
python -c "from app.main import app; print(len(app.openapi()['paths']))"
```

Client build:

```bash
cd client
npm run build
```

Client lint:

```bash
cd client
npm run lint
```

Note: full lint may still report older unrelated frontend lint issues. For small changes, run ESLint against the files you touched.

## Common Notes

- If `/search` shows no listings, check the API response from `/api/v1/listings/search?page=1&limit=12`.
- `200 OK` with `success: true` and non-empty `listings` means the backend is returning data correctly.
- `success: false` means the client should show the backend error instead of "Nothing found".
- `/auth/login` is for normal users only.
- `/auth/admin-login` is for admins only.
