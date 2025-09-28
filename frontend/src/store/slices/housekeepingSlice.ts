import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react'

// Housekeeping API slice
export const housekeepingApi = createApi({
  reducerPath: 'housekeepingApi',
  baseQuery: fetchBaseQuery({
    baseUrl: 'http://localhost:9011/',
  }),
  tagTypes: ['Housekeeping'],
  endpoints: (builder) => ({
    // Housekeeping tasks
    getHousekeepingTasks: builder.query({
      query: ({ skip = 0, limit = 100 } = {}) => `tasks/?skip=${skip}&limit=${limit}`,
      providesTags: ['Housekeeping'],
    }),
    getHousekeepingTask: builder.query({
      query: (taskId) => `tasks/${taskId}`,
      providesTags: (result, error, taskId) => [{ type: 'Housekeeping', id: `task-${taskId}` }],
    }),
    createHousekeepingTask: builder.mutation({
      query: (task) => ({
        url: 'tasks/',
        method: 'POST',
        body: task,
      }),
      invalidatesTags: ['Housekeeping'],
    }),
    updateTaskStatus: builder.mutation({
      query: ({ taskId, status, notes }) => ({
        url: `tasks/${taskId}/status`,
        method: 'PATCH',
        body: { status, notes },
      }),
      invalidatesTags: (result, error, { taskId }) => [
        { type: 'Housekeeping', id: `task-${taskId}` },
      ],
    }),

    // Maintenance requests
    getMaintenanceRequests: builder.query({
      query: ({ skip = 0, limit = 100 } = {}) => `requests/?skip=${skip}&limit=${limit}`,
      providesTags: ['Housekeeping'],
    }),
    getMaintenanceRequest: builder.query({
      query: (requestId) => `requests/${requestId}`,
      providesTags: (result, error, requestId) => [{ type: 'Housekeeping', id: `request-${requestId}` }],
    }),
    createMaintenanceRequest: builder.mutation({
      query: (request) => ({
        url: 'requests/',
        method: 'POST',
        body: request,
      }),
      invalidatesTags: ['Housekeeping'],
    }),
    assignMaintenanceRequest: builder.mutation({
      query: ({ requestId, assigned_to, scheduled_date }) => ({
        url: `requests/${requestId}/assign`,
        method: 'PATCH',
        body: { assigned_to, scheduled_date },
      }),
      invalidatesTags: (result, error, { requestId }) => [
        { type: 'Housekeeping', id: `request-${requestId}` },
      ],
    }),
    completeMaintenanceRequest: builder.mutation({
      query: ({ requestId, actual_cost, notes }) => ({
        url: `requests/${requestId}/complete`,
        method: 'PATCH',
        body: { actual_cost, notes },
      }),
      invalidatesTags: (result, error, { requestId }) => [
        { type: 'Housekeeping', id: `request-${requestId}` },
      ],
    }),

    // Equipment
    getEquipment: builder.query({
      query: ({ skip = 0, limit = 100 } = {}) => `equipment/?skip=${skip}&limit=${limit}`,
      providesTags: ['Housekeeping'],
    }),
    getEquipmentItem: builder.query({
      query: (equipmentId) => `equipment/${equipmentId}`,
      providesTags: (result, error, equipmentId) => [{ type: 'Housekeeping', id: `equipment-${equipmentId}` }],
    }),
    createEquipment: builder.mutation({
      query: (equipment) => ({
        url: 'equipment/',
        method: 'POST',
        body: equipment,
      }),
      invalidatesTags: ['Housekeeping'],
    }),
    updateEquipmentMaintenance: builder.mutation({
      query: ({ equipmentId, last_maintenance_date, next_maintenance_date }) => ({
        url: `equipment/${equipmentId}/maintenance`,
        method: 'PATCH',
        body: { last_maintenance_date, next_maintenance_date },
      }),
      invalidatesTags: (result, error, { equipmentId }) => [
        { type: 'Housekeeping', id: `equipment-${equipmentId}` },
      ],
    }),

    // Staff
    getStaff: builder.query({
      query: ({ skip = 0, limit = 100 } = {}) => `staff/?skip=${skip}&limit=${limit}`,
      providesTags: ['Housekeeping'],
    }),
    getStaffMember: builder.query({
      query: (staffId) => `staff/${staffId}`,
      providesTags: (result, error, staffId) => [{ type: 'Housekeeping', id: `staff-${staffId}` }],
    }),
    createStaff: builder.mutation({
      query: (staff) => ({
        url: 'staff/',
        method: 'POST',
        body: staff,
      }),
      invalidatesTags: ['Housekeeping'],
    }),

    // Schedules
    getCleaningSchedules: builder.query({
      query: ({ skip = 0, limit = 100 } = {}) => `schedules/?skip=${skip}&limit=${limit}`,
      providesTags: ['Housekeeping'],
    }),
    getCleaningSchedule: builder.query({
      query: (scheduleId) => `schedules/${scheduleId}`,
      providesTags: (result, error, scheduleId) => [{ type: 'Housekeeping', id: `schedule-${scheduleId}` }],
    }),
    createCleaningSchedule: builder.mutation({
      query: (schedule) => ({
        url: 'schedules/',
        method: 'POST',
        body: schedule,
      }),
      invalidatesTags: ['Housekeeping'],
    }),

    // Statistics and dashboard
    getMaintenanceStatistics: builder.query({
      query: () => 'statistics',
      providesTags: ['Housekeeping'],
    }),
    getTaskDashboard: builder.query({
      query: () => 'dashboard',
      providesTags: ['Housekeeping'],
    }),
  }),
})

export const {
  useGetHousekeepingTasksQuery,
  useGetHousekeepingTaskQuery,
  useCreateHousekeepingTaskMutation,
  useUpdateTaskStatusMutation,
  useGetMaintenanceRequestsQuery,
  useGetMaintenanceRequestQuery,
  useCreateMaintenanceRequestMutation,
  useAssignMaintenanceRequestMutation,
  useCompleteMaintenanceRequestMutation,
  useGetEquipmentQuery,
  useGetEquipmentItemQuery,
  useCreateEquipmentMutation,
  useUpdateEquipmentMaintenanceMutation,
  useGetStaffQuery,
  useGetStaffMemberQuery,
  useCreateStaffMutation,
  useGetCleaningSchedulesQuery,
  useGetCleaningScheduleQuery,
  useCreateCleaningScheduleMutation,
  useGetMaintenanceStatisticsQuery,
  useGetTaskDashboardQuery,
} = housekeepingApi