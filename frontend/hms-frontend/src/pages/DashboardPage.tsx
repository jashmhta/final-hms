import { useEffect, useState } from 'react'
import { Box, Button, Typography, Paper, List, ListItem, ListItemText, Stack, TextField } from '@mui/material'
import axios, { AxiosHeaders } from 'axios'

function authAxios() {
  const instance = axios.create()
  instance.interceptors.request.use(config => {
    const token = localStorage.getItem('accessToken')
    const headers = new AxiosHeaders(config.headers)
    if (token) headers.set('Authorization', `Bearer ${token}`)
    config.headers = headers
    return config
  })
  return instance
}

export default function DashboardPage() {
  const [overview, setOverview] = useState<{patients_count:number;appointments_today:number;revenue_cents:number} | null>(null)
  const [hospitals, setHospitals] = useState<any[]>([])
  const [estimateItems, setEstimateItems] = useState([{ description: 'Consultation', quantity: 1, unit_price_cents: 5000, gst_rate: 0.18 }])
  const [estimate, setEstimate] = useState<{subtotal_cents:number;gst_cents:number;discount_cents:number;total_cents:number} | null>(null)

  useEffect(() => {
    const api = authAxios()
    api.get('/api/analytics/overview').then(r => setOverview(r.data)).catch(() => setOverview(null))
    api.get('/api/hospitals/').then(r => setHospitals(r.data)).catch(() => setHospitals([]))
  }, [])

  return (
    <Box>
      <Stack direction={{ xs: 'column', md: 'row' }} spacing={2}>
        <Paper sx={{ p: 2, flex: 1 }}>
          <Typography variant="h6">Overview</Typography>
          <Typography>Patients: {overview?.patients_count ?? '-'}</Typography>
          <Typography>Appointments today: {overview?.appointments_today ?? '-'}</Typography>
          <Typography>Revenue: {(overview?.revenue_cents ?? 0) / 100}</Typography>
        </Paper>
        <Box sx={{ flex: 2 }}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>Hospitals</Typography>
            <List>
              {hospitals.map(h => (
                <ListItem key={h.id}>
                  <ListItemText primary={h.name} secondary={h.code} />
                </ListItem>
              ))}
            </List>
          </Paper>
          <Paper sx={{ p: 2, mt: 2 }}>
            <Typography variant="h6" gutterBottom>Quick Price Estimator</Typography>
            <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
              <TextField label="Description" value={estimateItems[0].description} onChange={e => setEstimateItems([{ ...estimateItems[0], description: e.target.value }])} />
              <TextField label="Qty" type="number" value={estimateItems[0].quantity} onChange={e => setEstimateItems([{ ...estimateItems[0], quantity: parseInt(e.target.value || '0') }])} />
              <TextField label="Unit Price (₹)" type="number" value={estimateItems[0].unit_price_cents/100} onChange={e => setEstimateItems([{ ...estimateItems[0], unit_price_cents: parseInt(e.target.value || '0')*100 }])} />
              <Button variant="contained" onClick={async () => {
                const r = await axios.post('/api/estimator/estimate', { items: estimateItems, discount_cents: 0 })
                setEstimate(r.data)
                try { await axios.post('/api/audit/events', { service: 'estimator', action: 'estimate', resource_type: 'quote', detail: `items=${estimateItems.length}` }) } catch {}
              }}>Estimate</Button>
            </Stack>
            {estimate && (
              <Box sx={{ mt: 2 }}>
                <Typography>Subtotal: ₹{(estimate.subtotal_cents/100).toFixed(2)}</Typography>
                <Typography>GST: ₹{(estimate.gst_cents/100).toFixed(2)}</Typography>
                <Typography>Total: ₹{(estimate.total_cents/100).toFixed(2)}</Typography>
              </Box>
            )}
          </Paper>
        </Box>
      </Stack>
    </Box>
  )
}
