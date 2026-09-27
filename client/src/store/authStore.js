import { create } from 'zustand'
import { browserCache } from '../services/browserCache'

export const useAuthStore = create((set) => ({
  // Initialize from localStorage
  accessToken: typeof window !== 'undefined' ? localStorage.getItem('accessToken') : null,
  role: typeof window !== 'undefined' ? (localStorage.getItem('role') ?? null) : null,
  userId: typeof window !== 'undefined' ? (localStorage.getItem('userId') ?? null) : null,
  isInitialized: false,
  
  setAuth: (accessToken, role, userId) => {
    localStorage.setItem('accessToken', accessToken)
    if (role) localStorage.setItem('role', role)
    else localStorage.removeItem('role')
    localStorage.setItem('userId', userId)
    set({ accessToken, role: role || null, userId, isInitialized: true })
  },
  
  // Initialize auth state from localStorage (called on app load)
  initializeAuth: () => {
    const accessToken = localStorage.getItem('accessToken')
    const role = localStorage.getItem('role')
    const userId = localStorage.getItem('userId')
    
    set({ 
      accessToken: accessToken ?? null,
      role: role ?? null,
      userId: userId ?? null,
      isInitialized: true
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
