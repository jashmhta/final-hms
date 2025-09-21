import { createSlice, PayloadAction } from '@reduxjs/toolkit'
import { apiSlice } from '../api/apiSlice'

// Pharmacy interfaces
export interface MedicationInventory {
  id: string
  name: string
  genericName: string
  strength: string
  form: 'tablet' | 'capsule' | 'liquid' | 'injection' | 'topical'
  currentStock: number
  reorderLevel: number
  unitPrice: number
  supplier: string
  expiryDate: string
  batchNumber: string
  storageLocation: string
  isActive: boolean
}

export interface Prescription {
  id: string
  patientId: string
  encounterId?: string
  medicationId: string
  medicationName: string
  dosage: string
  frequency: string
  duration: string
  quantity: number
  instructions: string
  prescriberId: string
  prescriberName: string
  status: 'pending' | 'dispensed' | 'cancelled' | 'completed'
  createdAt: string
  updatedAt: string
}

export interface Dispensing {
  id: string
  prescriptionId: string
  pharmacistId: string
  dispensedDate: string
  quantityDispensed: number
  batchNumber: string
  expiryDate: string
  instructions: string
  patientInstructions: string
}

// Pharmacy state interface
interface PharmacyState {
  inventory: MedicationInventory[]
  prescriptions: Prescription[]
  dispensings: Dispensing[]
  lowStockItems: MedicationInventory[]
  loading: boolean
  error: string | null
  filters: {
    medicationType?: string
    stockLevel?: 'low' | 'normal' | 'high'
    prescriptionStatus?: 'pending' | 'dispensed' | 'cancelled' | 'completed'
    search: string
  }
}

// Initial state
const initialState: PharmacyState = {
  inventory: [],
  prescriptions: [],
  dispensings: [],
  lowStockItems: [],
  loading: false,
  error: null,
  filters: {
    search: '',
  },
}

// Pharmacy slice
const pharmacySlice = createSlice({
  name: 'pharmacy',
  initialState,
  reducers: {
    setInventory: (state, action: PayloadAction<MedicationInventory[]>) => {
      state.inventory = action.payload
    },
    setPrescriptions: (state, action: PayloadAction<Prescription[]>) => {
      state.prescriptions = action.payload
    },
    setDispensings: (state, action: PayloadAction<Dispensing[]>) => {
      state.dispensings = action.payload
    },
    setLowStockItems: (state, action: PayloadAction<MedicationInventory[]>) => {
      state.lowStockItems = action.payload
    },
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.loading = action.payload
    },
    setError: (state, action: PayloadAction<string | null>) => {
      state.error = action.payload
    },
    setFilters: (state, action: PayloadAction<Partial<PharmacyState['filters']>>) => {
      state.filters = { ...state.filters, ...action.payload }
    },
    updateInventory: (state, action: PayloadAction<MedicationInventory>) => {
      const index = state.inventory.findIndex(item => item.id === action.payload.id)
      if (index !== -1) {
        state.inventory[index] = action.payload
      }
    },
    updatePrescription: (state, action: PayloadAction<Prescription>) => {
      const index = state.prescriptions.findIndex(p => p.id === action.payload.id)
      if (index !== -1) {
        state.prescriptions[index] = action.payload
      }
    },
    addDispensing: (state, action: PayloadAction<Dispensing>) => {
      state.dispensings.unshift(action.payload)
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
  setInventory,
  setPrescriptions,
  setDispensings,
  setLowStockItems,
  setLoading,
  setError,
  setFilters,
  updateInventory,
  updatePrescription,
  addDispensing,
  clearError,
} = pharmacySlice.actions

// Export reducer
export default pharmacySlice.reducer

// Selectors
export const selectInventory = (state: { pharmacy: PharmacyState }) => state.pharmacy.inventory
export const selectPrescriptions = (state: { pharmacy: PharmacyState }) => state.pharmacy.prescriptions
export const selectDispensings = (state: { pharmacy: PharmacyState }) => state.pharmacy.dispensings
export const selectLowStockItems = (state: { pharmacy: PharmacyState }) => state.pharmacy.lowStockItems
export const selectPharmacyLoading = (state: { pharmacy: PharmacyState }) => state.pharmacy.loading
export const selectPharmacyError = (state: { pharmacy: PharmacyState }) => state.pharmacy.error

export default pharmacySlice.reducer