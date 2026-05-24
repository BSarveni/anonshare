import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import { authApi, type User } from '../lib/api'

type AuthContextValue = {
  user: User | null
  loading: boolean
  isAuthenticated: boolean
  isAdmin: boolean
  login: (token: string) => Promise<void>
  logout: () => void
  refreshUser: () => Promise<void>
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  const refreshUser = useCallback(async () => {
    const token = localStorage.getItem('token')
    if (!token) {
      setUser(null)
      return
    }
    const { data } = await authApi.me()
    setUser(data)
  }, [])

  const login = useCallback(
    async (token: string) => {
      localStorage.setItem('token', token)
      await refreshUser()
    },
    [refreshUser],
  )

  const logout = useCallback(() => {
    localStorage.removeItem('token')
    setUser(null)
  }, [])

  useEffect(() => {
    refreshUser()
      .catch(() => {
        localStorage.removeItem('token')
        setUser(null)
      })
      .finally(() => setLoading(false))
  }, [refreshUser])

  const value = useMemo(
    () => ({
      user,
      loading,
      isAuthenticated: !!user,
      isAdmin: !!user?.is_admin,
      login,
      logout,
      refreshUser,
    }),
    [user, loading, login, logout, refreshUser],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
