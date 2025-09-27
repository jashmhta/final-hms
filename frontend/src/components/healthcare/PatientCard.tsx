import React, { useMemo, useCallback } from 'react'
import {
  Card,
  CardContent,
  CardActions,
  Typography,
  Chip,
  IconButton,
  Box,
  Avatar,
  Badge,
  Tooltip,
  useTheme,
  alpha,
} from '@mui/material'
import {
  Person,
  Phone,
  Email,
  CalendarToday,
  LocalHospital,
  Favorite,
  Warning,
  CheckCircle,
  Emergency,
  Male,
  Female,
  Transgender,
} from '@mui/icons-material'
import { format } from 'date-fns'

export interface PatientData {
  id: string
  firstName: string
  lastName: string
  dateOfBirth: string
  gender: 'male' | 'female' | 'other'
  patientId: string
  room?: string
  bed?: string
  admissionDate?: string
  condition: 'stable' | 'critical' | 'serious' | 'fair' | 'good'
  primaryPhysician: string
  allergies: string[]
  medications: number
  lastVitals?: {
    temperature?: number
    bloodPressure?: string
    heartRate?: number
    oxygenSaturation?: number
  }
  emergencyContact?: {
    name: string
    phone: string
    relationship: string
  }
  avatar?: string
  isEmergency?: boolean
  status: 'admitted' | 'outpatient' | 'discharged' | 'emergency'
}

interface PatientCardProps {
  patient: PatientData
  onViewDetails: (patientId: string) => void
  onContact?: (patientId: string) => void
  onEmergencyAlert?: (patientId: string) => void
  compact?: boolean
  showVitals?: boolean
  className?: string
}

