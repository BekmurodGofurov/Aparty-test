# Aparty Deep Diagnostic Report

Date: 2026-07-11

Scope: React frontend, FastAPI backend, SQLAlchemy/PostgreSQL schema and data-access helpers.

Mode: Read-only diagnostic audit. No application code changes were applied.

## Executive Summary

Aparty has a promising split between route handlers, schemas, models, and frontend services, but several production-blocking risks exist:

- Core listing creation/editing is contract-broken: owner/makler pages submit Uzbek field names while the backend requires English schema fields.
- Authentication has hardcoded secret defaults and a hardcoded OTP that can verify any registered phone.
- Rental acceptance and subscription/listing limits are enforced with non-atomic read-then-write logic, so concurrent requests can oversell rooms or bypass quotas.
- Search and dashboard paths are likely to slow down under real data because the schema lacks indexes for the columns the app filters and sorts on.
- Some UI state consumes raw backend objects as if they were adapted frontend objects, causing blank cards, wrong counts, and broken dashboards.

## End-To-End Data Flow Trace

### Search Flow

1. React search page reads URL params and pushes them into Zustand filters: `client/src/pages/shared/property-search/PropertySearch.jsx:30-38`.
2. Store maps Uzbek filter keys to backend query params: `client/src/store/listingStore.js:35-58`.
3. Store calls `searchListings`: `client/src/store/listingStore.js:106`.
4. API client sends `GET /api/v1/listings/search`: `client/src/services/listingService.js:3-8`.
5. Backend builds SQLAlchemy filters and calls `search_with_cards`: `backend/app/routers/listings.py:175-270`.
6. DB helper performs count plus paged listing query with owner/review joins: `database/operations/select/listings.py:187-236`.
7. Frontend adapts `ListingCard` English fields to Uzbek component fields: `client/src/store/listingStore.js:110-115` and `client/src/utils/adaptListing.js:12-73`.

Main risk: this path is conceptually aligned, but amenity key mismatches and missing DB indexes can cause incorrect filtering and slow queries.

### Listing Create Flow

1. Owner/makler forms keep Uzbek-shaped state: `client/src/pages/owner/OwnerCreate.jsx:99-126`, `client/src/pages/makler/MaklerCreate.jsx:102-129`.
2. Submit forwards that Uzbek payload mostly unchanged: `client/src/pages/owner/OwnerCreate.jsx:236-241`, `client/src/pages/makler/MaklerCreate.jsx:231-236`.
3. Service posts it to `POST /api/v1/listings/`: `client/src/services/listingService.js:91-94`.
4. Backend expects `ListingCreate` with English fields: `backend/app/schemas/listing.py:12-32`.
5. Backend constructs the ORM model from `payload.model_dump()`: `backend/app/routers/listings.py:152-157`.

Main risk: this flow is currently contract-broken. Required backend fields such as `region`, `district`, `rooms_count`, and `price_usd` are not sent by the frontend.

### Rental Request And Acceptance Flow

1. Listing detail posts a booking request: `client/src/pages/shared/listing/Listing.jsx:145-154`.
2. Service calls `POST /api/v1/rentals/requests`: `client/src/services/listingService.js:26-29`.
3. Backend checks listing activity, available spaces, requester active/pending limits, and duplicate pending request: `backend/app/routers/rentals.py:193-207`.
4. Backend inserts `RentalRequest`, optional initial message, notification, commits, and returns expanded payload: `backend/app/routers/rentals.py:209-233`.
5. Owner/makler dashboard accepts/rejects: `client/src/pages/owner/OwnerDashboard.jsx:154-162`, `client/src/pages/makler/MaklerDashboard.jsx:111-116`.
6. Backend acceptance creates `Rental`, decrements listing spaces, accepts request, rejects related pending requests, notifies users, and commits: `backend/app/routers/rentals.py:333-412`.

Main risk: capacity and request status transitions are not protected by row locks or conditional updates.

