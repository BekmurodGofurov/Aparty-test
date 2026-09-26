# Microservices

All client traffic enters through the Nginx API gateway (`http://localhost:8080`). Services talk to each other over REST or RabbitMQ events. Each service owns its PostgreSQL database and never reads another service's database.

| Service | Port | Database | Purpose |
|---|---|---|---|
| api-gateway | 8080 (public) | none | Routes `/api/v1/*` to the services below |
| iam-service | 8000 | `iam_db` | Telegram login, JWT, user profiles |
| catalog-service | 8001 | `catalog_db` | Listings and image uploads |
| order-service | 8002 | `orders_db` | Booking requests (no payments) |

Infrastructure: PostgreSQL, Redis (login state, refresh sessions, rate limits; password protected), RabbitMQ (`aparty.events` topic exchange). Their host ports are bound to `127.0.0.1` only.

## Gateway routes

| Path prefix | Service |
|---|---|
| `/api/v1/auth/`, `/api/v1/users/` | iam-service |
| `/api/v1/listings`, `/api/v1/media/` | catalog-service |
| `/api/v1/bookings` | order-service |

`/api/v1/users/public` is internal: the gateway answers 404 for it.

The gateway limits every client IP to 20 requests per second (burst 40) and `/api/v1/auth/` to 10 per minute (burst 10), answering 429. It also adds `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy` and `Permissions-Policy` headers.

## Authentication

### Login flow

Users sign in with the official "Log in with Telegram" (OpenID Connect, authorization code with PKCE). There is no password and no code to copy.

1. The frontend calls `GET /api/v1/auth/telegram/start`. IAM creates a random `state` and a PKCE verifier, keeps them in Redis for 10 minutes, sets an httpOnly `tg_login_state` cookie and returns `authorization_url`.
2. The browser opens that URL. The user enters their phone number in Telegram's page and approves in the Telegram app.
3. Telegram redirects to the frontend page `/auth/telegram/callback?code=...&state=...`, which calls `POST /api/v1/auth/telegram/callback` with `code` and `state`.
4. IAM checks that `state` matches the cookie (same browser) and is unused, exchanges the code with the client secret, verifies the `id_token` signature against Telegram's public keys (`iss`, `aud`, `exp`, RS256/ES256 only) and requires a verified phone number.
5. First login creates the user with the Telegram id as primary key, the name, phone and picture from Telegram, and no role. Later logins keep the profile the user edited and refresh the phone number.
6. IAM returns an access token and sets the refresh cookie. `needs_role: true` tells the frontend to show the role picker, which calls `PUT /api/v1/users/me/role` once and receives a new access token that carries the role.

Telegram login is unavailable (503) until `TELEGRAM_CLIENT_ID`, `TELEGRAM_CLIENT_SECRET` and `TELEGRAM_REDIRECT_URI` are set. Register the bot's Web Login and the redirect URL in @BotFather to get them.

### Tokens

- Access token: JWT, 15 minutes, claims `sub`, `role` (null until chosen), `iss`, `aud`, `exp`, `iat`, `jti`, `type: access`. Catalog and Order validate signature, issuer, audience and expiry with the shared `JWT_SECRET_KEY`.
- Refresh token: random opaque value in an httpOnly cookie, stored hashed in Redis. Each refresh replaces it (rotation), a used token stops working, and logout revokes it. It is never accepted in a request body.
- Send `Authorization: Bearer <access token>` to every service.

### Roles

Roles are `student`, `owner`, `makler` (chosen once) and `admin` (root account from `ADMIN_USERNAME` / `ADMIN_PASSWORD`, which cannot use Catalog or Order).

| Action | Allowed roles |
|---|---|
| Create a listing | owner, makler. The listing `source` follows the role and cannot be set by the client |
| Post a roommate ad | student or makler, for an apartment they live in (see Roommates) |
| Upload an image | any chosen role |
| Create a booking | any chosen role |
| Edit, delete or manage a listing | its creator |
| View or change a booking | requester and listing owner, within the status rules below |

