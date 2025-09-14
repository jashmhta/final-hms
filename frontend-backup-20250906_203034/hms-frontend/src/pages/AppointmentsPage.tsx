import { useEffect, useMemo, useState } from 'react'
import { Container, Paper, Typography, TextField, Stack, Button } from '@mui/material'
import axios from 'axios'
import { DataGrid, GridColDef } from '@mui/x-data-grid'

export default function AppointmentsPage() {
  const [rows, setRows] = useState<any[]>([])
  const [doctorId, setDoctorId] = useState('')
  const [date, setDate] = useState('')
  const [slots, setSlots] = useState<any[]>([])
  const [patientId, setPatientId] = useState('')
  const [start, setStart] = useState('')
  const [durationMin, setDurationMin] = useState('30')
  const [hospitalId, setHospitalId] = useState<number | null>(null)

  const columns = useMemo<GridColDef[]>(() => [
    { field: 'id', headerName: 'ID', width: 80 },
    { field: 'patient', headerName: 'Patient', width: 120 },
    { field: 'doctor', headerName: 'Doctor', width: 120 },
    { field: 'start_at', headerName: 'Start', flex: 1 },
    { field: 'end_at', headerName: 'End', flex: 1 },
  ], [])

  useEffect(() => {
    axios.get('/api/appointments/').then(r => setRows(r.data.results || r.data))
    axios.get('/api/users/me/').then(r => setHospitalId(r.data.hospital))
  }, [])

  const checkSlots = async () => {
    const r = await axios.get('/api/appointments/available_slots/', { params: { doctor: doctorId, date } })
    setSlots(r.data.slots)
  }

  const createAppointment = async () => {
    if (!hospitalId) return
    const startAt = new Date(start)
    const endAt = new Date(startAt.getTime() + parseInt(durationMin, 10) * 60000)
    await axios.post('/api/appointments/', {
      hospital: hospitalId,
      patient: parseInt(patientId, 10),
      doctor: parseInt(doctorId, 10),
      start_at: startAt.toISOString(),
      end_at: endAt.toISOString(),
    })
    const r = await axios.get('/api/appointments/')
    setRows(r.data.results || r.data)
  }

  return (
    <Container sx={{ my: 3 }}>
      <Paper sx={{ p: 2, mb: 2 }}>
        <Typography variant="h6" gutterBottom>Appointments</Typography>
        <div style={{ height: 520, width: '100%' }}>
          <DataGrid rows={rows} columns={columns} pageSizeOptions={[10, 25, 50]} initialState={{ pagination: { paginationModel: { page: 0, pageSize: 10 } } }} disableRowSelectionOnClick density="compact" />
        </div>
      </Paper>
      <Paper sx={{ p: 2, mb: 2 }}>
        <Typography variant="h6" gutterBottom>Create Appointment</Typography>
        <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
          <TextField label="Patient ID" value={patientId} onChange={e => setPatientId(e.target.value)} />
          <TextField label="Doctor ID" value={doctorId} onChange={e => setDoctorId(e.target.value)} />
          <TextField label="Start" type="datetime-local" InputLabelProps={{ shrink: true }} value={start} onChange={e => setStart(e.target.value)} />
          <TextField label="Duration (min)" value={durationMin} onChange={e => setDurationMin(e.target.value)} />
          <Button variant="contained" onClick={createAppointment} disabled={!patientId || !doctorId || !start || !hospitalId}>Create</Button>
        </Stack>
      </Paper>
      <Paper sx={{ p: 2 }}>
        <Typography variant="h6" gutterBottom>Check Available Slots</Typography>
        <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
          <TextField label="Doctor ID" value={doctorId} onChange={e => setDoctorId(e.target.value)} />
          <TextField label="Date" type="date" InputLabelProps={{ shrink: true }} value={date} onChange={e => setDate(e.target.value)} />
          <Button variant="contained" onClick={checkSlots}>Check</Button>
        </Stack>
        <Typography sx={{ mt: 1 }}>{slots.length} slots</Typography>
      </Paper>
    </Container>
  )
}