## Findings By Severity

## 🔴 CRITICAL

### CR-1: Hardcoded Production-Looking Secrets And Database Credentials

Files and lines:
- `backend/app/config.py:16-18`
- `backend/app/config.py:10-14`

Root cause:
`database_url`, `sync_database_url`, and `jwt_secret_key` have hardcoded defaults. The URLs include credentials and the JWT fallback is a static shared secret. Because `BaseSettings` uses `.env` but does not require these values, any missing environment variable silently falls back to committed credentials/secrets.

Impact:
If the repository is shared or deployed without env overrides, attackers can connect to the database or forge JWTs. Existing tokens remain forgeable until the secret is rotated.

Theoretical solution:
Remove secret defaults entirely. Use required settings with no default for DB URLs and JWT secret. Rotate the database password and JWT secret immediately. Add startup validation that fails if secrets are missing, too short, or match known development placeholders.

### CR-2: Hardcoded OTP Verifies Any Registered Phone

Files and lines:
- `backend/app/utils/security.py:26-32`
- `backend/app/routers/auth.py:133-148`

Root cause:
`verify_otp_code` accepts the global development code `000000` for every phone. The verify endpoint then marks the user verified and issues access/refresh tokens.

Impact:
Anyone who knows or guesses a registered phone number can verify that account with `000000` and receive valid tokens. This is an account-takeover path.

Theoretical solution:
Replace the hardcoded OTP with a server-side OTP store, preferably Redis, storing hashed OTPs keyed by phone/session with TTL, attempt counters, resend throttling, and single-use invalidation. Disable OTP routes in production unless the SMS/TOTP provider is configured.

### CR-3: Owner/Makler Listing Create Payload Does Not Match Backend Schema

Files and lines:
- `client/src/pages/owner/OwnerCreate.jsx:99-126`
- `client/src/pages/owner/OwnerCreate.jsx:236-241`
- `client/src/pages/makler/MaklerCreate.jsx:102-129`
- `client/src/pages/makler/MaklerCreate.jsx:231-236`
- `client/src/services/listingService.js:91-94`
- `backend/app/schemas/listing.py:12-32`
- `backend/app/routers/listings.py:141-157`

Root cause:
The frontend submits Uzbek field names such as `viloyat`, `tuman`, `narx_usd`, `rasmlar`, `jins`, `qulayliklar`, `max_kishi`, and `bosh_joy`. The backend `ListingCreate` requires English keys such as `region`, `district`, `price_usd`, `images`, `target_gender`, `amenities`, `max_guests`, and `available_spaces`.

Impact:
Listing creation from owner and makler flows should fail validation with 422, blocking a core marketplace workflow.

Theoretical solution:
Add a single request adapter before `createListing`/`updateListing`, or make the service layer own translation from UI model to API model. Keep the backend schema English and type-safe, but require the frontend service to send exactly the backend contract.

### CR-4: Listing Edit Payload Also Uses Wrong Field Names And Can Silently No-Op

Files and lines:
- `client/src/pages/owner/OwnerEdit.jsx:94-114`
- `client/src/pages/owner/OwnerEdit.jsx:237-242`
- `client/src/services/listingService.js:96-99`
- `backend/app/schemas/listing.py:41-60`
- `backend/app/routers/listings.py:348-361`

Root cause:
Edit form normalizes fetched backend data into Uzbek state, but submits the Uzbek state back to `PUT /listings/{id}`. `ListingUpdate` only defines English fields. Pydantic's default behavior ignores unknown extras, so many submitted fields may be discarded instead of causing an obvious error.

Impact:
Users can see a successful save path while key edits do not persist. This creates frontend/backend state mismatch and data-loss perception.

Theoretical solution:
Use a bidirectional adapter: API response -> UI form state for rendering, and UI form state -> API update payload for saving. Configure update schemas with `extra="forbid"` in development/testing to expose contract drift early.

