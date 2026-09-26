# Aparty: Microservices Roadmap

**Goal:** an event-driven microservices architecture. The current state of each service is documented in [docs/services.md](docs/services.md).

**Core principle:** strict database isolation. No two services share a database. Services talk over REST (sync) or RabbitMQ (async).

## 1. Scope decisions

- **PostgreSQL only.** Never SQLite, in any service or test.
- **Images only.** No video upload or processing.
- **Booking only.** No payments for now. A premium tier may come later; then repeat roommate ads are paid by the tenant.
- **No AI and matching service for now.**
- Everything is free at launch.

## 2. Target architecture

| # | Component | Tech | Database | Responsibility | Status |
|---|---|---|---|---|---|
| 1 | API Gateway | Nginx | none | Single entry point, per-IP rate limits, security headers | Done |
| 2 | RabbitMQ | RabbitMQ | none | `aparty.events` topic exchange | Done |
| 3 | IAM Service | FastAPI + Redis | `iam_db` | Telegram login (OIDC), JWT, roles, profiles | Done |
| 4 | Catalog Service | FastAPI | `catalog_db` | Listings, roommate ads, image upload | Done |
| 5 | Order Service | FastAPI | `orders_db` | Booking requests | Done |
| 6 | Notification Service | FastAPI | `notifications_db` | Site bell, Telegram messages, owner notice for roommate ads | Done |
| 7 | Search Service | FastAPI + Meilisearch/Elasticsearch | index | Fast search fed by `listing.*` events | Later (Catalog search in PostgreSQL is enough for now) |

## 3. Plan

### Done
- Gateway, Redis, RabbitMQ, per-service PostgreSQL databases, Docker Compose with all secrets in `.env`.
- IAM: Telegram login, role selection, rotating refresh sessions, rate limits.
- Catalog: listings CRUD, search, image upload, roommate ads, role rules, first RabbitMQ consumer.
- Order: booking requests with overlap and capacity rules, roommate approval by residents.
- Notification: booking and roommate-ad events become site notifications and Telegram messages.
- Frontend talks only to the gateway for auth, listings, bookings and roommate ads.
- Tests for every service against real PostgreSQL, run in CI.

### Next
1. **Transactional outbox** so events are not lost when RabbitMQ is down.
2. **Frontend migration** of the remaining pages that still call removed endpoints: admin panel, favorites, reviews, chat.
3. **Alembic migrations** to replace the development `ALTER TABLE` compatibility code in `init_db`.
4. **Search Service**, when listing volume needs it.

## 4. Strict rules

1. **DB isolation:** no service reads another service's database. Use REST or events.
2. **Contracts first:** agree the Pydantic schema between services before implementing.
3. **English everywhere:** code, comments, database, API payloads, commit messages.
4. **Focused PRs:** every change goes through a PR and merges only when CI is green (see [docs/BRANCH_PROTECTION.md](docs/BRANCH_PROTECTION.md)).
5. **Resilience:** if the Notification Service is down, booking must still work; events wait in the queue.
6. **Tests:** all work must pass its tests. New endpoints and functions update the docs.
