import express from 'express'
import cors from 'cors'
import bodyParser from 'body-parser'
import fetch from 'node-fetch'
import { ApolloServer } from '@apollo/server'
import { expressMiddleware } from '@apollo/server/express4'

const PORT = process.env.PORT || 9020
const ANALYTICS_URL = process.env.ANALYTICS_URL || 'http://analytics_service:9010'
const TRIAGE_URL = process.env.TRIAGE_URL || 'http://triage_service:9009'
const RADIOLOGY_URL = process.env.RADIOLOGY_URL || 'http://radiology_service:9012'
const BED_URL = process.env.BED_URL || 'http://bed_management_service:9008'
const BACKEND_URL = process.env.BACKEND_URL || 'http://backend:8000'

const typeDefs = `#graphql
  type AnalyticsOverview {
    patients_count: Int!
    appointments_today: Int!
    revenue_cents: Int!
  }
  type TriageResult { score: Int!, priority: String! }
  type RadiologyKPI { orders: Int!, stat: Int! }
  type BedKPI { total: Int!, available: Int!, occupied: Int! }
  type AccountingPL { revenue_cents: Int!, depreciation_cents: Int!, profit_cents: Int! }
  input TriageInput {
    age: Int!, heart_rate: Int!, systolic_bp: Int!, spo2: Int!, temperature_c: Float!
  }
  type Query {
    analyticsOverview: AnalyticsOverview!
    radiologyKpi: RadiologyKPI!
    bedKpi(hospital_id: Int!): BedKPI!
    accountingPL: AccountingPL!
  }
  type Mutation {
    triageScore(input: TriageInput!): TriageResult!
  }
`

const resolvers = {
  Query: {
    analyticsOverview: async (_, __, ctx) => {
      const res = await fetch(`${ANALYTICS_URL}/api/analytics/overview`, {
        headers: { Authorization: ctx.auth, 'X-Service-Key': ctx.serviceKey }
      })
      if (!res.ok) throw new Error('analytics error')
      return await res.json()
    },
    radiologyKpi: async (_, __, ctx) => {
      const res = await fetch(`${RADIOLOGY_URL}/api/radiology/kpi`, {
        headers: { Authorization: ctx.auth, 'X-Service-Key': ctx.serviceKey }
      })
      if (!res.ok) throw new Error('radiology error')
      return await res.json()
    },
    bedKpi: async (_, { hospital_id }, ctx) => {
      const res = await fetch(`${BED_URL}/api/bed/availability?hospital_id=${hospital_id}`, {
        headers: { Authorization: ctx.auth, 'X-Service-Key': ctx.serviceKey }
      })
      if (!res.ok) throw new Error('bed error')
      const data = await res.json()
      return { total: data.total, available: data.available, occupied: data.occupied }
    },
    accountingPL: async (_, __, ctx) => {
      const res = await fetch(`${BACKEND_URL}/api/accounting/consolidated-pl/`, {
        headers: { Authorization: ctx.auth }
      })
      if (!res.ok) throw new Error('pl error')
      return await res.json()
    },
  },
  Mutation: {
    triageScore: async (_, { input }, ctx) => {
      const res = await fetch(`${TRIAGE_URL}/api/triage/score`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: ctx.auth, 'X-Service-Key': ctx.serviceKey },
        body: JSON.stringify(input)
      })
      if (!res.ok) throw new Error('triage error')
      return await res.json()
    }
  }
}

const server = new ApolloServer({ typeDefs, resolvers })
await server.start()

const app = express()
app.use(cors())
app.get('/health', (_req, res) => res.json({ status: 'ok' }))
app.use('/graphql', bodyParser.json(), expressMiddleware(server, {
  context: async ({ req }) => ({
    auth: req.headers['authorization'] || '',
    serviceKey: process.env.SERVICE_SHARED_KEY || ''
  })
}))

app.listen(PORT, () => console.log(`GraphQL gateway listening on ${PORT}`))