### CR-5: Concurrent Rental Acceptance Can Oversell Available Spaces

Files and lines:
- `backend/app/routers/rentals.py:333-353`
- `database/operations/update/listings.py:77-81`
- `database/operations/insert/rentals.py:13-16`
- `database/alembic/versions/0001_initial_schema.py:72-103`
- `database/alembic/versions/0001_initial_schema.py:176-192`

Root cause:
Acceptance reads a request and listing, checks `available_spaces`, creates a rental, then decrements `listing.available_spaces` in Python. There is no `SELECT ... FOR UPDATE`, no conditional `UPDATE listings SET available_spaces = available_spaces - 1 WHERE available_spaces > 0`, no exclusion/unique constraint, and no transaction isolation guard specific to room capacity.

Impact:
Two owners/admin actions or duplicated browser submissions can accept requests concurrently and create more active rentals than the listing capacity.

Theoretical solution:
Wrap acceptance in a transaction that locks the listing row and request row. Use a conditional atomic update for capacity and verify exactly one row was affected. Add database constraints/checks for `available_spaces >= 0`, and consider an invariant table or unique partial index for active occupancy where appropriate.

### CR-6: Subscription Listing Limits Are Race-Prone And Can Be Bypassed

Files and lines:
- `backend/app/routers/listings.py:98-123`
- `backend/app/routers/listings.py:126-136`
- `backend/app/routers/listings.py:150-172`
- `database/operations/select/subscriptions.py:38-49`
- `database/operations/update/subscriptions.py:21-28`

Root cause:
Limit enforcement counts active simple/premium listings and separately increments subscription usage. The subscription increment commits independently before the listing/payment commit completes. There is no atomic `used_count < listing_limit` update and no row-level lock.

Impact:
Concurrent listing creation can exceed simple/premium limits. Failed listing creation after subscription increment can also consume quota without producing a listing.

Theoretical solution:
Make listing creation, subscription consumption, and payment creation one transaction. Use `UPDATE subscriptions SET used_count = used_count + 1 WHERE id = :id AND used_count < listing_limit RETURNING *`, or lock the subscription row with `FOR UPDATE`.

### CR-7: Public User Lookup Exposes User Profiles Without Authentication

Files and lines:
- `backend/app/routers/users.py:23-29`
- `backend/app/schemas/user.py:12-21`

Root cause:
`GET /api/v1/users/{user_id}` has no `get_current_user` dependency. It returns `UserOut`, including phone, role, email if present, university, verification state, and profile image.

Impact:
Any client with a UUID can enumerate or dereference user profile data. This is a privacy and scraping risk, especially because owner/student phone numbers are sensitive.

Theoretical solution:
Require authentication for direct user lookups. Return a public minimal profile for listing/contact contexts, and reserve full `UserOut` for self/admin access.

### CR-8: Upload Endpoint Allows SVG And Writes Files Synchronously Inside Async Route

Files and lines:
- `backend/app/routers/upload.py:13-14`
- `backend/app/routers/upload.py:16-33`

Root cause:
The upload allowlist includes `svg`/`image/svg+xml`. The route trusts extension/content-type and writes with `open()` plus `shutil.copyfileobj()` inside an `async def` route without size limits or content sniffing.

Impact:
Stored SVG can carry script or external references if rendered directly by browsers. Large uploads can block the event loop and exhaust disk/memory resources. Content-type can be spoofed.

Theoretical solution:
Disallow SVG unless sanitized and served with restrictive headers. Validate actual image bytes, enforce max file size, store outside the app working directory or object storage, and use async file handling or thread offload.

## 🟠 HIGH

### HI-1: Payment Authorization Lets Any Makler Mutate Any Payment

Files and lines:
- `backend/app/routers/payments.py:71-86`
- `backend/app/routers/payments.py:89-110`
- `backend/app/routers/payments.py:113-125`

Root cause:
Payment status/edit/delete routes allow roles `admin` and `makler`, but do not verify the makler owns the listing/rental/payment relationship.

