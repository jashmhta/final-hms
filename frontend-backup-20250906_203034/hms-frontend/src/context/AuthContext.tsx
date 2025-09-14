import { createContext, useContext, useEffect, useState } from 'react'
import axios from 'axios'

type User = {
  id: number
  username: string
  role: string
  hospital: number | null
}

type AuthContextType = {
  user: User | null
  loading: boolean
  logout: () => void
}

const AuthContext = createContext<AuthContextType>({ user: null, loading: true, logout: () => {} })

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const token = localStorage.getItem('accessToken')
    if (!token) {
      setLoading(false)
      return
    }
    axios.get('/api/users/me/').then(r => setUser(r.data)).catch(() => setUser(null)).finally(() => setLoading(false))
  }, [])

  const logout = () => {
    localStorage.removeItem('accessToken')
    localStorage.removeItem('refreshToken')
    window.location.href = '/login'
  }

  return <AuthContext.Provider value={{ user, loading, logout }}>{children}</AuthContext.Provider>
}

export function useAuth() {
  return useContext(AuthContext)
}
