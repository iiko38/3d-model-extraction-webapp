'use client'

import { createContext, useContext } from 'react'
import { useAdmin } from '@/hooks/useAdmin'

interface AdminContextType {
  user: any
  isAdmin: boolean
  loading: boolean
  login: (email: string, password: string) => Promise<{ data: any; error: any }>
  logout: () => Promise<{ error: any }>
}

const AdminContext = createContext<AdminContextType | undefined>(undefined)

export function AdminProvider({ children }: { children: React.ReactNode }) {
  const adminState = useAdmin()

  return (
    <AdminContext.Provider value={adminState}>
      {children}
    </AdminContext.Provider>
  )
}

export function useAdminContext() {
  const context = useContext(AdminContext)
  if (context === undefined) {
    throw new Error('useAdminContext must be used within an AdminProvider')
  }
  return context
}