Impact:
One broker can modify or delete another user's rental payments if they know the payment UUID.

Theoretical solution:
For makler access, join payment -> rental -> listing and require `listing.owner_id == current_user.id`. Keep unrestricted mutation for admins only.

### HI-2: Manual Rental Creation Does Not Check Listing Activity Or Capacity

Files and lines:
- `backend/app/routers/rentals.py:168-184`
- `database/operations/update/listings.py:77-81`

Root cause:
`POST /rentals/` only verifies `student_id` ownership/admin and that the listing exists. It does not reject inactive listings or zero-capacity listings before creating a rental.

Impact:
Authenticated users can create rentals directly for unavailable listings, and admins can accidentally create inconsistent occupancy records.

Theoretical solution:
Apply the same listing availability and capacity rules as request acceptance. Prefer a single rental-creation service that enforces invariants in one transaction.

### HI-3: Subscription Purchase Endpoint Lets Users Mint Arbitrary Subscription Limits

Files and lines:
- `backend/app/routers/subscriptions.py:27-34`
- `backend/app/schemas/subscription.py:11-15`

Root cause:
`POST /subscriptions/purchase` accepts `type`, `start_date`, `end_date`, and `listing_limit` directly from the client. It creates an active subscription without payment verification or role restriction.

Impact:
Any authenticated user can grant themselves arbitrary listing quota and dates.

Theoretical solution:
Remove or admin-gate the generic purchase endpoint. Only allow server-defined plan IDs with verified payment state, and restrict makler-only plans to makler users.

### HI-4: Listing Activation And Premium Upgrade Create Pending Payments But Activate Immediately

Files and lines:
- `backend/app/routers/listings.py:393-417`
- `backend/app/routers/listings.py:420-445`
- `backend/app/models/listing_payment.py:27-33`

Root cause:
`activate-basic` and `upgrade-to-premium` set listing visibility/premium first and create a `ListingPayment` with status `pending`. There is no payment confirmation or rollback gate.

Impact:
Users can activate paid promotions without actually paying.

Theoretical solution:
Create pending payment first, redirect/confirm payment externally, then activate listing only from a payment webhook or admin-confirmed payment transition.

### HI-5: Frontend Dashboard Consumes Raw Listing API Objects As Adapted Objects

Files and lines:
- `client/src/services/listingService.js:16-19`
- `client/src/pages/owner/OwnerDashboard.jsx:84-93`
- `client/src/pages/owner/OwnerDashboard.jsx:118-127`
- `client/src/pages/owner/OwnerDashboard.jsx:284-303`
- `client/src/pages/makler/MaklerDashboard.jsx:69-78`
- `client/src/pages/makler/MaklerDashboard.jsx:94-105`

Root cause:
`getMyListings` returns backend `ListingCard` fields (`is_active`, `is_premium`, `price_usd`, `images`, etc.) but dashboards read Uzbek fields (`faol`, `premium`, `narx_usd`, `rasmlar`, etc.) without calling `adaptListing`.

Impact:
Dashboard counts, active/inactive status, prices, image thumbnails, and listing titles can render incorrectly even when backend data is correct.

Theoretical solution:
Normalize all listing responses at the service boundary. Either make `getMyListings` return adapted listings or update dashboards to use English backend fields consistently.

### HI-6: Owner Dashboard Expects `tenant`, Backend Returns `student`

Files and lines:
- `backend/app/routers/rentals.py:442-476`
- `backend/app/schemas/rental.py:52-63`
- `client/src/pages/owner/OwnerDashboard.jsx:309-313`
- `client/src/pages/owner/OwnerDashboard.jsx:448-463`

Root cause:
The backend owner rental payload uses the `student` object per `OwnerRentalOut`, but the frontend reads `activeRental.tenant` and `rental.tenant`.

Impact:
Owner dashboard can crash or fail to render active rentals when it accesses `tenant.full_name` on undefined.

