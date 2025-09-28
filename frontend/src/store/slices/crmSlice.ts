import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react'

// CRM API slice for Marketing CRM service
export const crmApi = createApi({
  reducerPath: 'crmApi',
  baseQuery: fetchBaseQuery({
    baseUrl: 'http://localhost:9070/',
  }),
  tagTypes: ['CRM'],
  endpoints: (builder) => ({
    // Leads
    getLeads: builder.query({
      query: ({ skip = 0, limit = 100 } = {}) => `leads/?skip=${skip}&limit=${limit}`,
      providesTags: ['CRM'],
    }),
    getLead: builder.query({
      query: (leadId) => `leads/${leadId}`,
      providesTags: (result, error, leadId) => [{ type: 'CRM', id: `lead-${leadId}` }],
    }),
    createLead: builder.mutation({
      query: (lead) => ({
        url: 'leads/',
        method: 'POST',
        body: lead,
      }),
      invalidatesTags: ['CRM'],
    }),
    updateLeadStatus: builder.mutation({
      query: ({ leadId, status }) => ({
        url: `leads/${leadId}/status`,
        method: 'PATCH',
        body: { status },
      }),
      invalidatesTags: (result, error, { leadId }) => [
        { type: 'CRM', id: `lead-${leadId}` },
      ],
    }),

    // Campaigns
    getCampaigns: builder.query({
      query: ({ skip = 0, limit = 100 } = {}) => `campaigns/?skip=${skip}&limit=${limit}`,
      providesTags: ['CRM'],
    }),
    getCampaign: builder.query({
      query: (campaignId) => `campaigns/${campaignId}`,
      providesTags: (result, error, campaignId) => [{ type: 'CRM', id: `campaign-${campaignId}` }],
    }),
    createCampaign: builder.mutation({
      query: (campaign) => ({
        url: 'campaigns/',
        method: 'POST',
        body: campaign,
      }),
      invalidatesTags: ['CRM'],
    }),
    updateCampaignStatus: builder.mutation({
      query: ({ campaignId, status }) => ({
        url: `campaigns/${campaignId}/status`,
        method: 'PATCH',
        body: { status },
      }),
      invalidatesTags: (result, error, { campaignId }) => [
        { type: 'CRM', id: `campaign-${campaignId}` },
      ],
    }),

    // Interactions
    getInteractionsByLead: builder.query({
      query: (leadId) => `interactions/lead/${leadId}`,
      providesTags: ['CRM'],
    }),
    createInteraction: builder.mutation({
      query: (interaction) => ({
        url: 'interactions/',
        method: 'POST',
        body: interaction,
      }),
      invalidatesTags: ['CRM'],
    }),

    // Customers
    getCustomers: builder.query({
      query: ({ skip = 0, limit = 100 } = {}) => `customers/?skip=${skip}&limit=${limit}`,
      providesTags: ['CRM'],
    }),
    getCustomer: builder.query({
      query: (customerId) => `customers/${customerId}`,
      providesTags: (result, error, customerId) => [{ type: 'CRM', id: `customer-${customerId}` }],
    }),
    createCustomer: builder.mutation({
      query: (customer) => ({
        url: 'customers/',
        method: 'POST',
        body: customer,
      }),
      invalidatesTags: ['CRM'],
    }),
    updateCustomerValue: builder.mutation({
      query: ({ customerId, additional_value }) => ({
        url: `customers/${customerId}/value`,
        method: 'PATCH',
        body: { additional_value },
      }),
      invalidatesTags: (result, error, { customerId }) => [
        { type: 'CRM', id: `customer-${customerId}` },
      ],
    }),

    // Opportunities
    getOpportunities: builder.query({
      query: ({ skip = 0, limit = 100 } = {}) => `opportunities/?skip=${skip}&limit=${limit}`,
      providesTags: ['CRM'],
    }),
    getOpportunity: builder.query({
      query: (opportunityId) => `opportunities/${opportunityId}`,
      providesTags: (result, error, opportunityId) => [{ type: 'CRM', id: `opportunity-${opportunityId}` }],
    }),
    createOpportunity: builder.mutation({
      query: (opportunity) => ({
        url: 'opportunities/',
        method: 'POST',
        body: opportunity,
      }),
      invalidatesTags: ['CRM'],
    }),
    updateOpportunityStage: builder.mutation({
      query: ({ opportunityId, stage, probability }) => ({
        url: `opportunities/${opportunityId}/stage`,
        method: 'PATCH',
        body: { stage, probability },
      }),
      invalidatesTags: (result, error, { opportunityId }) => [
        { type: 'CRM', id: `opportunity-${opportunityId}` },
      ],
    }),

    // Marketing Activities
    getMarketingActivities: builder.query({
      query: ({ skip = 0, limit = 100 } = {}) => `activities/?skip=${skip}&limit=${limit}`,
      providesTags: ['CRM'],
    }),
    createMarketingActivity: builder.mutation({
      query: (activity) => ({
        url: 'activities/',
        method: 'POST',
        body: activity,
      }),
      invalidatesTags: ['CRM'],
    }),
    updateActivityMetrics: builder.mutation({
      query: ({ activityId, metrics }) => ({
        url: `activities/${activityId}/metrics`,
        method: 'PATCH',
        body: metrics,
      }),
      invalidatesTags: ['CRM'],
    }),

    // Statistics and dashboard
    getCRMStatistics: builder.query({
      query: () => 'statistics',
      providesTags: ['CRM'],
    }),
    getCRMDashboard: builder.query({
      query: () => 'dashboard',
      providesTags: ['CRM'],
    }),
  }),
})

export const {
  useGetLeadsQuery,
  useGetLeadQuery,
  useCreateLeadMutation,
  useUpdateLeadStatusMutation,
  useGetCampaignsQuery,
  useGetCampaignQuery,
  useCreateCampaignMutation,
  useUpdateCampaignStatusMutation,
  useGetInteractionsByLeadQuery,
  useCreateInteractionMutation,
  useGetCustomersQuery,
  useGetCustomerQuery,
  useCreateCustomerMutation,
  useUpdateCustomerValueMutation,
  useGetOpportunitiesQuery,
  useGetOpportunityQuery,
  useCreateOpportunityMutation,
  useUpdateOpportunityStageMutation,
  useGetMarketingActivitiesQuery,
  useCreateMarketingActivityMutation,
  useUpdateActivityMetricsMutation,
  useGetCRMStatisticsQuery,
  useGetCRMDashboardQuery,
} = crmApi