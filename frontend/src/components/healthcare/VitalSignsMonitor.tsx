import React, { useState, useEffect, useCallback } from 'react'
import {
  Box,
  Paper,
  Typography,
  Card,
  CardContent,
  Grid,
  LinearProgress,
  Alert,
  Chip,
  IconButton,
  Tooltip,
  Badge,
  useTheme,
  alpha,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
} from '@mui/material'
import {
  Favorite,
  FavoriteBorder,
  Thermostat,
  WaterDrop,
  Speed,
  MonitorWeight,
  Height,
  TrendingUp,
  TrendingDown,
  Refresh,
  Warning,
  Error,
  CheckCircle,
  Edit,
  History,
} from '@mui/icons-material'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, AreaChart, Area } from 'recharts'
import { format, subHours, addMinutes } from 'date-fns'

export interface VitalSigns {
  timestamp: Date
  temperature?: number
  bloodPressure?: {
    systolic: number
    diastolic: number
  }
  heartRate?: number
  oxygenSaturation?: number
  respiratoryRate?: number
  weight?: number
  height?: number
  bmi?: number
  bloodSugar?: number
  painLevel?: number
  consciousness?: string
  notes?: string
  recordedBy?: string
}

export interface VitalSignsAlert {
  id: string
  type: 'critical' | 'warning' | 'info'
  message: string
  vitalType: string
  value: number
  threshold: {
    min?: number
    max?: number
  }
  timestamp: Date
  acknowledged: boolean
}

interface VitalSignsMonitorProps {
  patientId: string
  patientName: string
  vitalSigns: VitalSigns[]
  alerts: VitalSignsAlert[]
  onVitalSignsUpdate: (vitals: VitalSigns) => void
  onAlertAcknowledge: (alertId: string) => void
  onManualEntry: (vitals: VitalSigns) => void
  className?: string
  compact?: boolean
  realTime?: boolean
}

