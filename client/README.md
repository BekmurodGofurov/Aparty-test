# Aparty client

React + Vite app. See [docs/frontend.md](../docs/frontend.md) for pages, configuration, caching and tests.

```
npm ci
npm run dev     # http://127.0.0.1:5173, live updates and /api proxy
npm run check   # lint, unit tests and production build
npm test        # unit tests
npm run build
```

The development server binds to loopback and keeps port 5173 fixed. If that
port is occupied, it reports an error instead of silently choosing another port.
