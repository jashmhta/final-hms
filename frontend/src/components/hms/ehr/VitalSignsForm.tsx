import React, { useState } from 'react'
import {
  Box,
  Card,
  CardContent,
  CardHeader,
  Typography,
  TextField,
  Button,
  Grid,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Alert,
  useTheme,
  FormHelperText,
  InputAdornment,
} from '@mui/material'
import {
  Thermostat as TemperatureIcon,
  Favorite as HeartIcon,
  Air as RespiratoryIcon,
  WaterDrop as OxygenIcon,
  Straighten as HeightIcon,
  MonitorWeight as WeightIcon,
  Save as SaveIcon,
  Cancel as CancelIcon,
} from '@mui/icons-material'
import { useTranslation } from 'react-i18next'
import { VitalSigns } from '../../../store/slices/ehrSlice'
import { useForm, Controller } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import * as z from 'zod'

// Validation schema
const vitalSignsSchema = z.object({
  temperature: z.number().min(30).max(45, 'Temperature must be between 30-45°C'),
  bloodPressureSystolic: z.number().min(60).max(250),
  bloodPressureDiastolic: z.number().min(30).max(150),
  heartRate: z.number().min(30).max(220),
  respiratoryRate: z.number().min(8).max(40),
  oxygenSaturation: z.number().min(70).max(100),
  height: z.number().min(50).max(250).optional(),
  weight: z.number().min(1).max(500).optional(),
  notes: z.string().optional(),
}).refine(data => data.bloodPressureSystolic > data.bloodPressureDiastolic, {
  message: 'Systolic pressure must be greater than diastolic pressure',
  path: ['bloodPressureSystolic'],
})

type VitalSignsFormData = z.infer<typeof vitalSignsSchema>

interface VitalSignsFormProps {
  patientId: string
  onSave: (vitals: VitalSigns) => void
  onCancel?: () => void
  initialData?: Partial<VitalSigns>
}

