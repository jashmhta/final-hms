import { createSlice, PayloadAction } from '@reduxjs/toolkit'
import { apiSlice } from '../api/apiSlice'

// Patient interface
export interface Patient {
  id: string
  medicalRecordNumber: string
  firstName: string
  lastName: string
  dateOfBirth: string
  gender: 'M' | 'F' | 'O'
  email: string
  phone: string
  address: string
  emergencyContact: {
    name: string
    relationship: string
    phone: string
  }
  insuranceInformation: {
    provider: string
    policyNumber: string
    groupNumber: string
    expirationDate: string
  }
  allergies: string[]
  medications: string[]
  medicalConditions: string[]
  bloodType: string
  createdAt: string
  updatedAt: string
}

// Patient state interface
interface PatientsState {
  patients: Patient[]
  currentPatient: Patient | null
  loading: boolean
  error: string | null
  filters: {
    search: string
    status: 'all' | 'active' | 'inactive'
    department?: string
  }
  pagination: {
    page: number
    limit: number
    total: number
  }
}

// Initial state
const initialState: PatientsState = {
  patients: [],
  currentPatient: null,
  loading: false,
  error: null,
  filters: {
    search: '',
    status: 'all',
  },
  pagination: {
    page: 1,
    limit: 20,
    total: 0,
  },
}

// Patients slice
const patientsSlice = createSlice({
  name: 'patients',
  initialState,
  reducers: {
    setPatients: (state, action: PayloadAction<Patient[]>) => {
      state.patients = action.payload
    },
    setCurrentPatient: (state, action: PayloadAction<Patient | null>) => {
      state.currentPatient = action.payload
    },
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.loading = action.payload
    },
    setError: (state, action: PayloadAction<string | null>) => {
      state.error = action.payload
    },
    setFilters: (state, action: PayloadAction<Partial<PatientsState['filters']>>) => {
      state.filters = { ...state.filters, ...action.payload }
    },
    setPagination: (state, action: PayloadAction<Partial<PatientsState['pagination']>>) => {
      state.pagination = { ...state.pagination, ...action.payload }
    },
    addPatient: (state, action: PayloadAction<Patient>) => {
      state.patients.unshift(action.payload)
    },
    updatePatient: (state, action: PayloadAction<Patient>) => {
      const index = state.patients.findIndex(p => p.id === action.payload.id)
      if (index !== -1) {
        state.patients[index] = action.payload
      }
      if (state.currentPatient?.id === action.payload.id) {
        state.currentPatient = action.payload
      }
    },
    deletePatient: (state, action: PayloadAction<string>) => {
      state.patients = state.patients.filter(p => p.id !== action.payload)
      if (state.currentPatient?.id === action.payload) {
        state.currentPatient = null
      }
    },
    clearError: (state) => {
      state.error = null
    },
  },
  extraReducers: (builder) => {
    builder
      // Handle API actions
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
  setPatients,
  setCurrentPatient,
  setLoading,
  setError,
  setFilters,
  setPagination,
  addPatient,
  updatePatient,
  deletePatient,
  clearError,
} = patientsSlice.actions

// Export reducer
export default patientsSlice.reducer

// Selectors
export const selectPatients = (state: { patients: PatientsState }) => state.patients.patients
export const selectCurrentPatient = (state: { patients: PatientsState }) => state.patients.currentPatient
export const selectPatientsLoading = (state: { patients: PatientsState }) => state.patients.loading
export const selectPatientsError = (state: { patients: PatientsState }) => state.patients.error
export const selectPatientsFilters = (state: { patients: PatientsState }) => state.patients.filters
export const selectPatientsPagination = (state: { patients: PatientsState }) => state.patients.pagination

// API endpoints
export const patientsApi = apiSlice.injectEndpoints({
  endpoints: (builder) => ({
    getPatients: builder.query<Patient[], void>({
      query: () => 'patients/',
      providesTags: ['Patient'],
    }),
    getPatient: builder.query<Patient, string>({
      query: (id) => `patients/${id}/`,
      providesTags: (result, error, id) => [{ type: 'Patient', id }],
    }),
    createPatient: builder.mutation<Patient, Partial<Patient>>({
      query: (patient) => ({
        url: 'patients/',
        method: 'POST',
        body: patient,
      }),
      invalidatesTags: ['Patient'],
    }),
    updatePatient: builder.mutation<Patient, { id: string; data: Partial<Patient> }>({
      query: ({ id, data }) => ({
        url: `patients/${id}/`,
        method: 'PATCH',
        body: data,
      }),
      invalidatesTags: (result, error, { id }) => [{ type: 'Patient', id }],
    }),
    deletePatient: builder.mutation<void, string>({
      query: (id) => ({
        url: `patients/${id}/`,
        method: 'DELETE',
      }),
      invalidatesTags: (result, error, id) => [{ type: 'Patient', id }],
    }),
    searchPatients: builder.query<Patient[], string>({
      query: (searchTerm) => `patients/search/?q=${searchTerm}`,
      providesTags: ['Patient'],
    }),
  }),
})

export const {
  useGetPatientsQuery,
  useGetPatientQuery,
  useCreatePatientMutation,
  useUpdatePatientMutation,
  useDeletePatientMutation,
  useSearchPatientsQuery,
} = patientsApi