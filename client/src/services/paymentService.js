import { api } from './api'

export const getPayments = async (skip = 0, limit = 10) => {
  const { data } = await api.get('/payments/', {
    params: { skip, limit },
  })
  return data
}

export const getPaymentById = async (paymentId) => {
  const { data } = await api.get(`/payments/${paymentId}`)
  return data
}

export const getUserPayments = async (userId, skip = 0, limit = 10) => {
  const { data } = await api.get(`/payments/user/${userId}`, {
    params: { skip, limit },
  })
  return data
}

export const updatePaymentStatus = async (paymentId, status) => {
  const { data } = await api.patch(`/payments/${paymentId}/status`, { status })
  return data
}

export const editPayment = async (paymentId, payload) => {
  const { data } = await api.patch(`/payments/${paymentId}`, payload)
  return data
}

export const deletePayment = async (paymentId) => {
  const { data } = await api.delete(`/payments/${paymentId}`)
  return data
}

export const createPayment = async (payload) => {
  const { data } = await api.post('/payments/', payload)
  return data
}
