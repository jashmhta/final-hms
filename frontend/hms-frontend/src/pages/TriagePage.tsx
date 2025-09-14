import { useState } from 'react'
import { Box, Button, Paper, Stack, TextField, Typography } from '@mui/material'
import axios from 'axios'

export default function TriagePage() {
  const [form, setForm] = useState({ age: 40, heart_rate: 80, systolic_bp: 120, spo2: 98, temperature_c: 36.6 })
  const [result, setResult] = useState<{score:number;priority:string} | null>(null)
  return (
    <Box>
      <Typography variant="h5" gutterBottom>Triage</Typography>
      <Paper sx={{ p: 2 }}>
        <Stack spacing={2} direction={{ xs: 'column', sm: 'row' }}>
          <TextField label="Age" type="number" value={form.age} onChange={e => setForm({ ...form, age: parseInt(e.target.value || '0') })} />
          <TextField label="HR" type="number" value={form.heart_rate} onChange={e => setForm({ ...form, heart_rate: parseInt(e.target.value || '0') })} />
          <TextField label="SBP" type="number" value={form.systolic_bp} onChange={e => setForm({ ...form, systolic_bp: parseInt(e.target.value || '0') })} />
          <TextField label="SpO₂" type="number" value={form.spo2} onChange={e => setForm({ ...form, spo2: parseInt(e.target.value || '0') })} />
          <TextField label="Temp °C" type="number" value={form.temperature_c} onChange={e => setForm({ ...form, temperature_c: parseFloat(e.target.value || '0') })} />
          <Button variant="contained" onClick={async () => {
            const r = await axios.post('/api/triage/score', form)
            setResult(r.data)
          }}>Score</Button>
        </Stack>
        {result && (
          <Box sx={{ mt: 2 }}>
            <Typography>Score: {result.score}</Typography>
            <Typography>Priority: {result.priority}</Typography>
          </Box>
        )}
      </Paper>
    </Box>
  )
}