Theoretical solution:
Update the frontend contract to use `student`, or adapt owner-rental responses to the UI's `tenant` shape in the service layer.

### HI-7: AI Roommate Search References Nonexistent ORM Field

Files and lines:
- `backend/app/services/ai_service.py:334-339`
- `backend/app/services/ai_service.py:362-376`
- `backend/app/models/listing.py:46-47`

Root cause:
AI search uses `Listing.max_occupants` and `l.max_occupants`, but the model defines `max_guests`.

Impact:
Roommate/bo'sh joy AI searches can throw an AttributeError and return a 500 through `backend/app/routers/ai.py:56-57`.

Theoretical solution:
Replace `max_occupants` references with `max_guests`, and add tests for `roommate=True` direct and tool-call paths.

### HI-8: Startup Auto-Migration Can Generate Migration Files In Production

Files and lines:
- `backend/app/main.py:15-21`
- `backend/app/db_migrations.py:56-80`
- `backend/app/config.py:23`

Root cause:
Application startup runs migrations, compares metadata, autogenerates a revision file if drift exists, then upgrades. `auto_migrate_on_startup` defaults to true.

Impact:
Production app instances can attempt schema writes and filesystem writes during startup. Multiple replicas can race on migration generation or schema mutation.

Theoretical solution:
Disable autogeneration in runtime. Run migrations as an explicit deployment step. Keep startup limited to health checks and fail-fast schema version verification.

### HI-9: JWT Refresh Tokens Are Stateless And Not Revocable

Files and lines:
- `backend/app/routers/auth.py:22-30`
- `backend/app/routers/auth.py:109-130`
- `backend/app/routers/auth.py:151-155`
- `backend/app/utils/security.py:20-23`

Root cause:
Refresh tokens are JWTs with only `sub`, `iat`, and `exp`. Logout deletes the browser cookie but does not revoke the server-side token. Refresh also does not verify token type, user existence, or session state.

Impact:
Stolen refresh tokens remain valid until expiration. Access tokens can be refreshed for deleted or disabled users if the subject is still accepted.

Theoretical solution:
Add `typ="refresh"` and `jti` claims, store refresh sessions server-side, rotate refresh tokens on use, revoke on logout, and validate the current user on refresh.

### HI-10: Admin Login Is Hidden Only By URL Parameter

Files and lines:
- `client/src/pages/shared/auth/LoginPage.jsx:22-32`
- `backend/app/routers/auth.py:86-106`

Root cause:
Admin login is exposed at `/api/v1/auth/admin-login`; the UI merely toggles it with `?admin=true`. There is no extra protection such as IP allowlist, MFA, or rate limiting.

Impact:
Brute-force and credential stuffing pressure focuses on a known endpoint.

Theoretical solution:
Add rate limiting, admin MFA, audit logging, and possibly network restrictions for admin login. Keep the non-admin login path incapable of admin authentication as it already does.

## 🟡 MEDIUM

### ME-1: Missing Search And Join Indexes For Core Query Paths

Files and lines:
- `database/alembic/versions/0001_initial_schema.py:72-103`
- `database/alembic/versions/0001_initial_schema.py:104-160`
- `database/alembic/versions/0001_initial_schema.py:176-269`
- `database/operations/select/listings.py:215-235`
- `database/operations/select/rentals.py:145-174`

Root cause:
The initial migration only creates indexes for `users.phone` and `notifications.user_id`. Listing search filters and sorts by `is_active`, `region`, `district`, `price_usd`, `target_gender`, `rooms_count`, `available_spaces`, `is_premium`, `premium_expires_at`, and `created_at`, but those columns lack indexes. Rental request inbox/conversation filters by requester/recipient/status without indexes.

Impact:
As listings and messages grow, search pages, dashboards, and conversations will degrade into sequential scans and expensive sorts.

