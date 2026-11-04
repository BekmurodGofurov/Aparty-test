import { api } from './api'
import { compressImage } from '../utils/imageCompress'

export const uploadService = {
  uploadImage: async (file) => {
    const formData = new FormData()
    formData.append('file', await compressImage(file))
    const { data } = await api.post('/media/image', formData)
    return {
      ...data,
      url: data.url ?? data.display_url
    }
  }
}
