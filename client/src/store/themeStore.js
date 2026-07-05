import { create } from 'zustand'

const getInitialTheme = () => {
  const saved = localStorage.getItem('aparty-theme')
  const theme = saved || 'dark'
  document.documentElement.setAttribute('data-theme', theme)
  return theme
}

export const useThemeStore = create((set) => ({
  theme: getInitialTheme(),
  toggleTheme: () =>
    set((state) => {
      const next = state.theme === 'light' ? 'dark' : 'light'
      localStorage.setItem('aparty-theme', next)
      document.documentElement.setAttribute('data-theme', next)
      return { theme: next }
    }),
}))
