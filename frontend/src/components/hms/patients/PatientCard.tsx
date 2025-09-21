import React from 'react'
import {
  Card,
  CardContent,
  CardActions,
  Typography,
  Box,
  Avatar,
  Chip,
  Button,
  IconButton,
  useTheme,
} from '@mui/material'
import {
  Person as PersonIcon,
  Phone as PhoneIcon,
  Email as EmailIcon,
  LocationOn as LocationIcon,
  MedicalServices as MedicalIcon,
  Edit as EditIcon,
  Visibility as ViewIcon,
} from '@mui/icons-material'
import { useTranslation } from 'react-i18next'
import { Patient } from '../../../store/slices/patientsSlice'

interface PatientCardProps {
  patient: Patient
  onEdit?: (patient: Patient) => void
  onView?: (patient: Patient) => void
  compact?: boolean
}

const PatientCard: React.FC<PatientCardProps> = ({
  patient,
  onEdit,
  onView,
  compact = false,
}) => {
  const { t } = useTranslation()
  const theme = useTheme()

  const getGenderColor = (gender: string) => {
    switch (gender) {
      case 'M':
        return theme.palette.primary.main
      case 'F':
        return theme.palette.secondary.main
      default:
        return theme.palette.info.main
    }
  }

  const getGenderText = (gender: string) => {
    switch (gender) {
      case 'M':
        return t('patients.male')
      case 'F':
        return t('patients.female')
      default:
        return t('patients.other')
    }
  }

  const calculateAge = (dateOfBirth: string) => {
    const birthDate = new Date(dateOfBirth)
    const today = new Date()
    let age = today.getFullYear() - birthDate.getFullYear()
    const monthDiff = today.getMonth() - birthDate.getMonth()

    if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birthDate.getDate())) {
      age--
    }

    return age
  }

  const getInitials = (firstName: string, lastName: string) => {
    return `${firstName?.[0] || ''}${lastName?.[0] || ''}`.toUpperCase()
  }

  if (compact) {
    return (
      <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
        <CardContent sx={{ flexGrow: 1, pb: 1 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
            <Avatar sx={{ bgcolor: getGenderColor(patient.gender), mr: 2 }}>
              {getInitials(patient.firstName, patient.lastName)}
            </Avatar>
            <Box>
              <Typography variant="h6" component="div">
                {patient.firstName} {patient.lastName}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {t('patients.medicalRecordNumber')}: {patient.medicalRecordNumber}
              </Typography>
            </Box>
          </Box>

          <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mb: 2 }}>
            <Chip
              size="small"
              label={getGenderText(patient.gender)}
              sx={{ bgcolor: getGenderColor(patient.gender), color: 'white' }}
            />
            <Chip
              size="small"
              label={`${calculateAge(patient.dateOfBirth)} years`}
              variant="outlined"
            />
            <Chip
              size="small"
              label={patient.bloodType}
              variant="outlined"
            />
          </Box>

          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
              <PhoneIcon fontSize="small" color="action" />
              <Typography variant="body2" color="text.secondary">
                {patient.phone}
              </Typography>
            </Box>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <EmailIcon fontSize="small" color="action" />
              <Typography variant="body2" color="text.secondary">
                {patient.email}
              </Typography>
            </Box>
        </CardContent>

        <CardActions sx={{ justifyContent: 'flex-end', pt: 1 }}>
          {onView && (
            <IconButton size="small" onClick={() => onView(patient)}>
              <ViewIcon />
            </IconButton>
          )}
          {onEdit && (
            <IconButton size="small" onClick={() => onEdit(patient)}>
              <EditIcon />
            </IconButton>
          )}
        </CardActions>
      </Card>
    )
  }

  return (
    <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <CardContent sx={{ flexGrow: 1 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
          <Avatar
            sx={{
              width: 56,
              height: 56,
              bgcolor: getGenderColor(patient.gender),
              mr: 2,
            }}
          >
            {getInitials(patient.firstName, patient.lastName)}
          </Avatar>
          <Box>
            <Typography variant="h5" component="div">
              {patient.firstName} {patient.lastName}
            </Typography>
            <Typography variant="body1" color="text.secondary">
              {t('patients.medicalRecordNumber')}: {patient.medicalRecordNumber}
            </Typography>
          </Box>
        </Box>

        <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mb: 3 }}>
          <Chip
            label={getGenderText(patient.gender)}
            sx={{ bgcolor: getGenderColor(patient.gender), color: 'white' }}
          />
          <Chip label={`${calculateAge(patient.dateOfBirth)} years`} variant="outlined" />
          <Chip label={patient.bloodType} variant="outlined" />
          <Chip
            label={t('common.active')}
            color="success"
            variant="outlined"
          />
        </Box>

        <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 2, mb: 3 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <PhoneIcon fontSize="small" color="action" />
            <Typography variant="body2">{patient.phone}</Typography>
          </Box>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <EmailIcon fontSize="small" color="action" />
            <Typography variant="body2">{patient.email}</Typography>
          </Box>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, gridColumn: 'span 2' }}>
            <LocationOn fontSize="small" color="action" />
            <Typography variant="body2">{patient.address}</Typography>
          </Box>
        </Box>

        {patient.allergies && patient.allergies.length > 0 && (
          <Box sx={{ mb: 2 }}>
            <Typography variant="subtitle2" color="text.secondary" gutterBottom>
              {t('patients.allergies')}:
            </Typography>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
              {patient.allergies.slice(0, 3).map((allergy, index) => (
                <Chip
                  key={index}
                  label={allergy}
                  size="small"
                  color="error"
                  variant="outlined"
                />
              ))}
              {patient.allergies.length > 3 && (
                <Chip
                  label={`+${patient.allergies.length - 3} more`}
                  size="small"
                  variant="outlined"
                />
              )}
            </Box>
          </Box>
        )}

        {patient.emergencyContact && (
          <Box>
            <Typography variant="subtitle2" color="text.secondary" gutterBottom>
              {t('patients.emergencyContact')}:
            </Typography>
            <Typography variant="body2">
              {patient.emergencyContact.name} - {patient.emergencyContact.phone}
            </Typography>
          </Box>
        )}
      </CardContent>

      <CardActions sx={{ justifyContent: 'flex-end', pt: 1 }}>
        {onView && (
          <Button
            size="small"
            startIcon={<ViewIcon />}
            onClick={() => onView(patient)}
          >
            {t('common.view')}
          </Button>
        )}
        {onEdit && (
          <Button
            size="small"
            startIcon={<EditIcon />}
            onClick={() => onEdit(patient)}
          >
            {t('common.edit')}
          </Button>
        )}
      </CardActions>
    </Card>
  )
}

export default PatientCard