Theoretical solution:
Add composite indexes around actual query shapes, e.g. active listings by region/district/price/created_at, owner listings by owner/created_at, rental requests by requester/status/created_at and recipient/status/created_at, payments by payer/status, reviews by listing/created_at. Add GIN or expression indexes for JSONB amenities if filtering remains JSONB-based.

### ME-2: Search Endpoint Has No Server-Side Cache Despite Expensive Aggregates

Files and lines:
- `backend/app/routers/listings.py:175-270`
- `database/operations/select/listings.py:195-236`
- `client/src/services/cacheService.js:8-25`

Root cause:
Search performs a count subquery plus review aggregation and sorting per request. The only cache is browser-local and does not prevent backend load across users.

Impact:
Popular feeds and repeated filter combinations can become DB hot spots.

Theoretical solution:
Introduce Redis or materialized/cache layer for listing feed/search responses with short TTL and invalidation on listing/review changes. Consider denormalized listing rating/review counts.

### ME-3: Client Cache Does Not Actually Short-Circuit Successful GET Requests

Files and lines:
- `client/src/services/api.js:38-60`
- `client/src/services/api.js:108-118`
- `client/src/services/cacheService.js:69-87`

Root cause:
The request interceptor attaches `_useCache` and `_cachedData` but still returns the config, so Axios sends the network request. Cached data is only returned in the error interceptor.

Impact:
The cache does not reduce normal backend latency or load. It only provides offline/error fallback.

Theoretical solution:
Use an adapter/interceptor that resolves cached responses before dispatch, or move caching into explicit service calls. Keep stale-on-error behavior as a separate feature.

### ME-4: Amenity Key Mismatch Between Frontend And Backend

Files and lines:
- `client/src/store/listingStore.js:16-25`
- `client/src/store/listingStore.js:95-104`
- `backend/app/routers/listings.py:226-241`
- `client/src/pages/owner/OwnerCreate.jsx:46-55`

Root cause:
Frontend uses keys like `gaz`, `suv`, `konditsioner`, `kir_mashina`, `holodilnik`, and `oshxona_jihozi`. Backend search expects params and JSON keys like `gas`, `water`, `ac`, `washing_machine`, `refrigerator`, and `kitchen_appliances`.

Impact:
Amenity filters can be ignored by FastAPI because unknown query params do not map to endpoint parameters. Created listings can store amenities under keys that search never checks.

Theoretical solution:
Define one canonical amenity enum/map and use it for form state, listing storage, search params, and display. Add contract tests for every amenity filter.

### ME-5: Public AI Endpoint Has No Authentication, Rate Limit, Or Abuse Control

Files and lines:
- `backend/app/routers/ai.py:31-57`
- `backend/app/services/ai_service.py:481-489`
- `backend/app/services/ai_service.py:537-543`
- `backend/app/services/ai_service.py:602-606`

Root cause:
`POST /api/v1/ai/chat` does not depend on `get_current_user` and can call an external LLM twice for one request.

Impact:
Anonymous traffic can burn Groq quota and increase backend latency/cost.

Theoretical solution:
Require authentication or strict anonymous rate limits, cache deterministic direct-search responses, and add per-IP/per-user throttling.

### ME-6: Uploads Lack Size Limit And Durable Storage Strategy

Files and lines:
- `backend/app/routers/upload.py:11-33`
- `backend/app/main.py:30-32`

Root cause:
Files are stored under local `uploads` and served directly by FastAPI static files. No max size, image dimension validation, malware scanning, or object-store lifecycle exists.

Impact:
Local disk can fill, deployments can lose uploaded files, and images are not optimized for frontend delivery.

Theoretical solution:
Use object storage with signed upload URLs or backend streaming. Enforce size/type/dimension limits and generate optimized variants/thumbnails.

### ME-7: Frontend Stores Access Tokens In `localStorage`

Files and lines:
- `client/src/store/authStore.js:4-14`
- `client/src/services/api.js:40-43`
- `client/src/services/api.js:131-147`

