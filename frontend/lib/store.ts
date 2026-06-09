import { create } from 'zustand'
import { User } from 'firebase/auth'

interface AuthStore {
  user: User | null
  loading: boolean
  setUser: (user: User | null) => void
  setLoading: (loading: boolean) => void
}

export const useAuthStore = create<AuthStore>((set) => ({
  user: null,
  loading: true,
  setUser: (user) => set({ user }),
  setLoading: (loading) => set({ loading }),
}))

interface ScanStore {
  recentScans: any[]
  addScan: (scan: any) => void
  clearScans: () => void
}

export const useScanStore = create<ScanStore>((set) => ({
  recentScans: [],
  addScan: (scan) =>
    set((state) => ({
      recentScans: [scan, ...state.recentScans].slice(0, 50),
    })),
  clearScans: () => set({ recentScans: [] }),
}))

interface UIStore {
  sidebarOpen: boolean
  toggleSidebar: () => void
  setSidebarOpen: (open: boolean) => void
}

export const useUIStore = create<UIStore>((set) => ({
  sidebarOpen: true,
  toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
  setSidebarOpen: (open) => set({ sidebarOpen: open }),
}))
