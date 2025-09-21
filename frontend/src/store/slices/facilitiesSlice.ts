import { createSlice, PayloadAction } from '@reduxjs/toolkit'

// Facilities interfaces
export interface Facility {
  id: string
  name: string
  type: 'room' | 'bed' | 'equipment' | 'vehicle' | 'other'
  subtype: string
  status: 'available' | 'occupied' | 'maintenance' | 'reserved' | 'inactive'
  location: string
  building?: string
  floor?: string
  departmentId?: string
  hospitalId: string
  capacity?: number
  currentOccupancy?: number
  lastMaintenance?: string
  nextMaintenance?: string
  isActive: boolean
  createdAt: string
  updatedAt: string
}

// Facilities state interface
interface FacilitiesState {
  facilities: Facility[]
  loading: boolean
  error: string | null
  filters: {
    type?: string
    status?: string
    departmentId?: string
    hospitalId?: string
  }
}

// Initial state
const initialState: FacilitiesState = {
  facilities: [],
  loading: false,
  error: null,
  filters: {},
}

// Facilities slice
const facilitiesSlice = createSlice({
  name: 'facilities',
  initialState,
  reducers: {
    setFacilities: (state, action: PayloadAction<Facility[]>) => {
      state.facilities = action.payload
    },
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.loading = action.payload
    },
    setError: (state, action: PayloadAction<string | null>) => {
      state.error = action.payload
    },
    setFilters: (state, action: PayloadAction<Partial<FacilitiesState['filters']>>) => {
      state.filters = { ...state.filters, ...action.payload }
    },
    addFacility: (state, action: PayloadAction<Facility>) => {
      state.facilities.push(action.payload)
    },
    updateFacility: (state, action: PayloadAction<Facility>) => {
      const index = state.facilities.findIndex(f => f.id === action.payload.id)
      if (index !== -1) {
        state.facilities[index] = action.payload
      }
    },
    clearError: (state) => {
      state.error = null
    },
  },
})

// Export actions
export const {
  setFacilities,
  setLoading,
  setError,
  setFilters,
  addFacility,
  updateFacility,
  clearError,
} = facilitiesSlice.actions

// Export reducer
export default facilitiesSlice.reducer

// Selectors
export const selectFacilities = (state: { facilities: FacilitiesState }) => state.facilities.facilities
export const selectFacilitiesLoading = (state: { facilities: FacilitiesState }) => state.facilities.loading
export const selectFacilitiesError = (state: { facilities: FacilitiesState }) => state.facilities.error

export default facilitiesSlice.reducer