Root cause:
The access token is persisted in `localStorage` and manually attached as a Bearer token.

Impact:
Any XSS in the app can steal access tokens. React escapes text by default, but user-generated image URLs/SVGs and future HTML rendering could raise XSS risk.

Theoretical solution:
Prefer short-lived access tokens in memory and refresh via HttpOnly cookie, or fully HttpOnly cookie auth with CSRF protection. Add CSP headers.

### ME-8: CORS Allows Credentials Across Multiple Origins

Files and lines:
- `backend/app/main.py:34-40`
- `backend/app/config.py:26-39`

Root cause:
CORS allows credentials and all methods/headers for every configured origin, including local dev hosts and a pages.dev domain.

Impact:
If any allowed origin is compromised, it can make credentialed requests from a browser.

Theoretical solution:
Use separate environment-specific CORS allowlists, remove dev origins from production, and restrict methods/headers where practical.

### ME-9: Frontend Payment Edit Payload Does Not Match Backend Payment Schema

Files and lines:
- `client/src/pages/makler/MaklerPayments.jsx:67`
- `client/src/pages/makler/MaklerPayments.jsx:92-104`
- `client/src/pages/makler/MaklerPayments.jsx:215-223`
- `backend/app/schemas/payment.py:23-27`

Root cause:
Frontend form uses `month`, while backend `PaymentUpdate` requires `billing_month`. It also initializes from `payment.month`, while backend output uses `billing_month`.

Impact:
Payment edit likely fails with 422 or saves stale data.

Theoretical solution:
Rename frontend fields to `billing_month` at the service boundary and render from backend `billing_month`.

### ME-10: N+1 Query Pattern In Rental Request Payload Expansion

Files and lines:
- `backend/app/routers/rentals.py:110-125`
- `backend/app/routers/rentals.py:236-260`
- `backend/app/routers/rentals.py:245-251`
- `database/operations/select/rentals.py:145-174`

Root cause:
Each rental request payload independently fetches listing, requester, and recipient. Conversations also fetch messages per request.

Impact:
Inbox/conversation pages scale as 1 + 3N or worse. With many requests, dashboards become latency-heavy.

Theoretical solution:
Use joined/selectin loads or explicit join queries returning request, listing, requester, recipient, and latest messages in batches.

### ME-11: User Profile Update Allows Phone Change Without Uniqueness Precheck Or Reverification

Files and lines:
- `backend/app/routers/users.py:32-53`
- `backend/app/schemas/user.py:26-34`
- `backend/app/models/user.py:26`

Root cause:
`UserUpdate` permits `phone`, and `update_current_user` applies it without checking duplicates or setting `is_verified=False`.

Impact:
Duplicate phone updates will raise database errors; successful phone changes preserve old verification state.

Theoretical solution:
Require OTP reverification for phone changes, precheck uniqueness, and return controlled 409/400 errors.

### ME-12: Global SQLAlchemy Error Handler Hides Root Cause But Does Not Roll Back Sessions

Files and lines:
- `backend/app/main.py:51-56`
- `backend/app/database.py:30-33`

Root cause:
The global SQLAlchemy handler returns a generic 503. `get_db` simply yields the session and does not explicitly roll back on exceptions.

Impact:
Failed writes can leave sessions in failed transaction state until context close. Clients cannot distinguish validation/constraint bugs from actual outage.

Theoretical solution:
Wrap `yield` in try/except with rollback. Convert known integrity errors into 409/400 at route/service level before falling back to 503.

## 🔵 LOW

### LO-1: Debug Prints May Leak User Prompts And AI Arguments

Files and lines:
- `backend/app/services/ai_service.py:468`
- `backend/app/services/ai_service.py:491-493`
- `backend/app/services/ai_service.py:534`
- `backend/app/services/ai_service.py:557`

Root cause:
The AI service logs raw user messages, arguments, and exception text with `print`.

Impact:
Sensitive user search prompts or internal errors can appear in logs.