const VitalSignsForm: React.FC<VitalSignsFormProps> = ({
  patientId,
  onSave,
  onCancel,
  initialData,
}) => {
  const { t } = useTranslation()
  const theme = useTheme()
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const {
    control,
    handleSubmit,
    formState: { errors },
    watch,
    setValue,
  } = useForm<VitalSignsFormData>({
    resolver: zodResolver(vitalSignsSchema),
    defaultValues: {
      temperature: initialData?.temperature || 37,
      bloodPressureSystolic: initialData?.bloodPressure?.systolic || 120,
      bloodPressureDiastolic: initialData?.bloodPressure?.diastolic || 80,
      heartRate: initialData?.heartRate || 72,
      respiratoryRate: initialData?.respiratoryRate || 16,
      oxygenSaturation: initialData?.oxygenSaturation || 98,
      height: initialData?.height,
      weight: initialData?.weight,
      notes: initialData?.notes || '',
    },
  })

  const height = watch('height')
  const weight = watch('weight')

  // Calculate BMI automatically
  const bmi = React.useMemo(() => {
    if (height && weight) {
      const heightInMeters = height / 100
      return weight / (heightInMeters * heightInMeters)
    }
    return null
  }, [height, weight])

  const getBMICategory = (bmi: number) => {
    if (bmi < 18.5) return { label: 'Underweight', color: theme.palette.info.main }
    if (bmi < 25) return { label: 'Normal', color: theme.palette.success.main }
    if (bmi < 30) return { label: 'Overweight', color: theme.palette.warning.main }
    return { label: 'Obese', color: theme.palette.error.main }
  }

  const getVitalStatus = (value: number, type: string) => {
    switch (type) {
      case 'temperature':
        if (value < 36) return { status: 'Low', color: theme.palette.info.main }
        if (value > 37.5) return { status: 'High', color: theme.palette.error.main }
        return { status: 'Normal', color: theme.palette.success.main }
      case 'heartRate':
        if (value < 60) return { status: 'Low', color: theme.palette.info.main }
        if (value > 100) return { status: 'High', color: theme.palette.warning.main }
        return { status: 'Normal', color: theme.palette.success.main }
      case 'oxygenSaturation':
        if (value < 95) return { status: 'Low', color: theme.palette.error.main }
        return { status: 'Normal', color: theme.palette.success.main }
      case 'bloodPressure':
        if (value < 90) return { status: 'Low', color: theme.palette.error.main }
        if (value > 140) return { status: 'High', color: theme.palette.error.main }
        return { status: 'Normal', color: theme.palette.success.main }
      default:
        return { status: 'Normal', color: theme.palette.success.main }
    }
  }

  const onSubmit = async (data: VitalSignsFormData) => {
    setIsSubmitting(true)
    setError(null)

    try {
      const vitalSigns: VitalSigns = {
        id: '',
        patientId,
        timestamp: new Date().toISOString(),
        temperature: data.temperature,
        bloodPressure: {
          systolic: data.bloodPressureSystolic,
          diastolic: data.bloodPressureDiastolic,
        },
        heartRate: data.heartRate,
        respiratoryRate: data.respiratoryRate,
        oxygenSaturation: data.oxygenSaturation,
        height: data.height,
        weight: data.weight,
        bmi: bmi || undefined,
        notes: data.notes,
      }

      await onSave(vitalSigns)
    } catch (err) {
      setError('Failed to save vital signs. Please try again.')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <Card sx={{ maxWidth: 800, mx: 'auto' }}>
      <CardHeader
        title={
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <FavoriteIcon color="primary" />
            <Typography variant="h6">Vital Signs Entry</Typography>
          </Box>
        }
        subheader="Enter patient vital signs measurements"
      />

      <CardContent>
        {error && (
          <Alert severity="error" sx={{ mb: 3 }}>
            {error}
          </Alert>
        )}

        <form onSubmit={handleSubmit(onSubmit)}>
          <Grid container spacing={3}>
            {/* Temperature */}
            <Grid item xs={12} sm={6} md={3}>
              <Controller
                name="temperature"
                control={control}
                render={({ field }) => (
                  <TextField
                    {...field}
                    fullWidth
                    label="Temperature (°C)"
                    type="number"
                    step="0.1"
                    error={!!errors.temperature}
                    helperText={errors.temperature?.message}
                    InputProps={{
                      startAdornment: (
                        <InputAdornment position="start">
                          <TemperatureIcon />
                        </InputAdornment>
                      ),
                    }}
                    inputProps={{
                      'aria-label': 'Temperature in Celsius',
                      step: '0.1',
                      min: '30',
                      max: '45',
                    }}
                  />
                )}
              />
              {field.value && (
                <FormHelperText>
                  Status:{' '}
                  <Typography
                    component="span"
                    color={getVitalStatus(field.value, 'temperature').color}
                  >
                    {getVitalStatus(field.value, 'temperature').status}
                  </Typography>
                </FormHelperText>
              )}
            </Grid>

            {/* Blood Pressure */}
            <Grid item xs={12} sm={6} md={3}>
              <Controller
                name="bloodPressureSystolic"
                control={control}
                render={({ field }) => (
                  <TextField
                    {...field}
                    fullWidth
                    label="BP Systolic"
                    type="number"
                    error={!!errors.bloodPressureSystolic}
                    helperText={errors.bloodPressureSystolic?.message}
                    inputProps={{
                      'aria-label': 'Blood pressure systolic',
                      min: '60',
                      max: '250',
                    }}
                  />
                )}
              />
            </Grid>

            <Grid item xs={12} sm={6} md={3}>
              <Controller
                name="bloodPressureDiastolic"
                control={control}
                render={({ field }) => (
                  <TextField
                    {...field}
                    fullWidth
                    label="BP Diastolic"
                    type="number"
                    error={!!errors.bloodPressureDiastolic}
                    helperText={errors.bloodPressureDiastolic?.message}
                    inputProps={{
                      'aria-label': 'Blood pressure diastolic',
                      min: '30',
                      max: '150',
                    }}
                  />
                )}
              />
            </Grid>

            {/* Heart Rate */}
            <Grid item xs={12} sm={6} md={3}>
              <Controller
                name="heartRate"
                control={control}
                render={({ field }) => (
                  <TextField
                    {...field}
                    fullWidth
                    label="Heart Rate (bpm)"
                    type="number"
                    error={!!errors.heartRate}
                    helperText={errors.heartRate?.message}
                    InputProps={{
                      startAdornment: (
                        <InputAdornment position="start">
                          <HeartIcon />
                        </InputAdornment>
                      ),
                    }}
                    inputProps={{
                      'aria-label': 'Heart rate in beats per minute',
                      min: '30',
                      max: '220',
                    }}
                  />
                )}
              />
            </Grid>

            {/* Respiratory Rate */}
            <Grid item xs={12} sm={6} md={3}>
              <Controller
                name="respiratoryRate"
                control={control}
                render={({ field }) => (
                  <TextField
                    {...field}
                    fullWidth
                    label="Resp. Rate (/min)"
                    type="number"
                    error={!!errors.respiratoryRate}
                    helperText={errors.respiratoryRate?.message}
                    InputProps={{
                      startAdornment: (
                        <InputAdornment position="start">
                          <RespiratoryIcon />
                        </InputAdornment>
                      ),
                    }}
                    inputProps={{
                      'aria-label': 'Respiratory rate per minute',
                      min: '8',
                      max: '40',
                    }}
                  />
                )}
              />
            </Grid>

            {/* Oxygen Saturation */}
            <Grid item xs={12} sm={6} md={3}>
              <Controller
                name="oxygenSaturation"
                control={control}
                render={({ field }) => (
                  <TextField
                    {...field}
                    fullWidth
                    label="O₂ Saturation (%)"
                    type="number"
                    error={!!errors.oxygenSaturation}
                    helperText={errors.oxygenSaturation?.message}
                    InputProps={{
                      startAdornment: (
                        <InputAdornment position="start">
                          <OxygenIcon />
                        </InputAdornment>
                      ),
                    }}
                    inputProps={{
                      'aria-label': 'Oxygen saturation percentage',
                      min: '70',
                      max: '100',
                    }}
                  />
                )}
              />
            </Grid>

            {/* Height */}
            <Grid item xs={12} sm={6} md={3}>
              <Controller
                name="height"
                control={control}
                render={({ field }) => (
                  <TextField
                    {...field}
                    fullWidth
                    label="Height (cm)"
                    type="number"
                    error={!!errors.height}
                    helperText={errors.height?.message}
                    InputProps={{
                      startAdornment: (
                        <InputAdornment position="start">
                          <HeightIcon />
                        </InputAdornment>
                      ),
                    }}
                    inputProps={{
                      'aria-label': 'Height in centimeters',
                      min: '50',
                      max: '250',
                    }}
                  />
                )}
              />
            </Grid>

            {/* Weight */}
            <Grid item xs={12} sm={6} md={3}>
              <Controller
                name="weight"
                control={control}
                render={({ field }) => (
                  <TextField
                    {...field}
                    fullWidth
                    label="Weight (kg)"
                    type="number"
                    error={!!errors.weight}
                    helperText={errors.weight?.message}
                    InputProps={{
                      startAdornment: (
                        <InputAdornment position="start">
                          <WeightIcon />
                        </InputAdornment>
                      ),
                    }}
                    inputProps={{
                      'aria-label': 'Weight in kilograms',
                      min: '1',
                      max: '500',
                    }}
                  />
                )}
              />
            </Grid>

            {/* BMI Display */}
            {bmi && (
              <Grid item xs={12} sm={6} md={3}>
                <Box
                  sx={{
                    p: 2,
                    border: '1px solid',
                    borderColor: 'divider',
                    borderRadius: 1,
                    textAlign: 'center',
                  }}
                >
                  <Typography variant="body2" color="text.secondary">
                    BMI
                  </Typography>
                  <Typography
                    variant="h6"
                    color={getBMICategory(bmi).color}
                    fontWeight="bold"
                  >
                    {bmi.toFixed(1)}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    {getBMICategory(bmi).label}
                  </Typography>
                </Box>
              </Grid>
            )}

            {/* Notes */}
            <Grid item xs={12}>
              <Controller
                name="notes"
                control={control}
                render={({ field }) => (
                  <TextField
                    {...field}
                    fullWidth
                    label="Notes"
                    multiline
                    rows={3}
                    error={!!errors.notes}
                    helperText={errors.notes?.message}
                    inputProps={{
                      'aria-label': 'Additional notes about vital signs',
                    }}
                  />
                )}
              />
            </Grid>

            {/* Action Buttons */}
            <Grid item xs={12}>
              <Box sx={{ display: 'flex', gap: 2, justifyContent: 'flex-end' }}>
                {onCancel && (
                  <Button
                    variant="outlined"
                    startIcon={<CancelIcon />}
                    onClick={onCancel}
                    disabled={isSubmitting}
                  >
                    Cancel
                  </Button>
                )}
                <Button
                  type="submit"
                  variant="contained"
                  startIcon={<SaveIcon />}
                  disabled={isSubmitting}
                >
                  {isSubmitting ? 'Saving...' : 'Save Vital Signs'}
                </Button>
              </Box>
            </Grid>
          </Grid>
        </form>
      </CardContent>
    </Card>
  )
}

export default VitalSignsForm