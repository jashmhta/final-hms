import { createSlice, PayloadAction } from '@reduxjs/toolkit'
import { apiSlice } from '../api/apiSlice'

// Appointments interfaces
export interface Appointment {
  id: string
  patientId: string
  patientName: string
  providerId: string
  providerName: string
  appointmentType: string
  startTime: string
  endTime: string
  status: 'scheduled' | 'confirmed' | 'in-progress' | 'completed' | 'cancelled' | 'no-show'
  location: string
  reason: string
  notes?: string
  reminderSent: boolean
  createdAt: string
  updatedAt: string
}

export interface TimeSlot {
  id: string
  providerId: string
  startTime: string
  endTime: string
  isAvailable: boolean
  appointmentId?: string
}

// Appointments state interface
interface AppointmentsState {
  appointments: Appointment[]
  timeSlots: TimeSlot[]
  loading: boolean
  error: string | null
  filters: {
    dateRange: {
      start: string
      end: string
    }
    providerId?: string
    status?: string
    appointmentType?: string
  }
}

// Initial state
const initialState: AppointmentsState = {
  appointments: [],
  timeSlots: [],
  loading: false,
  error: null,
  filters: {
    dateRange: {
      start: '',
      end: '',
    },
  },
}

// Appointments slice
const appointmentsSlice = createSlice({
  name: 'appointments',
  initialState,
  reducers: {
    setAppointments: (state, action: PayloadAction<Appointment[]>) => {
      state.appointments = action.payload
    },
    setTimeSlots: (state, action: PayloadAction<TimeSlot[]>) => {
      state.timeSlots = action.payload
    },
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.loading = action.payload
    },
    setError: (state, action: PayloadAction<string | null>) => {
      state.error = action.payload
    },
    setFilters: (state, action: PayloadAction<Partial<AppointmentsState['filters']>>) => {
      state.filters = { ...state.filters, ...action.payload }
    },
    addAppointment: (state, action: PayloadAction<Appointment>) => {
      state.appointments.push(action.payload)
    },
    updateAppointment: (state, action: PayloadAction<Appointment>) => {
      const index = state.appointments.findIndex(a => a.id === action.payload.id)
      if (index !== -1) {
        state.appointments[index] = action.payload
      }
    },
    cancelAppointment: (state, action: PayloadAction<string>) => {
      const appointment = state.appointments.find(a => a.id === action.payload)
      if (appointment) {
        appointment.status = 'cancelled'
      }
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
  setAppointments,
  setTimeSlots,
  setLoading,
  setError,
  setFilters,
  addAppointment,
  updateAppointment,
  cancelAppointment,
  clearError,
} = appointmentsSlice.actions

// Export reducer
export default appointmentsSlice.reducer

// Selectors
export const selectAppointments = (state: { appointments: AppointmentsState }) => state.appointments.appointments
export const selectTimeSlots = (state: { appointments: AppointmentsState }) => state.appointments.timeSlots
export const selectAppointmentsLoading = (state: { appointments: AppointmentsState }) => state.appointments.loading
export const selectAppointmentsError = (state: { appointments: AppointmentsState }) => state.appointments.error

export default appointmentsSlice.reducer