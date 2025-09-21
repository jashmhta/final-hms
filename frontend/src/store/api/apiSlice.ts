import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react'
import type {
  BaseQueryFn,
  FetchArgs,
  FetchBaseQueryError,
} from '@reduxjs/toolkit/query'

// Base query with authentication
const baseQuery = fetchBaseQuery({
  baseUrl: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/',
  prepareHeaders: (headers, { getState }) => {
    const token = (getState() as any).auth?.token
    if (token) {
      headers.set('authorization', `Bearer ${token}`)
    }
    headers.set('Content-Type', 'application/json')
    return headers
  },
})

// Base query with retry logic for healthcare API
const baseQueryWithRetry: BaseQueryFn<
  string | FetchArgs,
  unknown,
  FetchBaseQueryError
> = async (args, api, extraOptions) => {
  const result = await baseQuery(args, api, extraOptions)

  // Retry on 401 (token refresh logic would go here)
  if (result.error?.status === 401) {
    // Token refresh logic
    const state = api.getState() as any
    const refreshToken = state.auth?.refreshToken

    if (refreshToken) {
      try {
        // Refresh token logic
        const refreshResult = await baseQuery(
          {
            url: 'auth/refresh/',
            method: 'POST',
            body: { refresh: refreshToken },
          },
          api,
          extraOptions
        )

        if (refreshResult.data) {
          // Retry original request with new token
          return baseQuery(args, api, extraOptions)
        }
      } catch (error) {
        console.error('Token refresh failed:', error)
      }
    }
  }

  return result
}

// API slice definition
export const apiSlice = createApi({
  reducerPath: 'api',
  baseQuery: baseQueryWithRetry,
  tagTypes: [
    'Patient',
    'EHR',
    'Pharmacy',
    'Lab',
    'Appointment',
    'Billing',
    'Hospital',
    'Facility',
    'Analytics',
    'User',
  ],
  endpoints: () => ({}),
})

// Auto-generated hooks will be created here for each endpoint