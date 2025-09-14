import { useEffect, useState } from 'react'
import { Box, Button, Paper, Stack, TextField, Typography } from '@mui/material'
import axios from 'axios'

export default function NotificationsPage() {
  const [form, setForm] = useState({ channel: 'email', recipient: '', subject: '', message: '' })
  const [status, setStatus] = useState<string>('')
  const [history, setHistory] = useState<any[]>([])
  const send = async () => {
    const r = await axios.post('/api/notifications/send', form)
    setStatus(r.data.status || 'sent')
    try {
      await axios.post('/api/audit/events', { service: 'notifications', action: 'send', resource_type: 'notification', resource_id: String(r.data.id), detail: `Sent to ${form.recipient}` })
    } catch {}
    await loadHistory()
  }
  const loadHistory = async () => {
    const r = await axios.get('/api/notifications/history')
    setHistory(r.data)
  }
  useEffect(() => { loadHistory().catch(() => setHistory([])) }, [])
  return (
    <Box>
      <Typography variant="h5" gutterBottom>Notifications</Typography>
      <Paper sx={{ p: 2 }}>
        <Stack spacing={2}>
          <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
            <TextField label="Channel" value={form.channel} onChange={e => setForm({ ...form, channel: e.target.value })} />
            <TextField label="Recipient" value={form.recipient} onChange={e => setForm({ ...form, recipient: e.target.value })} />
          </Stack>
          <TextField label="Subject" value={form.subject} onChange={e => setForm({ ...form, subject: e.target.value })} />
          <TextField label="Message" multiline minRows={3} value={form.message} onChange={e => setForm({ ...form, message: e.target.value })} />
          <Button variant="outlined" onClick={send}>Send</Button>
          {status && <Typography>Result: {status}</Typography>}
        </Stack>
      </Paper>
      <Paper sx={{ p: 2, mt: 2 }}>
        <Typography variant="h6" gutterBottom>Recent</Typography>
        {history.map(h => (
          <Box key={h.id} sx={{ mb: 1 }}>
            <Typography>#{h.id} {h.channel} to {h.recipient} - {h.subject} [{h.status}]</Typography>
          </Box>
        ))}
      </Paper>
    </Box>
  )
}
