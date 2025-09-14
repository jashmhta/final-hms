import React, { useEffect, useState } from 'react'
import { Box, Typography, Paper, Stack, Switch, FormControlLabel, Divider, MenuItem, Select } from '@mui/material'
import axios from 'axios'

interface Hospital { id: number; name: string }
interface Plan { id: number; name: string }
interface HospitalPlan {
  id: number;
  hospital: number;
  plan: Plan;
  plan_id?: number;
  enable_opd: boolean | null;
  enable_ipd: boolean | null;
  enable_diagnostics: boolean | null;
  enable_pharmacy: boolean | null;
  enable_accounting: boolean | null;
}

const SuperAdminPage: React.FC = () => {
  const [hospitals, setHospitals] = useState<Hospital[]>([])
  const [plans, setPlans] = useState<Plan[]>([])
  const [subsByHospital, setSubsByHospital] = useState<Record<number, HospitalPlan | null>>({})

  useEffect(() => {
    axios.get('/api/hospitals/').then(r => setHospitals(r.data))
    axios.get('/api/plans/').then(r => setPlans(r.data))
  }, [])

  useEffect(() => {
    if (hospitals.length === 0) return
    hospitals.forEach(h => {
      axios.get('/api/hospital-plans/', { params: { hospital: h.id } })
        .then(r => {
          const sub = (Array.isArray(r.data) ? r.data[0] : r.data) as HospitalPlan | undefined
          setSubsByHospital(prev => ({ ...prev, [h.id]: sub || null }))
        })
        .catch(() => setSubsByHospital(prev => ({ ...prev, [h.id]: null })))
    })
  }, [hospitals])

  const updateSub = async (hospitalId: number, patch: Partial<HospitalPlan>) => {
    const current = subsByHospital[hospitalId]
    if (!current) return
    const resp = await axios.patch(`/api/hospital-plans/${current.id}/`, patch)
    setSubsByHospital(prev => ({ ...prev, [hospitalId]: resp.data }))
  }

  const changePlan = async (hospitalId: number, planId: number) => {
    const current = subsByHospital[hospitalId]
    if (!current) return
    await updateSub(hospitalId, { plan_id: planId } as any)
  }

  const flags: Array<{ key: keyof HospitalPlan; label: string }> = [
    { key: 'enable_opd', label: 'OPD' },
    { key: 'enable_ipd', label: 'IPD' },
    { key: 'enable_diagnostics', label: 'Diagnostics' },
    { key: 'enable_pharmacy', label: 'Pharmacy' },
    { key: 'enable_accounting', label: 'Accounting' },
  ]

  return (
    <Box>
      <Typography variant="h5" gutterBottom>Superadmin Control Panel</Typography>
      <Stack spacing={2}>
        {hospitals.map(h => {
          const sub = subsByHospital[h.id]
          return (
            <Paper key={h.id} variant="outlined" sx={{ p: 2 }}>
              <Typography variant="h6" gutterBottom>{h.name}</Typography>
              <Stack direction="row" spacing={2} alignItems="center" sx={{ mb: 1 }}>
                <Typography variant="body2">Plan:</Typography>
                <Select size="small" value={sub?.plan?.id || ''} onChange={(e) => changePlan(h.id, Number(e.target.value))} sx={{ minWidth: 180 }}>
                  {plans.map(p => (
                    <MenuItem key={p.id} value={p.id}>{p.name}</MenuItem>
                  ))}
                </Select>
              </Stack>
              <Divider sx={{ my: 1 }} />
              <Stack direction="row" spacing={2}>
                {flags.map(f => (
                  <FormControlLabel key={String(f.key)} control={<Switch
                    checked={(sub && (sub[f.key] ?? (sub.plan ? (sub.plan as any)[f.key] : true))) ? true : false}
                    onChange={(_e, checked) => updateSub(h.id, { [f.key]: checked } as any)}
                  />} label={f.label} />
                ))}
              </Stack>
            </Paper>
          )
        })}
      </Stack>
    </Box>
  )
}

export default SuperAdminPage
