import { createSlice, PayloadAction } from '@reduxjs/toolkit'
import { apiSlice } from '../api/apiSlice'

// Lab interfaces
export interface LabTest {
  id: string
  name: string
  code: string
  category: string
  description: string
  turnaroundTime: number // in hours
  isActive: boolean
}

export interface LabOrder {
  id: string
  patientId: string
  encounterId?: string
  providerId: string
  orderedTests: LabTest[]
  status: 'pending' | 'in-progress' | 'completed' | 'cancelled'
  priority: 'routine' | 'urgent' | 'stat'
  orderedAt: string
  completedAt?: string
  clinicalNotes?: string
}

export interface LabResult {
  id: string
  labOrderId: string
  testId: string
  testName: string
  result: string
  unit: string
  referenceRange: string
  isAbnormal: boolean
  performedBy: string
  performedAt: string
  reviewedBy?: string
  reviewedAt?: string
}

// Lab state interface
interface LabState {
  tests: LabTest[]
  orders: LabOrder[]
  results: LabResult[]
  loading: boolean
  error: string | null
  filters: {
    status?: string
    priority?: string
    dateRange?: {
      start: string
      end: string
    }
    testCategory?: string
  }
}

// Initial state
const initialState: LabState = {
  tests: [],
  orders: [],
  results: [],
  loading: false,
  error: null,
  filters: {},
}

// Lab slice
const labSlice = createSlice({
  name: 'lab',
  initialState,
  reducers: {
    setTests: (state, action: PayloadAction<LabTest[]>) => {
      state.tests = action.payload
    },
    setOrders: (state, action: PayloadAction<LabOrder[]>) => {
      state.orders = action.payload
    },
    setResults: (state, action: PayloadAction<LabResult[]>) => {
      state.results = action.payload
    },
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.loading = action.payload
    },
    setError: (state, action: PayloadAction<string | null>) => {
      state.error = action.payload
    },
    setFilters: (state, action: PayloadAction<Partial<LabState['filters']>>) => {
      state.filters = { ...state.filters, ...action.payload }
    },
    addLabOrder: (state, action: PayloadAction<LabOrder>) => {
      state.orders.unshift(action.payload)
    },
    updateLabOrder: (state, action: PayloadAction<LabOrder>) => {
      const index = state.orders.findIndex(o => o.id === action.payload.id)
      if (index !== -1) {
        state.orders[index] = action.payload
      }
    },
    addLabResult: (state, action: PayloadAction<LabResult>) => {
      state.results.unshift(action.payload)
    },
    clearError: (state) => {
      state.error = null
    },
  },
  extraReducers: (builder) => {
    builder
      .addMatcher(
        (action) => action.type.endsWith('/pending'),
        (state) => {
          state.loading = true
          state.error = null
        }
      )
      .addMatcher(
        (action) => action.type.endsWith('/fulfilled'),
        (state) => {
          state.loading = false
        }
      )
      .addMatcher(
        (action) => action.type.endsWith('/rejected'),
        (state, action) => {
          state.loading = false
          state.error = action.error.message || 'An error occurred'
        }
      )
  },
})

// Export actions
export const {
  setTests,
  setOrders,
  setResults,
  setLoading,
  setError,
  setFilters,
  addLabOrder,
  updateLabOrder,
  addLabResult,
  clearError,
} = labSlice.actions

// Export reducer
export default labSlice.reducer

// Selectors
export const selectLabTests = (state: { lab: LabState }) => state.lab.tests
export const selectLabOrders = (state: { lab: LabState }) => state.lab.orders
export const selectLabResults = (state: { lab: LabState }) => state.lab.results
export const selectLabLoading = (state: { lab: LabState }) => state.lab.loading
export const selectLabError = (state: { lab: LabState }) => state.lab.error

export default labSlice.reducer