const PatientCard: React.FC<PatientCardProps> = React.memo(({
  patient,
  onViewDetails,
  onContact,
  onEmergencyAlert,
  compact = false,
  showVitals = false,
  className,
}) => {
  const theme = useTheme()

  // Memoized computed values
  const getGenderIcon = useCallback((gender: string) => {
    switch (gender) {
      case 'male':
        return <Male sx={{ color: theme.palette.info.main }} />
      case 'female':
        return <Female sx={{ color: theme.palette.secondary.main }} />
      case 'other':
        return <Transgender sx={{ color: theme.palette.warning.main }} />
      default:
        return <Person />
    }
  }, [theme])

  const getConditionColor = useCallback((condition: string) => {
    switch (condition) {
      case 'critical':
        return theme.palette.error.main
      case 'serious':
        return theme.palette.warning.main
      case 'fair':
        return theme.palette.info.main
      case 'good':
        return theme.palette.success.main
      case 'stable':
        return theme.palette.primary.main
      default:
        return theme.palette.grey[500]
    }
  }, [theme])

  const getStatusColor = useCallback((status: string) => {
    switch (status) {
      case 'admitted':
        return theme.palette.success.main
      case 'emergency':
        return theme.palette.error.main
      case 'outpatient':
        return theme.palette.info.main
      case 'discharged':
        return theme.palette.grey[500]
      default:
        return theme.palette.grey[500]
    }
  }, [theme])

  const calculateAge = useCallback((dateOfBirth: string) => {
    const birthDate = new Date(dateOfBirth)
    const today = new Date()
    let age = today.getFullYear() - birthDate.getFullYear()
    const monthDiff = today.getMonth() - birthDate.getMonth()

    if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birthDate.getDate())) {
      age--
    }

    return age
  }, [])

  const formatVitalSigns = useCallback((vitals: PatientData['lastVitals']) => {
    if (!vitals) return null

    const vitalEntries = []
    if (vitals.temperature) {
      vitalEntries.push(`🌡️ ${vitals.temperature}°F`)
    }
    if (vitals.bloodPressure) {
      vitalEntries.push(`💨 ${vitals.bloodPressure}`)
    }
    if (vitals.heartRate) {
      vitalEntries.push(`❤️ ${vitals.heartRate} bpm`)
    }
    if (vitals.oxygenSaturation) {
      vitalEntries.push(`💧 ${vitals.oxygenSaturation}%`)
    }

    return vitalEntries.join(' • ')
  }, [])

  // Memoize computed values
  const patientAge = useMemo(() => calculateAge(patient.dateOfBirth), [patient.dateOfBirth, calculateAge])
  const conditionColor = useMemo(() => getConditionColor(patient.condition), [patient.condition, getConditionColor])
  const statusColor = useMemo(() => getStatusColor(patient.status), [patient.status, getStatusColor])
  const genderIcon = useMemo(() => getGenderIcon(patient.gender), [patient.gender, getGenderIcon])
  const formattedVitals = useMemo(() => formatVitalSigns(patient.lastVitals), [patient.lastVitals, formatVitalSigns])
  const formattedBirthDate = useMemo(() => format(new Date(patient.dateOfBirth), 'MMM dd, yyyy'), [patient.dateOfBirth])

  if (compact) {
    return (
      <Card
        className={className}
        sx={{
          mb: 1,
          border: patient.isEmergency
            ? `2px solid ${theme.palette.error.main}`
            : `1px solid ${theme.palette.divider}`,
          '&:hover': {
            boxShadow: theme.shadows[4],
            transform: 'translateY(-1px)',
          },
          transition: 'all 0.2s ease-in-out',
        }}
      >
        <CardContent sx={{ py: 2, '&:last-child': { pb: 2 } }}>
          <Box display="flex" alignItems="center" gap={2}>
            <Badge
              overlap="circular"
              anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
              badgeContent={
                patient.isEmergency ? (
                  <Emergency sx={{ fontSize: 16, color: theme.palette.error.main }} />
                ) : null
              }
            >
              <Avatar
                src={patient.avatar}
                sx={{
                  width: 40,
                  height: 40,
                  border: `2px solid ${getConditionColor(patient.condition)}`,
                }}
              >
                {patient.firstName.charAt(0)}
              </Avatar>
            </Badge>

            <Box flexGrow={1}>
              <Typography variant="subtitle2" fontWeight={600}>
                {patient.firstName} {patient.lastName}
              </Typography>
              <Box display="flex" alignItems="center" gap={1} mt={0.5}>
                {getGenderIcon(patient.gender)}
                <Typography variant="caption" color="textSecondary">
                  {patientAge}y • {patient.patientId}
                </Typography>
              </Box>
            </Box>

            <Box display="flex" flexDirection="column" alignItems="flex-end" gap={0.5}>
              <Chip
                label={patient.condition}
                size="small"
                sx={{
                  backgroundColor: alpha(conditionColor, 0.1),
                  color: conditionColor,
                  fontWeight: 600,
                  fontSize: '0.75rem',
                  height: 24,
                }}
              />
              <Chip
                label={patient.status}
                size="small"
                variant="outlined"
                sx={{
                  borderColor: statusColor,
                  color: statusColor,
                  fontSize: '0.7rem',
                  height: 20,
                }}
              />
            </Box>
          </Box>

          {showVitals && patient.lastVitals && (
            <Box mt={2} pt={2} borderTop={`1px solid ${theme.palette.divider}`}>
              <Typography variant="caption" color="textSecondary" sx={{ display: 'block', mb: 0.5 }}>
                Last Vitals:
              </Typography>
              <Typography variant="body2" sx={{ fontSize: '0.8rem' }}>
                {formattedVitals}
              </Typography>
            </Box>
          )}
        </CardContent>

        <CardActions sx={{ px: 2, py: 1, justifyContent: 'flex-end' }}>
          {onContact && (
            <Tooltip title="Contact Patient">
              <IconButton
                size="small"
                onClick={() => onContact(patient.id)}
                sx={{ color: theme.palette.info.main }}
              >
                <Phone fontSize="small" />
              </IconButton>
            </Tooltip>
          )}
          {onEmergencyAlert && (
            <Tooltip title="Emergency Alert">
              <IconButton
                size="small"
                onClick={() => onEmergencyAlert(patient.id)}
                sx={{ color: theme.palette.error.main }}
              >
                <Emergency fontSize="small" />
              </IconButton>
            </Tooltip>
          )}
          <Tooltip title="View Details">
            <IconButton
              size="small"
              onClick={() => onViewDetails(patient.id)}
              sx={{ color: theme.palette.primary.main }}
            >
              <Person fontSize="small" />
            </IconButton>
          </Tooltip>
        </CardActions>
      </Card>
    )
  }

  return (
    <Card
      className={className}
      sx={{
        border: patient.isEmergency
          ? `2px solid ${theme.palette.error.main}`
          : `1px solid ${theme.palette.divider}`,
        '&:hover': {
          boxShadow: theme.shadows[4],
          transform: 'translateY(-2px)',
        },
        transition: 'all 0.2s ease-in-out',
      }}
    >
      <CardContent>
        <Box display="flex" alignItems="flex-start" gap={3} mb={2}>
          <Badge
            overlap="circular"
            anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
            badgeContent={
              patient.isEmergency ? (
                <Emergency
                  sx={{
                    fontSize: 20,
                    color: theme.palette.error.main,
                    backgroundColor: theme.palette.background.paper,
                    borderRadius: '50%',
                    border: `2px solid ${theme.palette.background.paper}`,
                  }}
                />
              ) : null
            }
          >
            <Avatar
              src={patient.avatar}
              sx={{
                width: 64,
                height: 64,
                border: `3px solid ${conditionColor}`,
              }}
            >
              {patient.firstName.charAt(0)}
            </Avatar>
          </Badge>

          <Box flexGrow={1}>
            <Box display="flex" alignItems="center" gap={2} mb={1}>
              <Typography variant="h6" fontWeight={600}>
                {patient.firstName} {patient.lastName}
              </Typography>
              <Chip
                label={patient.patientId}
                size="small"
                variant="outlined"
                sx={{ fontSize: '0.75rem' }}
              />
            </Box>

            <Box display="flex" alignItems="center" gap={3} flexWrap="wrap">
              <Box display="flex" alignItems="center" gap={1}>
                {getGenderIcon(patient.gender)}
                <Typography variant="body2" color="textSecondary">
                  {patientAge} years
                </Typography>
              </Box>

              <Box display="flex" alignItems="center" gap={1}>
                <CalendarToday fontSize="small" />
                <Typography variant="body2" color="textSecondary">
                  {formattedBirthDate}
                </Typography>
              </Box>

              {patient.room && patient.bed && (
                <Box display="flex" alignItems="center" gap={1}>
                  <LocalHospital fontSize="small" />
                  <Typography variant="body2" color="textSecondary">
                    Room {patient.room}, Bed {patient.bed}
                  </Typography>
                </Box>
              )}
            </Box>

            <Box display="flex" alignItems="center" gap={2} mt={2}>
              <Chip
                label={patient.condition}
                sx={{
                  backgroundColor: alpha(conditionColor, 0.1),
                  color: conditionColor,
                  fontWeight: 600,
                }}
              />
              <Chip
                label={patient.status}
                variant="outlined"
                sx={{
                  borderColor: statusColor,
                  color: statusColor,
                }}
              />
              {patient.allergies.length > 0 && (
                <Chip
                  icon={<Warning fontSize="small" />}
                  label={`${patient.allergies.length} Allergies`}
                  size="small"
                  color="warning"
                  variant="outlined"
                />
              )}
            </Box>
          </Box>
        </Box>

        <Box display="flex" justifyContent="space-between" alignItems="center" mt={2} pt={2}>
          <Box>
            <Typography variant="caption" color="textSecondary">
              Primary Physician: {patient.primaryPhysician}
            </Typography>
            <Typography variant="body2" color="textSecondary">
              {patient.medications} active medications
            </Typography>
          </Box>

          {showVitals && patient.lastVitals && (
            <Box textAlign="right">
              <Typography variant="caption" color="textSecondary">
                Last Vitals:
              </Typography>
              <Typography variant="body2" sx={{ fontSize: '0.8rem' }}>
                {formattedVitals}
              </Typography>
            </Box>
          )}
        </Box>

        {patient.emergencyContact && (
          <Box mt={2} pt={2} borderTop={`1px solid ${theme.palette.divider}`}>
            <Typography variant="caption" color="textSecondary" sx={{ display: 'block', mb: 0.5 }}>
              Emergency Contact:
            </Typography>
            <Typography variant="body2">
              {patient.emergencyContact.name} ({patient.emergencyContact.relationship})
            </Typography>
            <Typography variant="body2" color="textSecondary">
              {patient.emergencyContact.phone}
            </Typography>
          </Box>
        )}
      </CardContent>

      <CardActions sx={{ justifyContent: 'flex-end', p: 2 }}>
        {onContact && (
          <Tooltip title="Contact Patient">
            <IconButton onClick={() => onContact(patient.id)}>
              <Phone />
            </IconButton>
          </Tooltip>
        )}
        {onEmergencyAlert && (
          <Tooltip title="Emergency Alert">
            <IconButton
              onClick={() => onEmergencyAlert(patient.id)}
              sx={{ color: theme.palette.error.main }}
            >
              <Emergency />
            </IconButton>
          </Tooltip>
        )}
        <Tooltip title="View Details">
          <IconButton
            onClick={() => onViewDetails(patient.id)}
            sx={{ color: theme.palette.primary.main }}
          >
            <Person />
          </IconButton>
        </Tooltip>
      </CardActions>
    </Card>
  )
})

export default PatientCard;