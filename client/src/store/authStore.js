import { create } from 'zustand'
import { browserCache } from '../services/browserCache'

const sanitizeStorageItem = (val) => (val === 'undefined' || val === 'null' || !val ? null : val)

export const useAuthStore = create((set) => ({
  // Initialize from localStorage
  accessToken: typeof window !== 'undefined' ? sanitizeStorageItem(localStorage.getItem('accessToken')) : null,
  role: typeof window !== 'undefined' ? sanitizeStorageItem(localStorage.getItem('role')) : null,
  userId: typeof window !== 'undefined' ? sanitizeStorageItem(localStorage.getItem('userId')) : null,
  isInitialized: false,

  setAuth: (accessToken, role, userId) => {
    if (accessToken) localStorage.setItem('accessToken', accessToken)
    else localStorage.removeItem('accessToken')

    if (role) localStorage.setItem('role', role)
    else localStorage.removeItem('role')

    if (userId != null && userId !== 'undefined' && userId !== 'null') {
      localStorage.setItem('userId', String(userId))
    } else {
      localStorage.removeItem('userId')
    }

    const cleanUserId = userId != null && userId !== 'undefined' && userId !== 'null' ? String(userId) : null
    set({ accessToken: accessToken || null, role: role || null, userId: cleanUserId, isInitialized: true })
  },

  // Initialize auth state from localStorage (called on app load)
  initializeAuth: () => {
    const accessToken = sanitizeStorageItem(localStorage.getItem('accessToken'))
    const role = sanitizeStorageItem(localStorage.getItem('role'))
    const userId = sanitizeStorageItem(localStorage.getItem('userId'))

    if (localStorage.getItem('userId') === 'undefined' || localStorage.getItem('userId') === 'null') {
      localStorage.removeItem('userId')
    }
    if (localStorage.getItem('role') === 'undefined' || localStorage.getItem('role') === 'null') {
      localStorage.removeItem('role')
    }

    set({
      accessToken: accessToken ?? null,
      role: role ?? null,
      userId: userId ?? null,
      isInitialized: true,
    })
  },

  clear: () => {
    localStorage.removeItem('accessToken')
    localStorage.removeItem('role')
    localStorage.removeItem('userId')
    browserCache.clear()
    set({ accessToken: null, role: null, userId: null, isInitialized: true })
  },
}))
