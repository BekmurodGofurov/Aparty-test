import { api } from './api'

export const favoritesService = {
  toggleFavorite: async (listingId) => {
    const { data } = await api.post(`/favorites/${listingId}`)
    return data
  },
  
  getMyFavorites: async () => {
    const { data } = await api.get('/favorites/me')
    return data
  }
}
