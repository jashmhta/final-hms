import { useEffect, useMemo, useState } from 'react'
import { Box, Paper, Typography, Stack, Button } from '@mui/material'
import axios from 'axios'
import { Line, LineChart, CartesianGrid, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'

export default function AnalyticsPage() {
  const [overview, setOverview] = useState<{patients_count:number;appointments_today:number;revenue_cents:number} | null>(null)
  const [apptTrend, setApptTrend] = useState<Array<{date:string;appointments:number}>>([])
  const [revTrend, setRevTrend] = useState<Array<{date:string;revenue_cents:number}>>([])

  useEffect(() => {
    axios.get('/api/analytics/overview').then(r => setOverview(r.data)).catch(() => setOverview(null))
    Promise.all([
      axios.get('/api/analytics/appointments_trend?days=14'),
      axios.get('/api/analytics/revenue_trend?days=14'),
    ]).then(([a, b]) => {
      setApptTrend(a.data || [])
      setRevTrend(b.data || [])
    }).catch(() => {
      setApptTrend([])
      setRevTrend([])
    })
  }, [])

  const revenue = useMemo(() => revTrend.map(x => ({ ...x, revenue: x.revenue_cents / 100 })), [revTrend])

  return (
    <Box>
      <Typography variant="h5" gutterBottom>Analytics</Typography>
      <Paper sx={{ p: 2, mb: 2 }}>
        <Typography>Patients: {overview?.patients_count ?? '-'}</Typography>
        <Typography>Appointments today: {overview?.appointments_today ?? '-'}</Typography>
        <Typography>Revenue: ₹{((overview?.revenue_cents ?? 0) / 100).toFixed(2)}</Typography>
        <Stack direction="row" spacing={2} sx={{ mt: 2 }}>
          <Button variant="outlined" onClick={() => window.open('/api/accounting/export-bills', '_blank')}>Export Bills CSV</Button>
          <Button variant="outlined" onClick={() => window.open('/api/accounting/export-bills-xlsx', '_blank')}>Export Bills XLSX</Button>
          <Button variant="outlined" onClick={() => window.open('/api/accounting/tally-xml', '_blank')}>Export Tally XML</Button>
        </Stack>
      </Paper>
      <Paper sx={{ p: 2, mb: 2 }}>
        <Typography variant="h6">Appointments (last 14 days)</Typography>
        <Box sx={{ width: '100%', height: 300 }}>
          <ResponsiveContainer>
            <LineChart data={apptTrend}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date"/>
              <YAxis allowDecimals={false} />
              <Tooltip />
              <Line type="monotone" dataKey="appointments" stroke="#000" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </Box>
      </Paper>
      <Paper sx={{ p: 2 }}>
        <Typography variant="h6">Revenue (₹, last 14 days)</Typography>
        <Box sx={{ width: '100%', height: 300 }}>
          <ResponsiveContainer>
            <LineChart data={revenue}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date"/>
              <YAxis />
              <Tooltip />
              <Line type="monotone" dataKey="revenue" stroke="#111" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </Box>
      </Paper>
    </Box>
  )
}
