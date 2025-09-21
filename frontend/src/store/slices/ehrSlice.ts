import { createSlice, PayloadAction } from '@reduxjs/toolkit'
import { apiSlice } from '../api/apiSlice'

// EHR interfaces
export interface ClinicalNote {
  id: string
  patientId: string
  noteType: string
  content: string
  authorId: string
  authorName: string
  createdAt: string
  updatedAt: string
}

export interface Encounter {
  id: string
  patientId: string
  encounterType: string
  startTime: string
  endTime?: string
  status: 'scheduled' | 'in-progress' | 'completed' | 'cancelled'
  location: string
  providerId: string
  chiefComplaint: string
  diagnosis: string[]
  treatment: string[]
  notes: ClinicalNote[]
}

export interface VitalSigns {
  id: string
  patientId: string
  timestamp: string
  temperature: number
  bloodPressure: {
    systolic: number
    diastolic: number
  }
  heartRate: number
  respiratoryRate: number
  oxygenSaturation: number
  height?: number
  weight?: number
  bmi?: number
  notes?: string
}

export interface Allergy {
  id: string
  patientId: string
  allergen: string
  reaction: string
  severity: 'mild' | 'moderate' | 'severe'
  onsetDate?: string
  isActive: boolean
  reportedBy: string
  reportedDate: string
}

export interface Medication {
  id: string
  patientId: string
  name: string
  dosage: string
  frequency: string
  route: string
  startDate: string
  endDate?: string
  prescriberId: string
  isActive: boolean
  instructions: string
}

export interface Immunization {
  id: string
  patientId: string
  vaccineName: string
  dateAdministered: string
  lotNumber: string
  administeredBy: string
  nextDueDate?: string
}

// EHR state interface
interface EHRState {
  encounters: Encounter[]
  currentEncounter: Encounter | null
  vitalSigns: VitalSigns[]
  allergies: Allergy[]
  medications: Medication[]
  immunizations: Immunization[]
  clinicalNotes: ClinicalNote[]
  loading: boolean
  error: string | null
  filters: {
    dateRange: {
      start: string
      end: string
    }
    encounterType?: string
  }
}

// Initial state
const initialState: EHRState = {
  encounters: [],
  currentEncounter: null,
  vitalSigns: [],
  allergies: [],
  medications: [],
  immunizations: [],
  clinicalNotes: [],
  loading: false,
  error: null,
  filters: {
    dateRange: {
      start: '',
      end: '',
    },
  },
}