Theoretical solution:
Use structured logging with redaction and appropriate log levels.

### LO-2: Listing View Count Helper Is Unused

Files and lines:
- `database/operations/update/listings.py:60-67`
- `backend/app/routers/listings.py:285-331`

Root cause:
The helper increments `views_count`, but `get_listing` does not call it.

Impact:
View counts shown in cards/details remain stale or dependent on external processes.

Theoretical solution:
Increment views in a controlled analytics path, with throttling/deduplication to avoid inflating counts.

### LO-3: Some Frontend Images Are Not Lazy-Loaded Or Decoded Async

Files and lines:
- `client/src/pages/shared/listing/Listing.jsx:214-224`
- `client/src/pages/shared/listing/Listing.jsx:277-287`
- `client/src/pages/owner/OwnerCreate.jsx:304-307`
- `client/src/pages/makler/MaklerCreate.jsx:299-302`

Root cause:
High-impact listing/detail and upload-preview images often omit `loading="lazy"` and `decoding="async"`; detail hero also uses both CSS background and an image for the active source.

Impact:
Image-heavy pages may increase LCP, memory, and bandwidth.

Theoretical solution:
Use optimized image variants, lazy loading for thumbnails/below-fold images, and set explicit dimensions/aspect ratios.

### LO-4: Profile Verification Display Uses Nonexistent `verified` Alias

Files and lines:
- `client/src/services/userService.js:3-11`
- `client/src/pages/owner/OwnerDashboard.jsx:222-225`
- `client/src/pages/makler/MaklerDashboard.jsx:190-193`

Root cause:
`normalizeUser` keeps `is_verified` but does not add `verified`. Dashboards read `owner?.verified` and `broker?.verified`.

Impact:
Verified users may display as unverified.

Theoretical solution:
Add a `verified: user.verified ?? user.is_verified` alias in the user normalizer or update components to use `is_verified`.

### LO-5: `RoleRoute` Trusts Local Role For Navigation

Files and lines:
- `client/src/components/RoleRoute/RoleRoute.jsx:4-18`
- `client/src/store/authStore.js:4-14`

Root cause:
Route protection is based on role stored in `localStorage`.

Impact:
This is not a backend authorization bypass because protected endpoints check JWT-derived roles, but users can spoof the frontend role and see admin/owner UI shells until API calls fail.

Theoretical solution:
Hydrate role from `/users/me` after token validation and treat local route guards as UX only.

## Security Notes

- SQL injection risk appears low in inspected ORM query paths because filters are composed through SQLAlchemy expressions rather than raw SQL.
- XSS risk is currently moderated by React escaping text. The largest XSS-adjacent risk is allowing uploaded SVG and using user-controlled image URLs.
- RBAC exists in backend route dependencies, but several resource-ownership checks are missing or too broad, especially payments and public user lookup.
- No rate limiting was observed for login, OTP, refresh, upload, or AI endpoints.

## Performance And Caching Notes

- The backend should prioritize indexing search/listing/request/payment tables before large data ingestion.
- Redis or another server-side cache would be most valuable for listing feeds, search filter results, notification counts, and AI direct search responses.
- The frontend cache needs a real preflight return path to reduce backend traffic.
- Dashboard and message endpoints need batched query patterns to avoid N+1 growth.

## Recommended Remediation Order

1. Rotate secrets and remove hardcoded credentials/JWT defaults.
2. Disable hardcoded OTP in any non-local environment.
3. Fix frontend listing create/update adapters and dashboard response adapters.
4. Add transactional row locks/atomic updates for rental acceptance and subscription usage.
5. Lock down payment mutation ownership and subscription purchase rules.
6. Add production-safe migration workflow and DB indexes for search/inbox/payment paths.
7. Harden uploads, CORS, token storage/refresh, and rate limiting.
8. Add end-to-end contract tests for owner create, makler create, edit listing, rental acceptance, payment edit, and AI roommate search.
