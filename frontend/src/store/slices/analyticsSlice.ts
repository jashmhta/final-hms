import { createSlice, PayloadAction } from '@reduxjs/toolkit'

// Analytics interfaces
export interface AnalyticsData {
  patientMetrics: {
    totalPatients: number
    newPatients: number
    activePatients: number
    patientByGender: { male: number; female: number; other: number }
    patientByAge: { '0-18': number; '19-35': number; '36-50': number; '51-65': number; '65+': number }
  }
  appointmentMetrics: {
    totalAppointments: number
    completedAppointments: number
    cancelledAppointments: number
    noShows: number
    utilizationRate: number
  }
  revenueMetrics: {
    totalRevenue: number
    monthlyRevenue: number
    topServices: Array<{ name: string; revenue: number }>
    collectionRate: number
  }
  operationalMetrics: {
    bedOccupancy: number
    averageLengthOfStay: number
    staffUtilization: number
    inventoryTurnover: number
  }
  qualityMetrics: {
    patientSatisfaction: number
    readmissionRate: number
    complicationRate: number
    mortalityRate: number
  }
}

// Analytics state interface
interface AnalyticsState {
  data: AnalyticsData | null
  loading: boolean
  error: string | null
  filters: {
    dateRange: {
      start: string
      end: string
    }
    hospitalId?: string
    departmentId?: string
  }
}

// Initial state
const initialState: AnalyticsState = {
  data: null,
  loading: false,
  error: null,
  filters: {
    dateRange: {
      start: '',
      end: '',
    },
  },
}

// Analytics slice
const analyticsSlice = createSlice({
  name: 'analytics',
  initialState,
  reducers: {
    setAnalyticsData: (state, action: PayloadAction<AnalyticsData>) => {
      state.data = action.payload
    },
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.loading = action.payload
    },
    setError: (state, action: PayloadAction<string | null>) => {
      state.error = action.payload
    },
    setFilters: (state, action: PayloadAction<Partial<AnalyticsState['filters']>>) => {
      state.filters = { ...state.filters, ...action.payload }
    },
    clearError: (state) => {
      state.error = null
    },
  },
})

// Export actions
export const {
  setAnalyticsData,
  setLoading,
  setError,
  setFilters,
  clearError,
} = analyticsSlice.actions

// Export reducer
export default analyticsSlice.reducer

// Selectors
export const selectAnalyticsData = (state: { analytics: AnalyticsState }) => state.analytics.data
export const selectAnalyticsLoading = (state: { analytics: AnalyticsState }) => state.analytics.loading
export const selectAnalyticsError = (state: { analytics: AnalyticsState }) => state.analytics.error

export default analyticsSlice.reducer