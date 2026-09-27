# Frontend

React + Vite single-page app in `client/`. It talks only to the API gateway (`/api/v1/*`); every call maps to an endpoint in [services.md](services.md).

## Pages

| Route | Who | Data |
|---|---|---|
| `/` | everyone | Real listings from `GET /listings/search` (tabs: all, roommate ads, rooms) and the real active-listing count |
| `/search`, `/map` | everyone | `GET /listings/search` with the filters listed in services.md. Search loads 12 per page and "Show more" appends the next page |
| `/listing/:id` | everyone | `GET /listings/{id}`, similar listings from the same district, booking request, roommate ads, Telegram and phone buttons |
| `/login`, `/auth/telegram/callback`, `/choose-role` | signed out / new users | Telegram login and one-time role choice |
| `/profile`, `/my-bookings` | students | Saved listings (`/favorites/me`), bookings (`/bookings`); stats are counted from these |
| `/owner`, `/owner/create`, `/owner/listing/:id/edit`, `/owner/profile` | owners | Own listings, incoming bookings |
| `/makler`, `/makler/create`, `/makler/listing/:id/edit`, `/makler/profile` | maklers | Same as owners |

People contact each other through Telegram (`owner_telegram_url`) or by phone. There is no chat, payments, subscriptions, reviews, AI assistant or admin panel, because the backend has none of them.

## Configuration

| Variable | Purpose |
|---|---|
| `VITE_BACKEND_API` | Gateway URL. Empty means same origin (the dev server proxies `/api`) |
| `VITE_CONTACT_PHONE`, `VITE_CONTACT_EMAIL`, `VITE_CONTACT_ADDRESS` | Optional. Shown in the footer only when set |
| `DEV_API_PROXY_TARGET`, `DEV_ALLOWED_HOSTS` | Dev server proxy target and allowed hosts (for tunnels) |

## Speed and traffic

- Pages load on demand (`React.lazy`), so the first visit downloads only what it opens. The map library loads only with the map and the create/edit forms.
- GET responses are cached in `localStorage` (`services/httpCache.js`): search 1 minute, a listing 2 minutes, saved listings 2 minutes, own profile 5 minutes. Keys include the signed-in user's id, so accounts never share data. Bookings, incoming requests, own listings and notifications are never cached.
- Identical GET requests that are already running share one network call.
- A write (create, edit, delete, save, book) drops the cache entries it could change. Signing out clears the cache.
- Notifications refresh every 60 seconds, and not while the tab is hidden.
- Photos are shrunk in the browser (longest side 1600 px, JPEG) before upload.
- The refresh token lives in an httpOnly cookie. The access token and role are kept in `localStorage`.

## Tests

`npm test` runs the unit tests (`node --test`): cache rules, booking adapters, profile stats, image sizing, JWT and time helpers. `npm run lint` and `npm run build` must pass too.
