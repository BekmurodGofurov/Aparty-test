# Aparty

Aparty is a student housing platform: listings, bookings and roommate ads. It is a monorepo of small services behind one gateway.

| Path | What it is |
|---|---|
| `client/` | React + Vite frontend |
| `microservices/api-gateway/` | Nginx gateway, the single entry point for the API (`localhost:8080`) |
| `microservices/services/iam-service/` | Telegram login, roles, JWT, profiles |
| `microservices/services/catalog-service/` | Listings, roommate ads, image upload |
| `microservices/services/order-service/` | Booking requests |
| `microservices/services/notification-service/` | Site notifications and Telegram messages |
| `bot/` | Telegram bot (greets users and links to the site) |
| `landing_page/` | Static landing page |
| `docs/` | Documentation |

Each service owns its PostgreSQL database and talks to the others over REST or RabbitMQ events. See [docs/services.md](docs/services.md) for endpoints, login flow, roles, roommate ads and configuration, [docs/frontend.md](docs/frontend.md) for the web app, and [MICROSERVICES_ROADMAP.md](MICROSERVICES_ROADMAP.md) for scope and next steps.

## Run everything with Docker

Requirements: Docker with Compose.

```bash
cp .env.example .env     # fill in every value, see the comments inside
docker compose up --build
curl localhost:8080/health
```

`docker compose` refuses to start when a required variable is missing. Databases are created from `postgres-init/`; on an existing Postgres volume, create a missing database by hand, for example `docker compose exec postgres psql -U <user> -c "CREATE DATABASE orders_db"`.

Telegram login needs a bot with Web Login enabled in @BotFather. Put its client id, secret and the frontend callback URL in `.env` (`TELEGRAM_CLIENT_ID`, `TELEGRAM_CLIENT_SECRET`, `TELEGRAM_REDIRECT_URI`); image upload needs `IMGBB_API_KEY`. These are required, so a missing or misspelled name stops `docker compose` with a message instead of failing later in the browser.

## Frontend

```bash
cd client
cp .env.example .env     # VITE_BACKEND_API points at the gateway
npm install
npm run dev
```

### Running with ngrok (for Telegram Login)

Telegram OAuth requires a public HTTPS address. Vite automatically proxies `/api` calls to the API gateway (`localhost:8080`), so ngrok must point to the frontend port (`5173`) to keep cookies first-party.

1. **Configure @BotFather**: Under `/mybots` → Bot Settings → Domain / Web Login, set the allowed redirect URI:
   ```text
   https://<your-ngrok-domain>/auth/telegram/callback
   ```
2. **Configure environment variables**:
   - In root `.env`:
     ```env
     TELEGRAM_REDIRECT_URI=https://<your-ngrok-domain>/auth/telegram/callback
     SITE_URL=https://<your-ngrok-domain>
     CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000,https://<your-ngrok-domain>
     ```
   - In `client/.env`:
     ```env
     DEV_ALLOWED_HOSTS=<your-ngrok-domain>
     DEV_API_PROXY_TARGET=http://localhost:8080
     VITE_BACKEND_API=
     ```
3. **Start backend services**:
   ```bash
   docker compose up -d
   ```
4. **Start the frontend**:
   ```bash
   cd client
   npm run dev        # live reload during development
   # or: npm run share  (builds and serves production bundle; saves tunnel quota and loads faster)
   ```
5. **Start ngrok tunnel**:
   ```bash
   ngrok http 5173 --url=<your-ngrok-domain>
   # example:
   # ngrok http 5173 --url=embellish-flattered-underpaid.ngrok-free.dev
   ```

See [docs/frontend.md](docs/frontend.md#sharing-through-a-tunnel-ngrok) for more tunnel and caching details.

## Tests

Service tests run against a real PostgreSQL database whose name ends with `_test`.

```bash
cd microservices/services/<service>
pip install -r requirements-dev.txt
TEST_DATABASE_URL=postgresql+asyncpg://<user>@localhost:5432/<service>_test pytest
```

Bot tests: `cd bot && pip install -r requirements-dev.txt && pytest`. Frontend: `cd client && npm test && npm run build`.

## Contributing

Use a feature branch and open a pull request to `main`; merges need a green CI. Keep code, comments and commit messages in English, keep values in configuration rather than in code, and update the docs when you add an endpoint. See [docs/BRANCH_PROTECTION.md](docs/BRANCH_PROTECTION.md).
