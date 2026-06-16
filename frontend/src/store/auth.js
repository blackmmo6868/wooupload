import { create } from 'zustand'

const savedStore = (() => {
  try { return JSON.parse(localStorage.getItem('selectedStore')) } catch { return null }
})()

export const useAuthStore = create((set) => ({
  user:          null,
  token:         localStorage.getItem('token'),
  selectedStore: savedStore,
  setAuth: (user, token) => {
    localStorage.setItem('token', token)
    set({ user, token })
  },
  setSelectedStore: (store) => {
    if (store) localStorage.setItem('selectedStore', JSON.stringify(store))
    else localStorage.removeItem('selectedStore')
    set({ selectedStore: store })
  },
  logout: () => {
    localStorage.removeItem('token')
    localStorage.removeItem('selectedStore')
    set({ user: null, token: null, selectedStore: null })
  },
}))
