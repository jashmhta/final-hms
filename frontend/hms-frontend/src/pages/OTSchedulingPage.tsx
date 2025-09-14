 import React, { useCallback, useEffect, useState } from 'react'
import { Box, Typography, Button, TextField, Stack, Paper, Divider } from '@mui/material'

interface SlotItem { id: number; theatre: string; start_at: string; end_at: string; procedure: string; surgeon: string }

const OTSchedulingPage: React.FC = () => {
  const [slots, setSlots] = useState<SlotItem[]>([])
  const [theatre, setTheatre] = useState('OT-1')
  const [startAt, setStartAt] = useState('')
  const [endAt, setEndAt] = useState('')
  const [procedure, setProcedure] = useState('')
  const [surgeon, setSurgeon] = useState('')
  const token = localStorage.getItem('accessToken') || ''
  const hospital = JSON.parse(atob((token.split('.')[1]||'') + '=='))?.hospital || 1

  const fetchSlots = useCallback(async () => {
    const res = await fetch(`/api/ot/slots?hospital_id=${hospital}`, { headers: { Authorization: `Bearer ${token}` } })
    if (res.ok) setSlots(await res.json())
  }, [hospital, token])
  useEffect(() => { fetchSlots() }, [fetchSlots])

  const createSlot = async () => {
    const payload = { hospital_id: hospital, theatre, start_at: new Date(startAt).toISOString(), end_at: new Date(endAt).toISOString(), procedure, surgeon }
    const res = await fetch('/api/ot/slots', { method: 'POST', headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` }, body: JSON.stringify(payload) })
    if (res.ok) { setProcedure(''); setSurgeon(''); fetchSlots() }
  }

  return (
    <Box>
      <Typography variant="h5" gutterBottom>OT Scheduling</Typography>
      <Paper variant="outlined" sx={{ p: 2, mb: 3 }}>
        <Stack direction="row" spacing={2} alignItems="center">
          <TextField label="Theatre" value={theatre} onChange={e => setTheatre(e.target.value)} size="small" />
          <TextField label="Start" type="datetime-local" value={startAt} onChange={e => setStartAt(e.target.value)} size="small" />
          <TextField label="End" type="datetime-local" value={endAt} onChange={e => setEndAt(e.target.value)} size="small" />
          <TextField label="Procedure" value={procedure} onChange={e => setProcedure(e.target.value)} size="small" />
          <TextField label="Surgeon" value={surgeon} onChange={e => setSurgeon(e.target.value)} size="small" />
          <Button variant="contained" onClick={createSlot}>Schedule</Button>
        </Stack>
      </Paper>
      <Divider sx={{ mb: 2 }} />
      <Stack spacing={1}>
        {slots.map(s => (
          <Paper key={s.id} variant="outlined" sx={{ p: 1.5 }}>
            <Typography variant="subtitle2">{s.theatre} • {new Date(s.start_at).toLocaleString()} → {new Date(s.end_at).toLocaleString()}</Typography>
            <Typography variant="body2">{s.procedure} — {s.surgeon}</Typography>
          </Paper>
        ))}
      </Stack>
    </Box>
  )
}

export default OTSchedulingPage