A user who has not chosen a role gets 403 on these actions.

### Abuse protection

- `GET /auth/telegram/start` and `POST /auth/telegram/callback`: 10 requests per minute per IP (429).
- `POST /auth/admin-login`: 5 failed attempts per IP and username lock it for 15 minutes (429).

## IAM Service

| Method | Path | Notes |
|---|---|---|
| GET | `/api/v1/auth/telegram/start` | Returns `authorization_url` |
| POST | `/api/v1/auth/telegram/callback` | Body: `code`, `state`. Returns `access_token`, `needs_role`, `user` |
| POST | `/api/v1/auth/admin-login` | Root admin from `ADMIN_USERNAME` / `ADMIN_PASSWORD` |
| POST | `/api/v1/auth/refresh` | Rotates the refresh cookie, returns a new access token |
| POST | `/api/v1/auth/logout` | Revokes the refresh token and clears the cookie |
| GET / PUT | `/api/v1/users/me` | Current profile. Editable: name, university, picture. The phone number comes from Telegram and cannot be changed |
| PUT | `/api/v1/users/me/role` | Body: `role` (`student`, `owner` or `makler`). Only once. Returns a new access token |
| GET | `/api/v1/users/{id}` | Own profile, or any profile for admin |
| GET | `/api/v1/users/public?ids=1,2` | Internal. Up to 100 ids. Returns `id`, `full_name`, `phone`, `is_verified` |

## Catalog Service

| Method | Path | Notes |
|---|---|---|
| POST | `/api/v1/listings` | Create (owner or makler) |
| GET | `/api/v1/listings/search` | Filters: region, district, target_gender, rental_type, owner_role, price_min/max, rooms_count, available_spaces, wifi, air_conditioner, washing_machine, kitchen, move_in_ready; `page`, `limit` (max 100) |
| GET | `/api/v1/listings/me` | Own listings |
| GET | `/api/v1/listings/{id}` | Detail, counts a view |
| GET | `/api/v1/listings/{id}/booking-info` | Internal, used by order-service. Does not count a view |
| PUT / PATCH | `/api/v1/listings/{id}` | Owner only |
| DELETE | `/api/v1/listings/{id}` | Soft delete, owner only |
| POST | `/api/v1/listings/{apartment_id}/roommate` | A tenant looks for roommates. See "Roommates" |
| POST | `/api/v1/listings/{id}/mark-occupied`, `mark-available`, `activate-basic` | Owner only |
| POST | `/api/v1/media/upload`, `/api/v1/media/image` | Image upload to ImgBB (any chosen role). jpg, jpeg, png, webp, up to `MAX_UPLOAD_SIZE_BYTES` |

Owner name, phone and verified flag are fetched from IAM (`/users/public`). If IAM is unavailable the listing is still served with empty owner details.

Events published: `listing.created`, `listing.updated` (also sent for deletes, with `status: deleted`).

Events consumed: `booking.updated` (queue `catalog-service.booking-events`). It marks a roommate ad occupied when its places are filled and reopens it when one frees up.

## Order Service

| Method | Path | Notes |
|---|---|---|
| POST | `/api/v1/bookings` | Body: `listing_id`, `start_date`, `end_date`, `message`. Price is nights × listing price |
| GET | `/api/v1/bookings` | Bookings requested by the current user |
| GET | `/api/v1/bookings/incoming` | Requests the user can answer: for their own listings, and roommate requests for apartments they live in. Includes `requester` (name, phone from IAM) and `listing_title`. Optional `listing_id` |
| GET | `/api/v1/bookings/{id}` | Requester or listing owner only |
| PATCH | `/api/v1/bookings/{id}/status` | Body: `status` |

Rules:

