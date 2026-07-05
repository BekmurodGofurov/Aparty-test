import { api } from './api'

export const uploadService = {
  uploadImage: async (file) => {
    const formData = new FormData()
    formData.append('file', file)
    const { data } = await api.post('/upload/image', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
    return data
  }
}