const VitalSignsMonitor: React.FC<VitalSignsMonitorProps> = ({
  patientId,
  patientName,
  vitalSigns,
  alerts,
  onVitalSignsUpdate,
  onAlertAcknowledge,
  onManualEntry,
  className,
  compact = false,
  realTime = false,
}) => {
  const theme = useTheme()
  const [currentVitals, setCurrentVitals] = useState<VitalSigns | null>(null)
  const [historicalData, setHistoricalData] = useState<any[]>([])
  const [isEditing, setIsEditing] = useState(false)
  const [manualEntryVitals, setManualEntryVitals] = useState<Partial<VitalSigns>>({})
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date())

  const vitalRanges = {
    temperature: { min: 36.1, max: 37.2, unit: '°C', critical: { min: 35, max: 39 } },
    heartRate: { min: 60, max: 100, unit: 'bpm', critical: { min: 40, max: 150 } },
    oxygenSaturation: { min: 95, max: 100, unit: '%', critical: { min: 90, max: 100 } },
    bloodPressure: {
      systolic: { min: 90, max: 120, critical: { min: 70, max: 180 } },
      diastolic: { min: 60, max: 80, critical: { min: 40, max: 110 } },
      unit: 'mmHg',
    },
    respiratoryRate: { min: 12, max: 20, unit: 'bpm', critical: { min: 8, max: 30 } },
    bloodSugar: { min: 70, max: 140, unit: 'mg/dL', critical: { min: 50, max: 250 } },
    painLevel: { min: 0, max: 10, unit: '/10', critical: { min: 0, max: 8 } },
  }

  const getVitalStatus = (vitalType: string, value: number): 'normal' | 'warning' | 'critical' => {
    const range = vitalRanges[vitalType as keyof typeof vitalRanges]
    if (!range) return 'normal'

    if (range.min && range.max) {
      if (range.critical) {
        if (value < range.critical.min || value > range.critical.max) return 'critical'
      }
      if (value < range.min || value > range.max) return 'warning'
    }

    if (vitalType === 'bloodPressure' && typeof range === 'object') {
      const bpRange = range as any
      if (bpRange.systolic && bpRange.diastolic) {
        // This is a simplified check - in reality, BP needs more complex analysis
        if (value < bpRange.systolic.critical.min || value > bpRange.systolic.critical.max) return 'critical'
        if (value < bpRange.systolic.min || value > bpRange.systolic.max) return 'warning'
      }
    }

    return 'normal'
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'critical':
        return theme.palette.error.main
      case 'warning':
        return theme.palette.warning.main
      case 'normal':
        return theme.palette.success.main
      default:
        return theme.palette.grey[500]
    }
  }

  const formatVitalValue = (vitalType: string, value: number) => {
    const range = vitalRanges[vitalType as keyof typeof vitalRanges]
    if (!range) return value.toString()

    if (vitalType === 'bloodPressure') {
      return `${value} ${range.unit}`
    }

    return `${value} ${range.unit}`
  }

  const getVitalIcon = (vitalType: string) => {
    const icons: Record<string, React.ReactNode> = {
      temperature: <Thermostat />,
      heartRate: <Favorite />,
      oxygenSaturation: <WaterDrop />,
      bloodPressure: <Speed />,
      respiratoryRate: <MonitorWeight />,
      bloodSugar: <TrendingUp />,
      painLevel: <Error />,
    }
    return icons[vitalType] || <Speed />
  }

  const generateHistoricalData = useCallback(() => {
    const now = new Date()
    const data = []

    for (let i = 23; i >= 0; i--) {
      const time = subHours(now, i)
      const hourVitals = vitalSigns.filter(v =>
        new Date(v.timestamp).getHours() === time.getHours() &&
        new Date(v.timestamp).getDate() === time.getDate()
      )

      if (hourVitals.length > 0) {
        const latestVitals = hourVitals[hourVitals.length - 1]
        data.push({
          time: format(time, 'HH:mm'),
          temperature: latestVitals.temperature,
          heartRate: latestVitals.heartRate,
          oxygenSaturation: latestVitals.oxygenSaturation,
          bloodPressure: latestVitals.bloodPressure?.systolic,
          bloodSugar: latestVitals.bloodSugar,
        })
      } else {
        // Generate sample data for demonstration
        data.push({
          time: format(time, 'HH:mm'),
          temperature: 36.5 + Math.random() * 1,
          heartRate: 70 + Math.random() * 20,
          oxygenSaturation: 96 + Math.random() * 3,
          bloodPressure: 110 + Math.random() * 20,
          bloodSugar: 90 + Math.random() * 40,
        })
      }
    }

    return data
  }, [vitalSigns])

  useEffect(() => {
    if (vitalSigns.length > 0) {
      const latest = vitalSigns[vitalSigns.length - 1]
      setCurrentVitals(latest)
      setLastUpdate(new Date(latest.timestamp))
    }
    setHistoricalData(generateHistoricalData())
  }, [vitalSigns, generateHistoricalData])

  useEffect(() => {
    if (realTime) {
      const interval = setInterval(() => {
        // Simulate real-time updates
        const now = new Date()
        setLastUpdate(now)
      }, 30000) // Update every 30 seconds

      return () => clearInterval(interval)
    }
  }, [realTime])

  const VitalCard: React.FC<{
    title: string
    value: number | string
    status: 'normal' | 'warning' | 'critical'
    unit: string
    icon: React.ReactNode
    trend?: 'up' | 'down' | 'stable'
    historical?: number[]
  }> = ({ title, value, status, unit, icon, trend, historical }) => (
    <Card
      sx={{
        border: `2px solid ${alpha(getStatusColor(status), 0.3)}`,
        backgroundColor: alpha(getStatusColor(status), 0.05),
        '&:hover': {
          boxShadow: theme.shadows[4],
        },
        transition: 'all 0.2s ease-in-out',
      }}
    >
      <CardContent sx={{ p: 2 }}>
        <Box display="flex" justifyContent="space-between" alignItems="start" mb={1}>
          <Box display="flex" alignItems="center" gap={1}>
            <Box sx={{ color: getStatusColor(status) }}>
              {icon}
            </Box>
            <Typography variant="caption" color="textSecondary" fontWeight={600}>
              {title}
            </Typography>
          </Box>
          {trend && (
            <Box sx={{ color: trend === 'up' ? theme.palette.error.main : trend === 'down' ? theme.palette.success.main : theme.palette.info.main }}>
              {trend === 'up' ? <TrendingUp fontSize="small" /> : trend === 'down' ? <TrendingDown fontSize="small" /> : <Speed fontSize="small" />}
            </Box>
          )}
        </Box>

        <Typography variant="h4" fontWeight={600} color={getStatusColor(status)}>
          {value}
        </Typography>

        <Typography variant="caption" color="textSecondary">
          {unit}
        </Typography>

        {historical && historical.length > 0 && (
          <Box sx={{ mt: 1, height: 30 }}>
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={historical.map((val, idx) => ({ time: idx, value: val }))}>
                <Area
                  type="monotone"
                  dataKey="value"
                  stroke={getStatusColor(status)}
                  fill={alpha(getStatusColor(status), 0.2)}
                  strokeWidth={1}
                />
              </AreaChart>
            </ResponsiveContainer>
          </Box>
        )}
      </CardContent>
    </Card>
  )

  if (compact) {
    if (!currentVitals) return null

    return (
      <Card className={className}>
        <CardContent sx={{ p: 2 }}>
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
            <Typography variant="h6" fontWeight={600}>
              Vital Signs
            </Typography>
            <Box display="flex" alignItems="center" gap={1}>
              <Typography variant="caption" color="textSecondary">
                Updated: {format(lastUpdate, 'HH:mm')}
              </Typography>
              {realTime && (
                <Box
                  sx={{
                    width: 8,
                    height: 8,
                    borderRadius: '50%',
                    backgroundColor: theme.palette.success.main,
                    animation: 'pulse 2s infinite',
                  }}
                />
              )}
            </Box>
          </Box>

          <Grid container spacing={2}>
            {currentVitals.heartRate && (
              <Grid xs={6} sm={3}>
                <VitalCard
                  title="Heart Rate"
                  value={currentVitals.heartRate}
                  status={getVitalStatus('heartRate', currentVitals.heartRate)}
                  unit={vitalRanges.heartRate.unit}
                  icon={<Favorite />}
                />
              </Grid>
            )}
            {currentVitals.temperature && (
              <Grid xs={6} sm={3}>
                <VitalCard
                  title="Temperature"
                  value={currentVitals.temperature}
                  status={getVitalStatus('temperature', currentVitals.temperature)}
                  unit={vitalRanges.temperature.unit}
                  icon={<Thermostat />}
                />
              </Grid>
            )}
            {currentVitals.oxygenSaturation && (
              <Grid xs={6} sm={3}>
                <VitalCard
                  title="O2 Saturation"
                  value={currentVitals.oxygenSaturation}
                  status={getVitalStatus('oxygenSaturation', currentVitals.oxygenSaturation)}
                  unit={vitalRanges.oxygenSaturation.unit}
                  icon={<WaterDrop />}
                />
              </Grid>
            )}
            {currentVitals.bloodPressure && (
              <Grid xs={6} sm={3}>
                <VitalCard
                  title="Blood Pressure"
                  value={`${currentVitals.bloodPressure.systolic}/${currentVitals.bloodPressure.diastolic}`}
                  status={getVitalStatus('bloodPressure', currentVitals.bloodPressure.systolic)}
                  unit={vitalRanges.bloodPressure.unit}
                  icon={<Speed />}
                />
              </Grid>
            )}
          </Grid>

          {alerts.filter(alert => !alert.acknowledged).length > 0 && (
            <Alert severity="error" sx={{ mt: 2 }}>
              {alerts.filter(alert => !alert.acknowledged).length} active alert(s)
            </Alert>
          )}
        </CardContent>
      </Card>
    )
  }

  return (
    <Paper className={className} sx={{ p: 3 }}>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Box>
          <Typography variant="h4" fontWeight={600}>
            Vital Signs Monitor
          </Typography>
          <Typography variant="subtitle1" color="textSecondary">
            {patientName} • Patient ID: {patientId}
          </Typography>
        </Box>

        <Box display="flex" alignItems="center" gap={2}>
          <Box display="flex" alignItems="center" gap={1}>
            <Typography variant="caption" color="textSecondary">
              Last Updated: {format(lastUpdate, 'MMM d, yyyy HH:mm:ss')}
            </Typography>
            {realTime && (
              <Box
                sx={{
                  width: 12,
                  height: 12,
                  borderRadius: '50%',
                  backgroundColor: theme.palette.success.main,
                  animation: 'pulse 2s infinite',
                }}
              />
            )}
          </Box>

          <Tooltip title="Refresh">
            <IconButton onClick={() => onVitalSignsUpdate(currentVitals || {} as VitalSigns)}>
              <Refresh />
            </IconButton>
          </Tooltip>

          <Tooltip title="Manual Entry">
            <IconButton onClick={() => setIsEditing(true)}>
              <Edit />
            </IconButton>
          </Tooltip>

          <Badge badgeContent={alerts.filter(alert => !alert.acknowledged).length} color="error">
            <Tooltip title="View History">
              <IconButton>
                <History />
              </IconButton>
            </Tooltip>
          </Badge>
        </Box>
      </Box>

      {/* Active Alerts */}
      {alerts.filter(alert => !alert.acknowledged).length > 0 && (
        <Box sx={{ mb: 3 }}>
          <Typography variant="h6" fontWeight={600} mb={2}>
            Active Alerts
          </Typography>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
            {alerts
              .filter(alert => !alert.acknowledged)
              .map(alert => (
                <Alert
                  key={alert.id}
                  severity={alert.type === 'critical' ? 'error' : 'warning'}
                  action={
                    <Button
                      color="inherit"
                      size="small"
                      onClick={() => onAlertAcknowledge(alert.id)}
                    >
                      Acknowledge
                    </Button>
                  }
                >
                  <Box>
                    <Typography variant="subtitle2" fontWeight={600}>
                      {alert.message}
                    </Typography>
                    <Typography variant="caption" color="textSecondary">
                      {format(new Date(alert.timestamp), 'MMM d, yyyy HH:mm:ss')}
                    </Typography>
                  </Box>
                </Alert>
              ))}
          </Box>
        </Box>
      )}

      {/* Current Vital Signs */}
      {currentVitals && (
        <Box sx={{ mb: 4 }}>
          <Typography variant="h6" fontWeight={600} mb={2}>
            Current Vital Signs
          </Typography>
          <Grid container spacing={3}>
            {currentVitals.heartRate && (
              <Grid xs={12} sm={6} md={3}>
                <VitalCard
                  title="Heart Rate"
                  value={currentVitals.heartRate}
                  status={getVitalStatus('heartRate', currentVitals.heartRate)}
                  unit={vitalRanges.heartRate.unit}
                  icon={<Favorite />}
                />
              </Grid>
            )}
            {currentVitals.temperature && (
              <Grid xs={12} sm={6} md={3}>
                <VitalCard
                  title="Temperature"
                  value={currentVitals.temperature}
                  status={getVitalStatus('temperature', currentVitals.temperature)}
                  unit={vitalRanges.temperature.unit}
                  icon={<Thermostat />}
                />
              </Grid>
            )}
            {currentVitals.oxygenSaturation && (
              <Grid xs={12} sm={6} md={3}>
                <VitalCard
                  title="O2 Saturation"
                  value={currentVitals.oxygenSaturation}
                  status={getVitalStatus('oxygenSaturation', currentVitals.oxygenSaturation)}
                  unit={vitalRanges.oxygenSaturation.unit}
                  icon={<WaterDrop />}
                />
              </Grid>
            )}
            {currentVitals.bloodPressure && (
              <Grid xs={12} sm={6} md={3}>
                <VitalCard
                  title="Blood Pressure"
                  value={`${currentVitals.bloodPressure.systolic}/${currentVitals.bloodPressure.diastolic}`}
                  status={getVitalStatus('bloodPressure', currentVitals.bloodPressure.systolic)}
                  unit={vitalRanges.bloodPressure.unit}
                  icon={<Speed />}
                />
              </Grid>
            )}
            {currentVitals.respiratoryRate && (
              <Grid xs={12} sm={6} md={3}>
                <VitalCard
                  title="Respiratory Rate"
                  value={currentVitals.respiratoryRate}
                  status={getVitalStatus('respiratoryRate', currentVitals.respiratoryRate)}
                  unit={vitalRanges.respiratoryRate.unit}
                  icon={<MonitorWeight />}
                />
              </Grid>
            )}
            {currentVitals.bloodSugar && (
              <Grid xs={12} sm={6} md={3}>
                <VitalCard
                  title="Blood Sugar"
                  value={currentVitals.bloodSugar}
                  status={getVitalStatus('bloodSugar', currentVitals.bloodSugar)}
                  unit={vitalRanges.bloodSugar.unit}
                  icon={<TrendingUp />}
                />
              </Grid>
            )}
          </Grid>
        </Box>
      )}

      {/* Historical Trends */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h6" fontWeight={600} mb={2}>
          24-Hour Trends
        </Typography>
        <Grid container spacing={3}>
          <Grid xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="subtitle2" fontWeight={600} mb={2}>
                  Heart Rate & Temperature
                </Typography>
                <ResponsiveContainer width="100%" height={200}>
                  <LineChart data={historicalData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="time" />
                    <YAxis yAxisId="left" />
                    <YAxis yAxisId="right" orientation="right" />
                    <Tooltip />
                    <Legend />
                    <Line yAxisId="left" type="monotone" dataKey="heartRate" stroke="#ef4444" name="Heart Rate (bpm)" />
                    <Line yAxisId="right" type="monotone" dataKey="temperature" stroke="#f59e0b" name="Temperature (°C)" />
                  </LineChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </Grid>
          <Grid xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="subtitle2" fontWeight={600} mb={2}>
                  Oxygen Saturation & Blood Pressure
                </Typography>
                <ResponsiveContainer width="100%" height={200}>
                  <LineChart data={historicalData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="time" />
                    <YAxis yAxisId="left" />
                    <YAxis yAxisId="right" orientation="right" />
                    <Tooltip />
                    <Legend />
                    <Line yAxisId="left" type="monotone" dataKey="oxygenSaturation" stroke="#3b82f6" name="O2 Saturation (%)" />
                    <Line yAxisId="right" type="monotone" dataKey="bloodPressure" stroke="#8b5cf6" name="Blood Pressure (mmHg)" />
                  </LineChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Box>

      {/* Manual Entry Dialog */}
      <Dialog open={isEditing} onClose={() => setIsEditing(false)} maxWidth="md" fullWidth>
        <DialogTitle>Manual Vital Signs Entry</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid xs={12} sm={6}>
              <TextField
                label="Temperature (°C)"
                type="number"
                value={manualEntryVitals.temperature || ''}
                onChange={(e) => setManualEntryVitals(prev => ({ ...prev, temperature: parseFloat(e.target.value) }))}
                fullWidth
              />
            </Grid>
            <Grid xs={12} sm={6}>
              <TextField
                label="Heart Rate (bpm)"
                type="number"
                value={manualEntryVitals.heartRate || ''}
                onChange={(e) => setManualEntryVitals(prev => ({ ...prev, heartRate: parseFloat(e.target.value) }))}
                fullWidth
              />
            </Grid>
            <Grid xs={12} sm={6}>
              <TextField
                label="Oxygen Saturation (%)"
                type="number"
                value={manualEntryVitals.oxygenSaturation || ''}
                onChange={(e) => setManualEntryVitals(prev => ({ ...prev, oxygenSaturation: parseFloat(e.target.value) }))}
                fullWidth
              />
            </Grid>
            <Grid xs={12} sm={3}>
              <TextField
                label="Systolic BP"
                type="number"
                value={manualEntryVitals.bloodPressure?.systolic || ''}
                onChange={(e) => setManualEntryVitals(prev => ({
                  ...prev,
                  bloodPressure: { ...prev.bloodPressure, systolic: parseInt(e.target.value) }
                }))}
                fullWidth
              />
            </Grid>
            <Grid xs={12} sm={3}>
              <TextField
                label="Diastolic BP"
                type="number"
                value={manualEntryVitals.bloodPressure?.diastolic || ''}
                onChange={(e) => setManualEntryVitals(prev => ({
                  ...prev,
                  bloodPressure: { ...prev.bloodPressure, diastolic: parseInt(e.target.value) }
                }))}
                fullWidth
              />
            </Grid>
            <Grid xs={12} sm={6}>
              <TextField
                label="Respiratory Rate"
                type="number"
                value={manualEntryVitals.respiratoryRate || ''}
                onChange={(e) => setManualEntryVitals(prev => ({ ...prev, respiratoryRate: parseFloat(e.target.value) }))}
                fullWidth
              />
            </Grid>
            <Grid xs={12} sm={6}>
              <TextField
                label="Blood Sugar (mg/dL)"
                type="number"
                value={manualEntryVitals.bloodSugar || ''}
                onChange={(e) => setManualEntryVitals(prev => ({ ...prev, bloodSugar: parseFloat(e.target.value) }))}
                fullWidth
              />
            </Grid>
            <Grid xs={12}>
              <TextField
                label="Notes"
                multiline
                rows={3}
                value={manualEntryVitals.notes || ''}
                onChange={(e) => setManualEntryVitals(prev => ({ ...prev, notes: e.target.value }))}
                fullWidth
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setIsEditing(false)}>Cancel</Button>
          <Button
            onClick={() => {
              onManualEntry({
                ...manualEntryVitals,
                timestamp: new Date(),
                recordedBy: 'Manual Entry',
              } as VitalSigns)
              setIsEditing(false)
              setManualEntryVitals({})
            }}
            variant="contained"
          >
            Save Vital Signs
          </Button>
        </DialogActions>
      </Dialog>

      {/* Add CSS animation for real-time indicator */}
      <style>{`
        @keyframes pulse {
          0% {
            box-shadow: 0 0 0 0 rgba(34, 197, 94, 0.7);
          }
          70% {
            box-shadow: 0 0 0 10px rgba(34, 197, 94, 0);
          }
          100% {
            box-shadow: 0 0 0 0 rgba(34, 197, 94, 0);
          }
        }
      `}</style>
    </Paper>
  )
}

export default VitalSignsMonitor