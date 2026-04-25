import { createContext, useContext, useState, ReactNode } from 'react'
import type { AuthInfo } from '../lib/api'

interface AuthContextType {
  auth: AuthInfo | null
  setAuth: (a: AuthInfo | null) => void
  logout: () => void
}

const AuthContext = createContext<AuthContextType>(null!)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [auth, setAuthState] = useState<AuthInfo | null>(() => {
    try {
      const raw = localStorage.getItem('kinorum_auth')
      return raw ? JSON.parse(raw) : null
    } catch {
      return null
    }
  })

  const setAuth = (a: AuthInfo | null) => {
    setAuthState(a)
    if (a) {
      localStorage.setItem('kinorum_token', a.token)
      localStorage.setItem('kinorum_auth', JSON.stringify(a))
    } else {
      localStorage.removeItem('kinorum_token')
      localStorage.removeItem('kinorum_auth')
    }
  }

  const logout = () => setAuth(null)

  return (
    <AuthContext.Provider value={{ auth, setAuth, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => useContext(AuthContext)
