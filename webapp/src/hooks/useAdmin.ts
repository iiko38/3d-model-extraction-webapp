import { useState, useEffect } from 'react'
import { getCurrentUser, isAdmin, signIn, signOut, onAuthStateChange, AdminUser } from '@/lib/auth'

export function useAdmin() {
  const [user, setUser] = useState<AdminUser | null>(null)
  const [adminStatus, setAdminStatus] = useState<boolean>(true) // Always true for admin access
  const [loading, setLoading] = useState<boolean>(false) // No loading needed

  useEffect(() => {
    // No auth check needed - admin is always enabled
    setLoading(false)
  }, [])

  const login = async (email: string, password: string) => {
    // No-op since admin is always enabled
    return { data: null, error: null }
  }

  const logout = async () => {
    // No-op since admin is always enabled
    return { error: null }
  }

  return {
    user,
    isAdmin: adminStatus,
    loading,
    login,
    logout
  }
}
