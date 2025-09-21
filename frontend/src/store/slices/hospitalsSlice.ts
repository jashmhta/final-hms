import { createSlice, PayloadAction } from '@reduxjs/toolkit'

// Hospitals interfaces
export interface Hospital {
  id: string
  name: string
  code: string
  type: 'general' | 'specialized' | 'clinic' | 'laboratory'
  address: string
  city: string
  state: string
  country: string
  zipCode: string
  phone: string
  email: string
  website?: string
  capacity: number
  currentOccupancy: number
  isActive: boolean
  departments: Department[]
  createdAt: string
  updatedAt: string
}

export interface Department {
  id: string
  hospitalId: string
  name: string
  code: string
  type: string
  headId?: string
  phone: string
  email: string
  location: string
  capacity: number
  isActive: boolean
}

// Hospitals state interface
interface HospitalsState {
  hospitals: Hospital[]
  currentHospital: Hospital | null
  loading: boolean
  error: string | null
  filters: {
    type?: string
    city?: string
    isActive?: boolean
  }
}

// Initial state
const initialState: HospitalsState = {
  hospitals: [],
  currentHospital: null,
  loading: false,
  error: null,
  filters: {},
}

// Hospitals slice
const hospitalsSlice = createSlice({
  name: 'hospitals',
  initialState,
  reducers: {
    setHospitals: (state, action: PayloadAction<Hospital[]>) => {
      state.hospitals = action.payload
    },
    setCurrentHospital: (state, action: PayloadAction<Hospital | null>) => {
      state.currentHospital = action.payload
    },
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.loading = action.payload
    },
    setError: (state, action: PayloadAction<string | null>) => {
      state.error = action.payload
    },
    setFilters: (state, action: PayloadAction<Partial<HospitalsState['filters']>>) => {
      state.filters = { ...state.filters, ...action.payload }
    },
    addHospital: (state, action: PayloadAction<Hospital>) => {
      state.hospitals.push(action.payload)
    },
    updateHospital: (state, action: PayloadAction<Hospital>) => {
      const index = state.hospitals.findIndex(h => h.id === action.payload.id)
      if (index !== -1) {
        state.hospitals[index] = action.payload
      }
      if (state.currentHospital?.id === action.payload.id) {
        state.currentHospital = action.payload
      }
    },
    clearError: (state) => {
      state.error = null
    },
  },
})

// Export actions
export const {
  setHospitals,
  setCurrentHospital,
  setLoading,
  setError,
  setFilters,
  addHospital,
  updateHospital,
  clearError,
} = hospitalsSlice.actions

// Export reducer
export default hospitalsSlice.reducer

// Selectors
export const selectHospitals = (state: { hospitals: HospitalsState }) => state.hospitals.hospitals
export const selectCurrentHospital = (state: { hospitals: HospitalsState }) => state.hospitals.currentHospital
export const selectHospitalsLoading = (state: { hospitals: HospitalsState }) => state.hospitals.loading
export const selectHospitalsError = (state: { hospitals: HospitalsState }) => state.hospitals.error

export default hospitalsSlice.reducer