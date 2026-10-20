import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

const DEFAULT_API_PROXY_TARGET = 'http://localhost:8080'

// Dev server. `/api` is proxied to the gateway, so the site and the API share one origin
// (needed for Telegram login through a tunnel such as ngrok, where cookies must stay first-party).
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const allowedHosts = (env.DEV_ALLOWED_HOSTS || '')
    .split(',')
    .map((host) => host.trim())
    .filter(Boolean)

  return {
    plugins: [react()],
    server: {
      host: '127.0.0.1',
      port: 5173,
      strictPort: true,
      allowedHosts,
      proxy: {
        '/api': { target: env.DEV_API_PROXY_TARGET || DEFAULT_API_PROXY_TARGET, changeOrigin: false },
      },
    },
  }
})
