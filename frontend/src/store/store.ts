import { configureStore } from '@reduxjs/toolkit'
import { setupListeners } from '@tanstack/react-query'
import { apiSlice } from './api/apiSlice'
import patientsSlice from './slices/patientsSlice'
import ehrSlice from './slices/ehrSlice'
import pharmacySlice from './slices/pharmacySlice'
import labSlice from './slices/labSlice'
import appointmentsSlice from './slices/appointmentsSlice'
import billingSlice from './slices/billingSlice'
import hospitalsSlice from './slices/hospitalsSlice'
import facilitiesSlice from './slices/facilitiesSlice'
import analyticsSlice from './slices/analyticsSlice'
import authSlice from './slices/authSlice'
import usersSlice from './slices/usersSlice'
import { persistStore, persistReducer } from 'redux-persist'
import storage from 'redux-persist/lib/storage'
import { combineReducers } from '@reduxjs/toolkit'

// Redux Persist configuration
const persistConfig = {
  key: 'hms-root',
  storage,
  whitelist: ['auth', 'patients', 'appointments'], // Only persist essential data
  blacklist: ['api', 'analytics', 'billing'] // Don't persist sensitive or large data
}

// Root reducer
const rootReducer = combineReducers({
  [apiSlice.reducerPath]: apiSlice.reducer,
  auth: authSlice,
  patients: patientsSlice,
  ehr: ehrSlice,
  pharmacy: pharmacySlice,
  lab: labSlice,
  appointments: appointmentsSlice,
  billing: billingSlice,
  hospitals: hospitalsSlice,
  facilities: facilitiesSlice,
  analytics: analyticsSlice,
  users: usersSlice,
})

// Persisted reducer
const persistedReducer = persistReducer(persistConfig, rootReducer)

// Configure store
export const store = configureStore({
  reducer: persistedReducer,
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: {
        ignoredActions: ['persist/PERSIST', 'persist/REHYDRATE'],
      },
    }).concat(apiSlice.middleware),
  devTools: process.env.NODE_ENV !== 'production',
})

// Setup RTK Query listeners
setupListeners(store.dispatch)

// Persistor
export const persistor = persistStore(store)

// Infer types
export type RootState = ReturnType<typeof store.getState>
export type AppDispatch = typeof store.dispatch