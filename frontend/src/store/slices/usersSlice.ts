import { createSlice, PayloadAction } from '@reduxjs/toolkit'

// Users interfaces
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

export interface Department {
  id: string
  name: string
  code: string
  headId?: string
  isActive: boolean
}

// Users state interface
interface UsersState {
  users: User[]
  departments: Department[]
  loading: boolean
  error: string | null
  filters: {
    role?: string
    department?: string
    isActive?: boolean
    search: string
  }
}

// Initial state
const initialState: UsersState = {
  users: [],
  departments: [],
  loading: false,
  error: null,
  filters: {
    search: '',
  },
}

// Users slice
const usersSlice = createSlice({
  name: 'users',
  initialState,
  reducers: {
    setUsers: (state, action: PayloadAction<User[]>) => {
      state.users = action.payload
    },
    setDepartments: (state, action: PayloadAction<Department[]>) => {
      state.departments = action.payload
    },
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.loading = action.payload
    },
    setError: (state, action: PayloadAction<string | null>) => {
      state.error = action.payload
    },
    setFilters: (state, action: PayloadAction<Partial<UsersState['filters']>>) => {
      state.filters = { ...state.filters, ...action.payload }
    },
    addUser: (state, action: PayloadAction<User>) => {
      state.users.push(action.payload)
    },
    updateUser: (state, action: PayloadAction<User>) => {
      const index = state.users.findIndex(u => u.id === action.payload.id)
      if (index !== -1) {
        state.users[index] = action.payload
      }
    },
    deactivateUser: (state, action: PayloadAction<string>) => {
      const user = state.users.find(u => u.id === action.payload)
      if (user) {
        user.isActive = false
      }
    },
    clearError: (state) => {
      state.error = null
    },
  },
})

// Export actions
export const {
  setUsers,
  setDepartments,
  setLoading,
  setError,
  setFilters,
  addUser,
  updateUser,
  deactivateUser,
  clearError,
} = usersSlice.actions

// Export reducer
export default usersSlice.reducer

// Selectors
export const selectUsers = (state: { users: UsersState }) => state.users.users
export const selectDepartments = (state: { users: UsersState }) => state.users.departments
export const selectUsersLoading = (state: { users: UsersState }) => state.users.loading
export const selectUsersError = (state: { users: UsersState }) => state.users.error

export default usersSlice.reducer