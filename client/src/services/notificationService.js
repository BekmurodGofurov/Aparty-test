import { api } from './api'

export const notificationService = {
  getMyNotifications: async () => {
    const { data } = await api.get('/notifications/me')
    return data
  },

  markRead: async (id) => {
    const { data } = await api.patch(`/notifications/${id}/read`)
    return data
  },

  markAllRead: async () => {
    const { data } = await api.patch('/notifications/read-all')
    return data
  },
}
