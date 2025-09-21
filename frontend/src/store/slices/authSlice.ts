import { createSlice, PayloadAction } from '@reduxjs/toolkit'

// Auth interfaces
export interface User {
  id: string
  username: string
  email: string
  firstName: string
  lastName: string
  role: string
  permissions: string[]
  department?: string
  facility?: string
  isActive: boolean
  lastLogin?: string
}

export interface AuthState {
  user: User | null
  token: string | null
  refreshToken: string | null
  isAuthenticated: boolean
  loading: boolean
  error: string | null
  mfaRequired: boolean
  mfaVerified: boolean
}

// Initial state
const initialState: AuthState = {
  user: null,
  token: null,
  refreshToken: null,
  isAuthenticated: false,
  loading: false,
  error: null,
  mfaRequired: false,
  mfaVerified: false,
}

// Auth slice
const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    setUser: (state, action: PayloadAction<User>) => {
      state.user = action.payload
    },
    setToken: (state, action: PayloadAction<string>) => {
      state.token = action.payload
      state.isAuthenticated = true
    },
    setRefreshToken: (state, action: PayloadAction<string>) => {
      state.refreshToken = action.payload
    },
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.loading = action.payload
    },
    setError: (state, action: PayloadAction<string | null>) => {
      state.error = action.payload
    },
    setMfaRequired: (state, action: PayloadAction<boolean>) => {
      state.mfaRequired = action.payload
    },
    setMfaVerified: (state, action: PayloadAction<boolean>) => {
      state.mfaVerified = action.payload
    },
    loginSuccess: (state, action: PayloadAction<{ user: User; token: string; refreshToken: string }>) => {
      state.user = action.payload.user
      state.token = action.payload.token
      state.refreshToken = action.payload.refreshToken
      state.isAuthenticated = true
      state.loading = false
      state.error = null
    },
    loginFailure: (state, action: PayloadAction<string>) => {
      state.user = null
      state.token = null
      state.refreshToken = null
      state.isAuthenticated = false
      state.loading = false
      state.error = action.payload
    },
    logout: (state) => {
      state.user = null
      state.token = null
      state.refreshToken = null
      state.isAuthenticated = false
      state.mfaRequired = false
      state.mfaVerified = false
      state.loading = false
      state.error = null
    },
    clearError: (state) => {
      state.error = null
    },
    updateUserProfile: (state, action: PayloadAction<Partial<User>>) => {
      if (state.user) {
        state.user = { ...state.user, ...action.payload }
      }
    },
  },
})

// Export actions
export const {
  setUser,
  setToken,
  setRefreshToken,
  setLoading,
  setError,
  setMfaRequired,
  setMfaVerified,
  loginSuccess,
  loginFailure,
  logout,
  clearError,
  updateUserProfile,
} = authSlice.actions

// Export reducer
export default authSlice.reducer

// Selectors
export const selectUser = (state: { auth: AuthState }) => state.auth.user
export const selectToken = (state: { auth: AuthState }) => state.auth.token
export const selectIsAuthenticated = (state: { auth: AuthState }) => state.auth.isAuthenticated
export const selectAuthLoading = (state: { auth: AuthState }) => state.auth.loading
export const selectAuthError = (state: { auth: AuthState }) => state.auth.error
export const selectMfaRequired = (state: { auth: AuthState }) => state.auth.mfaRequired
export const selectMfaVerified = (state: { auth: AuthState }) => state.auth.mfaVerified
export const selectUserPermissions = (state: { auth: AuthState }) => state.auth.user?.permissions || []
export const selectUserRole = (state: { auth: AuthState }) => state.auth.user?.role