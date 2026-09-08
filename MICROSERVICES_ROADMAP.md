# Aparty: Master Migration & Microservices Roadmap

**Status:** In Progress
**Goal:** Complete transition from a modular monolith to a 100% event-driven microservices architecture. Until the project is completely finished, all development must strictly follow this roadmap.
**Core Principle:** Strict Database Isolation. No two services share the same database. All inter-service communication happens via REST APIs (Sync) or RabbitMQ (Async).

---

## 1. TARGET ARCHITECTURE

The system consists of **7 independent components**. Direct cross-database queries are strictly prohibited. 

### Service Boundaries & Responsibilities (100% Strict):

| # | Service Name | Tech Stack | Database | Core Responsibilities | Events (Pub/Sub) |
|---|---|---|---|---|---|
| **1** | **API Gateway + Redis** | Nginx / Redis | None (Cache only) | Single entry point for all external requests. SSL, CORS, Rate Limiting, ETag, and Cache management. | - |
| **2** | **RabbitMQ Broker** | RabbitMQ | None (Queue) | Async message delivery between services. Uses `aparty.events` topic exchange. | - |
| **3** | **IAM Service** | FastAPI | `iam_db` (PG) | Authentication, JWT, Roles (Owner, Makler, User), OTP, Profile management. | **Pub:** `user.registered`, `user.updated` |
| **4** | **Search Service** | FastAPI | Elastic / Meili | Ultra-fast listing search, filtering (location, price, rooms), typo-tolerance. | **Sub:** `listing.created`, `listing.updated`, `listing.deleted` |
| **5** | **AI & Matching Service**| FastAPI | Vector DB | Roommate matching, smart recommendations, price prediction/analytics. | **Sub:** `user.activity`, `listing.created` |
| **6** | **Notification Service**| FastAPI / Python| SQLite (Log only) | Sends Emails (SMTP), Telegram Bot messages, SMS. *Runs in background only, no REST API.* | **Sub:** `user.registered`, `booking.created`, `media.processed` |
| **7** | **Catalog & Media & Orders**| FastAPI | `catalog_db` (PG) | **Catalog:** Listings CRUD. **Media:** Image/Video upload & crop (FFmpeg). **Orders:** Booking & Payments. | **Pub:** `listing.*`, `media.uploaded`, `booking.*` |

---

## 2. STEP-BY-STEP EXECUTION PLAN

This roadmap must be executed sequentially. Do not proceed to the next phase until the current one is 100% complete and tested.

### Phase 1: Monolith Preparation & Caching System Implementation
*Stabilizing system performance and reducing PostgreSQL load before decoupling.*
- [x] **1.1. Redis Integration:** Connect Redis cache to the FastAPI project.
- [x] **1.2. TTL and Jitter:** Apply TTL to heavy queries (e.g., apartment lists) and add "Jitter" (randomized seconds) to prevent cache stampedes.
- [x] **1.3. ETag Implementation:** Apply ETag mechanism in React/Zustand frontend requests (304 Not Modified).
- [x] **1.4. Eventual Consistency (Daemon):** Cache "Likes" and "Views" first, then save them to PostgreSQL in the background via a sync Daemon.

### Phase 2: Modular Monolith (Internal Module Separation)
*Separating code into strictly bounded domains before splitting them into microservices.*
- [x] **2.1. Folder Architecture:** Split code purely by business logic (users, apartments, orders, media).
- [x] **2.2. Actor, Command, Event Pattern:** Implement CQRS. APIs do not write to the DB directly; they trigger Commands (e.g., `PlaceOrder`), which fire Events.
- [x] **2.3. Database Decoupling:** Remove all Foreign Keys between distinct domain tables. Link records exclusively via UUIDs/IDs.

### Phase 3: Message Queue Integration
*Building the infrastructure for inter-service communication.*
- [x] **3.1. Broker Setup:** Install and run RabbitMQ via Docker Compose.
- [x] **3.2. Pub/Sub Integration (Publisher):** Publish internal events (`listing.created`, `booking.created`) to the RabbitMQ exchange.
- [ ] **3.3. Consumer Connection:** Build and connect the first microservice to consume and act upon these broker messages.

### Phase 4: Extracting the First Safe Microservice (Media Service)
*Extracting a resource-heavy, low-risk component to validate the microservice flow.*
- [ ] **4.1. Create Media Service:** Move video/image uploading, cropping, and ImgBB logic into a standalone Python service.
- [ ] **4.2. Event Listening:** When a user uploads a video/image, publish a `MediaUploaded` event to the broker.
- [ ] **4.3. Background Processing:** The new service consumes the event and runs `EncoderService` (formatting/compression) and `ThumbnailService`.
- [ ] **4.4. Notification Trigger:** Once processing is done, publish a `MediaProcessed` event. The **Notification Service** consumes this and sends an Email.

### Phase 5: Migrating Core Business Processes to Microservices
*Extracting the most critical domains into independent services.*
- [x] **5.1. User Service (IAM):** Fully separate authentication and user data management (`iam-service`, `iam_db`).
- [ ] **5.2. Order & Payment Service:** Extract the rental and booking logic currently sitting inside `catalog-service`. Build an independent service that handles `PlaceOrder`, manages `ReserveItems`, processes payments (Payme/Click), and owns its own DB.

### Phase 6: API Gateway & Frontend Integration
*Ensuring the frontend interacts with a single entry point, completely unaware of the underlying microservices.*
- [x] **6.1. API Gateway Setup:** Create a single entry point using Nginx (`api-gateway`, port 8080).
- [ ] **6.2. Zustand Adaptation (In Progress):** Refactor the React/Zustand frontend to direct 100% of API calls to the Gateway (`http://localhost:8080/api/v1/...`). Direct calls to port 8000 or 8001 are strictly forbidden.

### Phase 7: Advanced Services (Search and AI)
*Elevating the platform to a premium standard.*
- [ ] **7.1. Create Search Service:** Move heavy search and filter queries off PostgreSQL. Consume `listing.*` events from RabbitMQ to update an Elasticsearch/Meilisearch index in real-time.
- [ ] **7.2. Create AI & Matching Service:** Extract `ai_service.py` from the old monolith. Build a dedicated service utilizing a Vector Database to power "Roommate Matching" and intelligent listing recommendations.

---

## 3. PROJECT STRICT RULES (Non-Negotiable)

Any Pull Request (PR) that violates these rules will be rejected immediately.

1. **DB Isolation Rule:** No service is allowed to execute a direct `SELECT` or `JOIN` on another service's database. If Service A needs data from Service B, it must fetch it via REST API (Gateway) or wait for a RabbitMQ Event.
2. **Contracts First:** The JSON payload format (Pydantic Schema) between Frontend and Backend, or between two Microservices, must be explicitly defined and agreed upon before writing any implementation code.
3. **Strict English Convention:** 100% of the codebase variables, functions, database tables, API payloads, comments, and commit messages must be in English.
4. **Git & PR Limits:** A single Commit must not exceed 200 lines of code. Large features must be broken down into smaller, reviewable chunks to facilitate code review and catch bugs early. All changes must go through a Pull Request and merge only when all CI tests are green.
5. **Resilience (Zero Downtime):** If the `Notification Service` crashes, a user clicking "Book Apartment" must not see an error. The system must drop the notification event into the RabbitMQ queue and proceed. The email will be sent automatically once the service is restored.