import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react'

// Biomedical Equipment API slice
export const biomedicalApi = createApi({
  reducerPath: 'biomedicalApi',
  baseQuery: fetchBaseQuery({
    baseUrl: 'http://localhost:9074/',
  }),
  tagTypes: ['Biomedical'],
  endpoints: (builder) => ({
    // Equipment
    getEquipment: builder.query({
      query: ({ skip = 0, limit = 100 } = {}) => `equipment/?skip=${skip}&limit=${limit}`,
      providesTags: ['Biomedical'],
    }),
    getEquipmentItem: builder.query({
      query: (equipmentId) => `equipment/${equipmentId}`,
      providesTags: (result, error, equipmentId) => [{ type: 'Biomedical', id: `equipment-${equipmentId}` }],
    }),
    createEquipment: builder.mutation({
      query: (equipment) => ({
        url: 'equipment/',
        method: 'POST',
        body: equipment,
      }),
      invalidatesTags: ['Biomedical'],
    }),
    updateEquipmentStatus: builder.mutation({
      query: ({ equipmentId, status }) => ({
        url: `equipment/${equipmentId}/status`,
        method: 'PATCH',
        body: { status },
      }),
      invalidatesTags: (result, error, { equipmentId }) => [
        { type: 'Biomedical', id: `equipment-${equipmentId}` },
      ],
    }),

    // Maintenance
    getMaintenanceByEquipment: builder.query({
      query: (equipmentId) => `maintenance/equipment/${equipmentId}`,
      providesTags: ['Biomedical'],
    }),
    getUpcomingMaintenance: builder.query({
      query: (daysAhead = 30) => `maintenance/upcoming/?days_ahead=${daysAhead}`,
      providesTags: ['Biomedical'],
    }),
    getOverdueMaintenance: builder.query({
      query: () => 'maintenance/overdue/',
      providesTags: ['Biomedical'],
    }),
    createMaintenance: builder.mutation({
      query: (maintenance) => ({
        url: 'maintenance/',
        method: 'POST',
        body: maintenance,
      }),
      invalidatesTags: ['Biomedical'],
    }),
    completeMaintenance: builder.mutation({
      query: ({ maintenanceId, findings, actions_taken, next_maintenance_date }) => ({
        url: `maintenance/${maintenanceId}/complete`,
        method: 'PATCH',
        body: { findings, actions_taken, next_maintenance_date },
      }),
      invalidatesTags: ['Biomedical'],
    }),

    // Calibration
    getCalibrationByEquipment: builder.query({
      query: (equipmentId) => `calibration/equipment/${equipmentId}`,
      providesTags: ['Biomedical'],
    }),
    getOverdueCalibrations: builder.query({
      query: () => 'calibration/overdue/',
      providesTags: ['Biomedical'],
    }),
    createCalibration: builder.mutation({
      query: (calibration) => ({
        url: 'calibration/',
        method: 'POST',
        body: calibration,
      }),
      invalidatesTags: ['Biomedical'],
    }),

    // Incidents
    getIncidentsByEquipment: builder.query({
      query: (equipmentId) => `incidents/equipment/${equipmentId}`,
      providesTags: ['Biomedical'],
    }),
    getOpenIncidents: builder.query({
      query: () => 'incidents/open/',
      providesTags: ['Biomedical'],
    }),
    createIncident: builder.mutation({
      query: (incident) => ({
        url: 'incidents/',
        method: 'POST',
        body: incident,
      }),
      invalidatesTags: ['Biomedical'],
    }),
    resolveIncident: builder.mutation({
      query: ({ incidentId, resolution }) => ({
        url: `incidents/${incidentId}/resolve`,
        method: 'PATCH',
        body: { resolution },
      }),
      invalidatesTags: ['Biomedical'],
    }),

    // Training
    getTrainingByEquipment: builder.query({
      query: (equipmentId) => `training/equipment/${equipmentId}`,
      providesTags: ['Biomedical'],
    }),
    getTrainingByStaff: builder.query({
      query: (staffMember) => `training/staff/${staffMember}`,
      providesTags: ['Biomedical'],
    }),
    createTraining: builder.mutation({
      query: (training) => ({
        url: 'training/',
        method: 'POST',
        body: training,
      }),
      invalidatesTags: ['Biomedical'],
    }),

    // Vendors
    getVendors: builder.query({
      query: ({ skip = 0, limit = 100 } = {}) => `vendors/?skip=${skip}&limit=${limit}`,
      providesTags: ['Biomedical'],
    }),
    createVendor: builder.mutation({
      query: (vendor) => ({
        url: 'vendors/',
        method: 'POST',
        body: vendor,
      }),
      invalidatesTags: ['Biomedical'],
    }),

    // Statistics and dashboard
    getEquipmentStatistics: builder.query({
      query: () => 'statistics',
      providesTags: ['Biomedical'],
    }),
    getEquipmentDashboard: builder.query({
      query: () => 'dashboard',
      providesTags: ['Biomedical'],
    }),
  }),
})

export const {
  useGetEquipmentQuery,
  useGetEquipmentItemQuery,
  useCreateEquipmentMutation,
  useUpdateEquipmentStatusMutation,
  useGetMaintenanceByEquipmentQuery,
  useGetUpcomingMaintenanceQuery,
  useGetOverdueMaintenanceQuery,
  useCreateMaintenanceMutation,
  useCompleteMaintenanceMutation,
  useGetCalibrationByEquipmentQuery,
  useGetOverdueCalibrationsQuery,
  useCreateCalibrationMutation,
  useGetIncidentsByEquipmentQuery,
  useGetOpenIncidentsQuery,
  useCreateIncidentMutation,
  useResolveIncidentMutation,
  useGetTrainingByEquipmentQuery,
  useGetTrainingByStaffQuery,
  useCreateTrainingMutation,
  useGetVendorsQuery,
  useCreateVendorMutation,
  useGetEquipmentStatisticsQuery,
  useGetEquipmentDashboardQuery,
} = biomedicalApi