import { useEffect, useMemo, useState } from 'react'
import { Box, Button, Paper, Stack, TextField, Typography } from '@mui/material'
import axios from 'axios'
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'

interface FeedbackItem {
  id: number;
  rating: number;
  comment: string;
  hospital_id: number;
  patient_id: number;
}

export default function FeedbackPage() {
  const [items, setItems] = useState<FeedbackItem[]>([])
  const [form, setForm] = useState({ hospital_id: '1', patient_id: '', rating: '5', comment: '' })

  const refresh = async () => {
    const r = await axios.get('/api/feedback/')
    setItems(r.data)
  }
  useEffect(() => { refresh().catch(() => setItems([])) }, [])

  const chartData = useMemo(() => {
    const counts: Record<string, number> = { '1': 0, '2': 0, '3': 0, '4': 0, '5': 0 }
    items.forEach((it) => { counts[String(it.rating)] = (counts[String(it.rating)] || 0) + 1 })
    return Object.keys(counts).map(k => ({ rating: k, count: counts[k] }))
  }, [items])

  return (
    <Box>
      <Typography variant="h5" gutterBottom>Feedback</Typography>
      <Paper sx={{ p: 2, mb: 2 }}>
        <Typography variant="h6" gutterBottom>Submit Feedback</Typography>
        <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
          <TextField label="Hospital ID" value={form.hospital_id} onChange={e => setForm({ ...form, hospital_id: e.target.value })} />
          <TextField label="Patient ID" value={form.patient_id} onChange={e => setForm({ ...form, patient_id: e.target.value })} />
          <TextField label="Rating (1-5)" value={form.rating} onChange={e => setForm({ ...form, rating: e.target.value })} />
          <TextField label="Comment" value={form.comment} onChange={e => setForm({ ...form, comment: e.target.value })} />
          <Button variant="contained" onClick={async () => {
            const resp = await axios.post('/api/feedback/', { hospital_id: parseInt(form.hospital_id, 10), patient_id: parseInt(form.patient_id || '0', 10), rating: parseInt(form.rating || '1', 10), comment: form.comment })
            await axios.post('/api/audit/events', { service: 'feedback', action: 'submit', resource_type: 'feedback', resource_id: String(resp.data.id) }).catch(() => {})
            setForm({ ...form, patient_id: '', comment: '' })
            await refresh()
          }}>Submit</Button>
        </Stack>
      </Paper>
      <Paper sx={{ p: 2 }}>
        <Typography variant="h6" gutterBottom>Ratings Distribution</Typography>
        <Box sx={{ width: '100%', height: 280 }}>
          <ResponsiveContainer>
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="rating" />
              <YAxis allowDecimals={false} />
              <Tooltip />
              <Bar dataKey="count" fill="#000" />
            </BarChart>
          </ResponsiveContainer>
        </Box>
      </Paper>
    </Box>
  )
}
