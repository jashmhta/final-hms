import { createContext } from 'react'

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

export const AuthContext = createContext<AuthContextType>({ user: null, loading: true, logout: () => {} })
