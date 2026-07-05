import { api } from './api'

export const normalizeUser = (user = {}) => ({
  ...user,
  id: user.id ?? user.user_id,
  ism: user.ism ?? user.full_name,
  telefon: user.telefon ?? user.phone,
  rol: user.rol ?? user.role ?? user.role_name,
  universitet: user.universitet ?? user.university,
  rasm_url: user.rasm_url ?? user.profile_picture_url,
})

export const userService = {
  getCurrentUser: async () => {
    const { data } = await api.get('/users/me')
    return normalizeUser(data)
  },
  
  updateProfile: async (payload) => {
    const { data } = await api.put('/users/me', payload)
    return normalizeUser(data)
  },
  
  getUserById: async (userId) => {
    const { data } = await api.get(`/users/${userId}`)
    return normalizeUser(data)
  }
}