// EHR slice
const ehrSlice = createSlice({
  name: 'ehr',
  initialState,
  reducers: {
    setEncounters: (state, action: PayloadAction<Encounter[]>) => {
      state.encounters = action.payload
    },
    setCurrentEncounter: (state, action: PayloadAction<Encounter | null>) => {
      state.currentEncounter = action.payload
    },
    setVitalSigns: (state, action: PayloadAction<VitalSigns[]>) => {
      state.vitalSigns = action.payload
    },
    setAllergies: (state, action: PayloadAction<Allergy[]>) => {
      state.allergies = action.payload
    },
    setMedications: (state, action: PayloadAction<Medication[]>) => {
      state.medications = action.payload
    },
    setImmunizations: (state, action: PayloadAction<Immunization[]>) => {
      state.immunizations = action.payload
    },
    setClinicalNotes: (state, action: PayloadAction<ClinicalNote[]>) => {
      state.clinicalNotes = action.payload
    },
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.loading = action.payload
    },
    setError: (state, action: PayloadAction<string | null>) => {
      state.error = action.payload
    },
    setFilters: (state, action: PayloadAction<Partial<EHRState['filters']>>) => {
      state.filters = { ...state.filters, ...action.payload }
    },
    addVitalSigns: (state, action: PayloadAction<VitalSigns>) => {
      state.vitalSigns.unshift(action.payload)
    },
    updateEncounter: (state, action: PayloadAction<Encounter>) => {
      const index = state.encounters.findIndex(e => e.id === action.payload.id)
      if (index !== -1) {
        state.encounters[index] = action.payload
      }
      if (state.currentEncounter?.id === action.payload.id) {
        state.currentEncounter = action.payload
      }
    },
    addClinicalNote: (state, action: PayloadAction<ClinicalNote>) => {
      state.clinicalNotes.unshift(action.payload)
      if (state.currentEncounter) {
        state.currentEncounter.notes.push(action.payload)
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
  setEncounters,
  setCurrentEncounter,
  setVitalSigns,
  setAllergies,
  setMedications,
  setImmunizations,
  setClinicalNotes,
  setLoading,
  setError,
  setFilters,
  addVitalSigns,
  updateEncounter,
  addClinicalNote,
  clearError,
} = ehrSlice.actions

// Export reducer
export default ehrSlice.reducer

// Selectors
export const selectEncounters = (state: { ehr: EHRState }) => state.ehr.encounters
export const selectCurrentEncounter = (state: { ehr: EHRState }) => state.ehr.currentEncounter
export const selectVitalSigns = (state: { ehr: EHRState }) => state.ehr.vitalSigns
export const selectAllergies = (state: { ehr: EHRState }) => state.ehr.allergies
export const selectMedications = (state: { ehr: EHRState }) => state.ehr.medications
export const selectImmunizations = (state: { ehr: EHRState }) => state.ehr.immunizations
export const selectClinicalNotes = (state: { ehr: EHRState }) => state.ehr.clinicalNotes
export const selectEhrLoading = (state: { ehr: EHRState }) => state.ehr.loading
export const selectEhrError = (state: { ehr: EHRState }) => state.ehr.error

// API endpoints
export const ehrApi = apiSlice.injectEndpoints({
  endpoints: (builder) => ({
    getEncounters: builder.query<Encounter[], string>({
      query: (patientId) => `ehr/encounters/?patient_id=${patientId}`,
      providesTags: (result, error, patientId) => [{ type: 'EHR', id: patientId }],
    }),
    getEncounter: builder.query<Encounter, string>({
      query: (id) => `ehr/encounters/${id}/`,
      providesTags: (result, error, id) => [{ type: 'EHR', id }],
    }),
    createEncounter: builder.mutation<Encounter, Partial<Encounter>>({
      query: (encounter) => ({
        url: 'ehr/encounters/',
        method: 'POST',
        body: encounter,
      }),
      invalidatesTags: (result, error, arg) => [{ type: 'EHR', id: arg.patientId }],
    }),
    updateEncounter: builder.mutation<Encounter, { id: string; data: Partial<Encounter> }>({
      query: ({ id, data }) => ({
        url: `ehr/encounters/${id}/`,
        method: 'PATCH',
        body: data,
      }),
      invalidatesTags: (result, error, { id }) => [{ type: 'EHR', id }],
    }),
    getVitalSigns: builder.query<VitalSigns[], string>({
      query: (patientId) => `ehr/vitals/?patient_id=${patientId}`,
      providesTags: (result, error, patientId) => [{ type: 'EHR', id: patientId }],
    }),
    addVitalSigns: builder.mutation<VitalSigns, Partial<VitalSigns>>({
      query: (vitals) => ({
        url: 'ehr/vitals/',
        method: 'POST',
        body: vitals,
      }),
      invalidatesTags: (result, error, arg) => [{ type: 'EHR', id: arg.patientId }],
    }),
    getAllergies: builder.query<Allergy[], string>({
      query: (patientId) => `ehr/allergies/?patient_id=${patientId}`,
      providesTags: (result, error, patientId) => [{ type: 'EHR', id: patientId }],
    }),
    addAllergy: builder.mutation<Allergy, Partial<Allergy>>({
      query: (allergy) => ({
        url: 'ehr/allergies/',
        method: 'POST',
        body: allergy,
      }),
      invalidatesTags: (result, error, arg) => [{ type: 'EHR', id: arg.patientId }],
    }),
    getMedications: builder.query<Medication[], string>({
      query: (patientId) => `ehr/medications/?patient_id=${patientId}`,
      providesTags: (result, error, patientId) => [{ type: 'EHR', id: patientId }],
    }),
    addMedication: builder.mutation<Medication, Partial<Medication>>({
      query: (medication) => ({
        url: 'ehr/medications/',
        method: 'POST',
        body: medication,
      }),
      invalidatesTags: (result, error, arg) => [{ type: 'EHR', id: arg.patientId }],
    }),
    getClinicalNotes: builder.query<ClinicalNote[], string>({
      query: (patientId) => `ehr/notes/?patient_id=${patientId}`,
      providesTags: (result, error, patientId) => [{ type: 'EHR', id: patientId }],
    }),
    addClinicalNote: builder.mutation<ClinicalNote, Partial<ClinicalNote>>({
      query: (note) => ({
        url: 'ehr/notes/',
        method: 'POST',
        body: note,
      }),
      invalidatesTags: (result, error, arg) => [{ type: 'EHR', id: arg.patientId }],
    }),
  }),
})

export const {
  useGetEncountersQuery,
  useGetEncounterQuery,
  useCreateEncounterMutation,
  useUpdateEncounterMutation,
  useGetVitalSignsQuery,
  useAddVitalSignsMutation,
  useGetAllergiesQuery,
  useAddAllergyMutation,
  useGetMedicationsQuery,
  useAddMedicationMutation,
  useGetClinicalNotesQuery,
  useAddClinicalNoteMutation,
} = ehrApi