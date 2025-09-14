import { useEffect, useState } from 'react'
import { Box, Button, MenuItem, Paper, Stack, TextField, Typography } from '@mui/material'
import axios from 'axios'

export default function ConsentPage() {
  const [templates, setTemplates] = useState<Array<{id:number;name:string;body:string}>>([])
  const [selected, setSelected] = useState<number>(1)
  const [signer, setSigner] = useState({ patient_id: '', signer_name: '', signer_phone: '' })
  const [message, setMessage] = useState('')

  const refresh = async () => {
    const r = await axios.get('/api/consent/templates')
    setTemplates(r.data)
    if (r.data.length && !selected) setSelected(r.data[0].id)
  }
  useEffect(() => { refresh().catch(() => setTemplates([])) }, [])

  const selectedTemplate = templates.find(t => t.id === selected)

  return (
    <Box>
      <Typography variant="h5" gutterBottom>Consent</Typography>
      <Paper sx={{ p: 2, mb: 2 }}>
        <Typography variant="h6" gutterBottom>Template</Typography>
        <Stack spacing={2}>
          <TextField select label="Select Template" value={selected} onChange={(e) => setSelected(parseInt(e.target.value, 10))} sx={{ maxWidth: 360 }}>
            {templates.map(t => <MenuItem key={t.id} value={t.id}>{t.name}</MenuItem>)}
          </TextField>
          <Paper sx={{ p: 2 }}>
            <Typography whiteSpace="pre-wrap">{selectedTemplate?.body || 'No template selected'}</Typography>
          </Paper>
        </Stack>
      </Paper>
      <Paper sx={{ p: 2 }}>
        <Typography variant="h6" gutterBottom>Sign Consent</Typography>
        <Stack spacing={2} direction={{ xs: 'column', sm: 'row' }}>
          <TextField label="Patient ID" value={signer.patient_id} onChange={e => setSigner({ ...signer, patient_id: e.target.value })} />
          <TextField label="Full Name" value={signer.signer_name} onChange={e => setSigner({ ...signer, signer_name: e.target.value })} />
          <TextField label="Phone" value={signer.signer_phone} onChange={e => setSigner({ ...signer, signer_phone: e.target.value })} />
          <Button variant="contained" onClick={async () => {
            const resp = await axios.post('/api/consent/sign', { template_id: selected, patient_id: parseInt(signer.patient_id || '0', 10), signer_name: signer.signer_name, signer_phone: signer.signer_phone })
            setMessage('Signed successfully')
            try { await axios.post('/api/audit/events', { service: 'consent', action: 'sign', resource_type: 'signature', resource_id: String(resp.data.id) }) } catch {}
          }} disabled={!selected || !signer.patient_id || !signer.signer_name}>Sign</Button>
        </Stack>
        {message && <Typography sx={{ mt: 1 }}>{message}</Typography>}
      </Paper>
    </Box>
  )
}
