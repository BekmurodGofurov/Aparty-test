---
name: aparty-rules
description: Aparty project rules and scope. Use for any work in this repo - writing code, adding services, DB changes, tests, commits or PRs.
---

# Aparty project rules

## Scope (current MVP)
- Services: IAM, Catalog, Orders (booking only), Notification, Search, plus Nginx gateway, Redis, RabbitMQ.
- **Images only.** No video upload or processing.
- **Booking only.** No payments (Payme/Click).
- **No AI & Matching service** for now.
- **Everything is free.** No premium logic for now.
- Do not propose or add features outside this scope without asking.

## Database
- **PostgreSQL only**, in every service. Never SQLite, not even for logs or tests.
- One database per service. No cross-database SELECT/JOIN; use REST or RabbitMQ events.

## Testing
- All work must pass tests before it is considered done.
- Add or update tests together with the code, run them, and report the real result. If something fails or was not run, say so.

## Docs
- When a new endpoint or function is added and its tests pass, update the docs in the same piece of work: edit the existing doc file, or add a new one if none fits.
- Do not document code whose tests fail or were not run.

## Code conventions
- **No hardcoding.** Secrets, URLs, ports, limits, TTLs, and other configurable values come from env/config, never literals in code. No default secrets in `docker-compose.yml` or code.
- **No duplication (DRY).** Define a value or logic once and reuse it: constants, shared helpers, one schema per contract. If the same thing appears in two places, extract it.
- Everything in English: variables, functions, tables, API payloads, comments, commit messages, error messages.
- Keep comments minimal. Comment only the non-obvious "why", never what the code plainly does.
- Define the Pydantic contract before implementing an endpoint that crosses a service boundary.

## Git
- **Never run `git commit` or `git push` without asking the user first, every time.** Earlier approval does not carry over.
- **Do not add Claude attribution** to commits or PRs: no `Co-Authored-By`, no "Generated with Claude Code".
- Commit in logical steps with clear English messages. There is no line limit for PRs.
