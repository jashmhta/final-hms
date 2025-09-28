import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react'

// Dietary API slice
export const dietaryApi = createApi({
  reducerPath: 'dietaryApi',
  baseQuery: fetchBaseQuery({
    baseUrl: 'http://localhost:9010/',
  }),
  tagTypes: ['Dietary'],
  endpoints: (builder) => ({
    // Patient diet requirements
    getPatientDietRequirements: builder.query({
      query: (patientId) => `patient-requirements/${patientId}`,
      providesTags: (result, error, patientId) => [{ type: 'Dietary', id: `requirement-${patientId}` }],
    }),
    createPatientDietRequirement: builder.mutation({
      query: (requirement) => ({
        url: 'patient-requirements/',
        method: 'POST',
        body: requirement,
      }),
      invalidatesTags: ['Dietary'],
    }),
    updatePatientDietRequirement: builder.mutation({
      query: ({ patientId, requirement }) => ({
        url: `patient-requirements/${patientId}`,
        method: 'PUT',
        body: requirement,
      }),
      invalidatesTags: (result, error, { patientId }) => [
        { type: 'Dietary', id: `requirement-${patientId}` },
      ],
    }),

    // Food items
    getFoodItems: builder.query({
      query: ({ skip = 0, limit = 100 } = {}) => `food-items/?skip=${skip}&limit=${limit}`,
      providesTags: ['Dietary'],
    }),
    searchFoodItems: builder.query({
      query: (query) => `food-items/search/${query}`,
      providesTags: ['Dietary'],
    }),

    // Meal plans
    getMealPlans: builder.query({
      query: ({ skip = 0, limit = 100 } = {}) => `meal-plans/?skip=${skip}&limit=${limit}`,
      providesTags: ['Dietary'],
    }),
    getPatientMealPlans: builder.query({
      query: (patientId) => `meal-plans/patient/${patientId}`,
      providesTags: (result, error, patientId) => [{ type: 'Dietary', id: `meal-plans-${patientId}` }],
    }),
    createMealPlan: builder.mutation({
      query: (mealPlan) => ({
        url: 'meal-plans/',
        method: 'POST',
        body: mealPlan,
      }),
      invalidatesTags: ['Dietary'],
    }),

    // Meals
    getMeals: builder.query({
      query: ({ skip = 0, limit = 100 } = {}) => `meals/?skip=${skip}&limit=${limit}`,
      providesTags: ['Dietary'],
    }),
    getMealsByDate: builder.query({
      query: (date) => `meals/date/${date}`,
      providesTags: ['Dietary'],
    }),
    createMeal: builder.mutation({
      query: (meal) => ({
        url: 'meals/',
        method: 'POST',
        body: meal,
      }),
      invalidatesTags: ['Dietary'],
    }),
    updateMealStatus: builder.mutation({
      query: ({ mealId, served }) => ({
        url: `meals/${mealId}/serve`,
        method: 'PATCH',
        body: { served },
      }),
      invalidatesTags: ['Dietary'],
    }),

    // Menus
    getMenus: builder.query({
      query: ({ skip = 0, limit = 100 } = {}) => `menus/?skip=${skip}&limit=${limit}`,
      providesTags: ['Dietary'],
    }),
    getMenusByDietType: builder.query({
      query: (dietType) => `menus/diet/${dietType}`,
      providesTags: ['Dietary'],
    }),

    // Statistics and dashboard
    getDietaryStatistics: builder.query({
      query: () => 'statistics',
      providesTags: ['Dietary'],
    }),
    getDietaryDashboard: builder.query({
      query: () => 'dashboard',
      providesTags: ['Dietary'],
    }),
  }),
})

export const {
  useGetPatientDietRequirementsQuery,
  useCreatePatientDietRequirementMutation,
  useUpdatePatientDietRequirementMutation,
  useGetFoodItemsQuery,
  useSearchFoodItemsQuery,
  useGetMealPlansQuery,
  useGetPatientMealPlansQuery,
  useCreateMealPlanMutation,
  useGetMealsQuery,
  useGetMealsByDateQuery,
  useCreateMealMutation,
  useUpdateMealStatusMutation,
  useGetMenusQuery,
  useGetMenusByDietTypeQuery,
  useGetDietaryStatisticsQuery,
  useGetDietaryDashboardQuery,
} = dietaryApi