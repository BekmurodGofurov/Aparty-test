import { api } from './api'

export const authService = {
  // Returns the Telegram URL the browser must be sent to.
  startTelegramLogin: async () => {
    const { data } = await api.get('/auth/telegram/start')
    return data.authorization_url
  },

  completeTelegramLogin: async ({ code, state }) => {
    const { data } = await api.post('/auth/telegram/callback', { code, state })
    return data
  },

  adminLogin: async ({ username, password }) => {
    const { data } = await api.post('/auth/admin-login', { username, password })
    return data
  },

  // Returns a new access token that carries the chosen role.
  chooseRole: async (role) => {
    const { data } = await api.put('/users/me/role', { role })
    return data
  },

  logout: async () => {
    await api.post('/auth/logout')
  },
}
