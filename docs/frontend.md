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
| `DEV_API_PROXY_TARGET`, `DEV_ALLOWED_HOSTS` | Where `/api` is proxied and which extra hosts may open the site (for tunnels). Used by `npm run dev` and `npm run share` |

## Sharing through a tunnel (ngrok)

Telegram login needs a public HTTPS address, and other people can open your local copy only through one. With ngrok and its free static domain:

1. Root `.env`: `TELEGRAM_REDIRECT_URI=https://<domain>/auth/telegram/callback` and `SITE_URL=https://<domain>`; register the same redirect URL in @BotFather. `client/.env`: `DEV_ALLOWED_HOSTS=<domain>`.
2. `docker compose up -d` in the repository root.
3. In `client/`, start one of:
   - `npm run share`: builds the app and serves the production bundle on port 5173. Use it when other people open the site. A page then loads in a few files instead of dozens of modules, which is faster through the tunnel and spends far less of ngrok's free monthly request and traffic quota. Run it again after changing the code.
   - `npm run dev`: live reload while you work. It is slower through the tunnel.
4. `ngrok http 5173 --url=<domain>`. Run a single agent, because a second one on the same domain splits the traffic between them.

Both commands proxy `/api` to the gateway, so the site and the API share one origin and the login cookies stay first-party. On the free plan, ngrok shows each new visitor a "You are about to visit" page first; the app opens after "Visit Site".

## Speed and traffic

- Pages load on demand (`React.lazy`), so the first visit downloads only what it opens. Right after that, the rest of the pages are fetched in the background while the browser is idle (`App.jsx`), so opening any other page afterwards needs no network round trip for its code. The map library still loads only with the map and the create/edit forms.
- GET responses are cached in `localStorage` (`services/httpCache.js`): search and a listing detail 1–2 minutes (public), saved listings and own profile 2–5 minutes, own listings/bookings/incoming requests 20 seconds (short, and cleared immediately by any booking write — see below). Keys include the signed-in user's id, so accounts never share data. Notifications are never cached. Two requests for the same params, in any key order, hit the same cache entry.
- Since React Router unmounts a page when you navigate away, a page's own component state can't survive a visit away and back — only the cache can. The pages people move between constantly (home, search, a listing, profile, both dashboards, saved bookings) read `services/browserCache.js`'s `peekCache()` as their *initial* state, so revisiting one already fetched this session paints the last-known content immediately and refreshes it in the background, instead of showing a loading screen again on every visit.
- Identical GET requests that are already running share one network call.
- A write (create, edit, delete, save, book, answer a booking) drops the cache entries it could change. Signing out clears the cache.
- Notifications refresh every 60 seconds, and not while the tab is hidden.
- Photos are shrunk in the browser (longest side 1600 px, JPEG) before upload.
- A photo or avatar that fails to load (an avatar changed in Telegram, a deleted upload) is replaced by initials, an icon or the placeholder photo (`components/ui/FallbackImage.jsx`) instead of a broken image.
- The refresh token lives in an httpOnly cookie. The access token and role are kept in `localStorage`.

## Tests

`npm test` runs the unit tests (`node --test`): cache rules, booking adapters, profile stats, image sizing, JWT and time helpers. `npm run lint` and `npm run build` must pass too.
