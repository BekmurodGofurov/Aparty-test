# Aparty client

React + Vite app. See [docs/frontend.md](../docs/frontend.md) for pages, configuration, caching and tests.

```bash
npm ci
npm run dev     # http://127.0.0.1:5173, live updates and /api proxy
npm run check   # lint, unit tests and production build
npm test        # unit tests
npm run build
npm run share   # builds and serves production bundle on port 5173 (recommended with ngrok)
```

The development server binds to loopback and keeps port 5173 fixed. If that
port is occupied, it reports an error instead of silently choosing another port.

### Telegram Login via ngrok

```bash
# 1. Start frontend
npm run dev
# (or 'npm run share' for optimized production bundle through tunnel)

# 2. In another terminal, start ngrok
ngrok http 5173 --url=<your-domain>
```
