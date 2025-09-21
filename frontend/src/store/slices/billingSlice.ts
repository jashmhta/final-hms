import { createSlice, PayloadAction } from '@reduxjs/toolkit'

// Billing interfaces
export interface Bill {
  id: string
  patientId: string
  encounterId?: string
  billNumber: string
  totalAmount: number
  amountPaid: number
  balance: number
  status: 'draft' | 'pending' | 'paid' | 'overdue' | 'cancelled'
  dueDate: string
  items: BillItem[]
  createdAt: string
  updatedAt: string
}

export interface BillItem {
  id: string
  billId: string
  description: string
  quantity: number
  unitPrice: number
  totalPrice: number
  serviceType: string
}

export interface ServiceCatalog {
  id: string
  name: string
  description: string
  category: string
  price: number
  isActive: boolean
}

// Billing state interface
interface BillingState {
  bills: Bill[]
  serviceCatalog: ServiceCatalog[]
  loading: boolean
  error: string | null
  filters: {
    status?: string
    patientId?: string
    dateRange?: {
      start: string
      end: string
    }
  }
}

// Initial state
const initialState: BillingState = {
  bills: [],
  serviceCatalog: [],
  loading: false,
  error: null,
  filters: {},
}

// Billing slice
const billingSlice = createSlice({
  name: 'billing',
  initialState,
  reducers: {
    setBills: (state, action: PayloadAction<Bill[]>) => {
      state.bills = action.payload
    },
    setServiceCatalog: (state, action: PayloadAction<ServiceCatalog[]>) => {
      state.serviceCatalog = action.payload
    },
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.loading = action.payload
    },
    setError: (state, action: PayloadAction<string | null>) => {
      state.error = action.payload
    },
    setFilters: (state, action: PayloadAction<Partial<BillingState['filters']>>) => {
      state.filters = { ...state.filters, ...action.payload }
    },
    addBill: (state, action: PayloadAction<Bill>) => {
      state.bills.unshift(action.payload)
    },
    updateBill: (state, action: PayloadAction<Bill>) => {
      const index = state.bills.findIndex(b => b.id === action.payload.id)
      if (index !== -1) {
        state.bills[index] = action.payload
      }
    },
    clearError: (state) => {
      state.error = null
    },
  },
})

// Export actions
export const {
  setBills,
  setServiceCatalog,
  setLoading,
  setError,
  setFilters,
  addBill,
  updateBill,
  clearError,
} = billingSlice.actions

// Export reducer
export default billingSlice.reducer

// Selectors
export const selectBills = (state: { billing: BillingState }) => state.billing.bills
export const selectServiceCatalog = (state: { billing: BillingState }) => state.billing.serviceCatalog
export const selectBillingLoading = (state: { billing: BillingState }) => state.billing.loading
export const selectBillingError = (state: { billing: BillingState }) => state.billing.error

export default billingSlice.reducer