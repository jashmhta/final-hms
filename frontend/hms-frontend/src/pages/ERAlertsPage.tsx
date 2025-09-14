 import React, { useCallback, useEffect, useState } from 'react'
import { Box, Typography, Button, TextField, Stack, Paper, Divider } from '@mui/material'

interface AlertItem { id: number; patient_id: number; severity: string; message: string; created_at: string }

const ERAlertsPage: React.FC = () => {
  const [alerts, setAlerts] = useState<AlertItem[]>([])
  const [patientId, setPatientId] = useState('')
  const [severity, setSeverity] = useState('CRITICAL')
  const [message, setMessage] = useState('')
  const token = localStorage.getItem('accessToken') || ''
  const hospital = JSON.parse(atob((token.split('.')[1]||'') + '=='))?.hospital || 1

  const fetchAlerts = useCallback(async () => {
    const res = await fetch(`/api/er/alerts?hospital_id=${hospital}`, { headers: { Authorization: `Bearer ${token}` } })
    if (res.ok) {
      setAlerts(await res.json())
    }
  }, [hospital, token])

  useEffect(() => { fetchAlerts() }, [fetchAlerts])

  const createAlert = async () => {
    const payload = { hospital_id: hospital, patient_id: Number(patientId), severity, message }
    const res = await fetch('/api/er/alerts', {
      method: 'POST', headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` }, body: JSON.stringify(payload)
    })
    if (res.ok) { setPatientId(''); setMessage(''); fetchAlerts() }
  }

  return (
    <Box>
      <Typography variant="h5" gutterBottom>ER Alerts</Typography>
      <Paper variant="outlined" sx={{ p: 2, mb: 3 }}>
        <Stack direction="row" spacing={2} alignItems="center">
          <TextField label="Patient ID" value={patientId} onChange={e => setPatientId(e.target.value)} size="small" />
          <TextField label="Severity" value={severity} onChange={e => setSeverity(e.target.value)} size="small" />
          <TextField label="Message" value={message} onChange={e => setMessage(e.target.value)} size="small" sx={{ minWidth: 240 }} />
          <Button variant="contained" onClick={createAlert}>Create</Button>
        </Stack>
      </Paper>
      <Divider sx={{ mb: 2 }} />
      <Stack spacing={1}>
        {alerts.map(a => (
          <Paper key={a.id} variant="outlined" sx={{ p: 1.5 }}>
            <Typography variant="subtitle2">#{a.id} • Patient {a.patient_id} • {a.severity}</Typography>
            <Typography variant="body2">{a.message}</Typography>
            <Typography variant="caption" color="text.secondary">{new Date(a.created_at).toLocaleString()}</Typography>
          </Paper>
        ))}
      </Stack>
    </Box>
  )
}

export default ERAlertsPage