- Dates must be in the future and `end_date` after `start_date`. The end date is the check-out day, so back-to-back bookings are allowed.
- Overlapping `pending` or `confirmed` bookings return 409. Concurrent requests are serialized per listing with a PostgreSQL advisory lock.
- A whole unit accepts one booking per date range. A shared room or roommate listing accepts as many overlapping bookings as it offers places (`available_spaces`). A person cannot hold two overlapping bookings of the same listing (409).
- The owner cannot book their own listing (400). Unknown, inactive or non-active listings return 404. If Catalog is down, creation returns 503.
- Status changes: the owner can move `pending` to `confirmed`, `rejected` or `cancelled`, and `confirmed` to `cancelled`. The requester can move `pending` or `confirmed` to `cancelled`. Anything else returns 409.

Events published: `booking.created`, `booking.updated`. Both carry `apartment_listing_id` and `is_roommate_request`.

## Roommates

Tenants who rent an apartment can look for people to share it with. This works even when the tenants did not rent through the platform, so no booking is needed and nobody has to give permission.

1. A logged-in tenant (role `student` or `makler`, never the apartment's owner) opens an apartment listing and posts an ad with `POST /api/v1/listings/{apartment_id}/roommate`.
2. The ad states who lives there now (`residents_male`, `residents_female`, `residents_children`), how many people can come (`available_spaces`, 1 to 10), who is wanted (`target_gender`: male, female or mixed), the first day a newcomer can move in (`available_from`, empty means anytime, the tenants are waiting), the price per person, and an optional description.
3. Address, coordinates, rooms, amenities and photos are copied from the apartment and cannot be edited. The ad has `source: roommate`, `rental_type: shared_room` and `parent_listing_id` pointing to the apartment. The poster's name and phone come from IAM, so newcomers can call the tenants directly (not the owner).
4. The ad is valid for 30 days (`ROOMMATE_LISTING_DAYS`), then stops showing in search and cannot be booked. The first ad is free; a paid tier for repeat ads may come later, charged to the tenant.
5. One active ad per apartment: the tenants post it once. Closing (deleting) or expiry lets them post a new one. An ad marked occupied still counts until closed.
6. Newcomers can also request a booking of the ad. The request goes to the poster **and to everyone who currently lives in the apartment on the platform** (confirmed, not yet ended bookings of the apartment, including roommates accepted earlier). Any one of them accepts or declines a pending request; only the poster can cancel an accepted roommate.
7. When confirmed roommate bookings fill the offered places, Catalog (consuming `booking.updated`, which carries `listing_confirmed_count`) marks the ad occupied and hides it from search. If a place frees up it reopens, unless the poster closed it by hand.
8. Deleting the apartment closes its ads.

The `listing.created` event of an ad carries `source: roommate`, `parent_listing_id` and `apartment_owner_id`. Notifying the apartment's owner ("your tenants are looking for N more people") is planned for the Notification service.

Roommate ads are found with `owner_role=student`. A roommate booking never conflicts with the tenant's own booking of the apartment.

## Configuration

Docker: copy `.env.example` to `.env` in the repo root and fill in every value. `docker compose` fails if a required variable is missing. The Telegram values are optional at start-up, but login stays disabled until they are set.

The frontend needs `VITE_BACKEND_API` (the gateway URL). The redirect URI registered in @BotFather must be the frontend callback page, for example `https://<domain>/auth/telegram/callback`.

Running a service outside Docker: copy that service's `.env.example` to `.env`.

## Tests

Tests use a real PostgreSQL database whose name ends with `_test`. The suite refuses to run otherwise, because it drops and recreates the tables. Redis and Telegram are replaced with in-memory and mocked fakes, so no external service is needed.

```bash
cd microservices/services/<service>
pip install -r requirements-dev.txt
TEST_DATABASE_URL=postgresql+asyncpg://<user>@localhost:5432/<service>_test pytest
```

CI runs each service's suite against its own PostgreSQL database.

The Telegram bot has its own small suite: `cd bot && pip install -r requirements-dev.txt && pytest`. The bot only greets users and links to the website; login and registration happen on the site.
