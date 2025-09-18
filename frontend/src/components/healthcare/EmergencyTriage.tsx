import React, { useState, useEffect } from 'react'
import {
  Box,
  Paper,
  Typography,
  Card,
  CardContent,
  Grid,
  Button,
  IconButton,
  Tooltip,
  Chip,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  List,
  ListItem,
  ListItemText,
  ListItemAvatar,
  Avatar,
  Badge,
  useTheme,
  alpha,
  Divider,
  LinearProgress,
  Tabs,
  Tab,
  Stepper,
  Step,
  StepLabel,
  StepContent,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Switch,
  FormControlLabel,
  RadioGroup,
  Radio,
  FormLabel,
} from '@mui/material'
import {
  Emergency,
  LocalHospital,
  MonitorHeart,
  Warning,
  Error,
  CheckCircle,
  Timer,
  Person,
  Phone,
  MapLocation,
  ExpandMore,
  DirectionsCar,
  Flight,
  PriorityHigh,
  AccessTime,
  Notes,
  Assessment,
  MedicalServices,
  Bloodtype,
  PregnantWoman,
  Accessibility,
  Psychology,
} from '@mui/icons-material'
import { format, addMinutes, subMinutes, differenceInMinutes } from 'date-fns'

export interface TriagePatient {
  id: string
  name: string
  age: number
  gender: string
  chiefComplaint: string
  triageLevel: 'resuscitation' | 'emergent' | 'urgent' | 'less-urgent' | 'non-urgent'
  arrivalTime: Date
  waitTime: number
  vitalSigns: {
    temperature?: number
    bloodPressure?: { systolic: number; diastolic: number }
    heartRate: number
    oxygenSaturation: number
    respiratoryRate?: number
    painLevel: number
    consciousness: string
  }
  symptoms: string[]
  allergies: string[]
  medications: string[]
  medicalHistory: string[]
  lastUpdate: Date
  assignedProvider?: string
  location?: string
  transportMethod: 'walk-in' | 'ambulance' | 'helicopter' | 'private-vehicle'
  estimatedTimeToProvider?: number
  isCritical: boolean
  requiresIsolation: boolean
  requiresSpecialist: boolean
  notes: string
}

export interface TriageAssessment {
  id: string
  patientId: string
  assessor: string
  assessmentTime: Date
  triageLevel: 'resuscitation' | 'emergent' | 'urgent' | 'less-urgent' | 'non-urgent'
  esiScore: 1 | 2 | 3 | 4 | 5
  criticalFindings: string[]
  disposition: 'ed' | 'fast-track' | 'waiting-room' | 'immediate' | 'resuscitation'
  estimatedTreatmentTime: number
  resourcesRequired: string[]
  specialConsiderations: string[]
}

interface EmergencyTriageProps {
  patients: TriagePatient[]
  assessments: TriageAssessment[]
  onPatientUpdate: (patient: TriagePatient) => void
  onAssessmentComplete: (assessment: TriageAssessment) => void
  onEmergencyAlert: (patientId: string) => void
  onProviderAssign: (patientId: string, providerId: string) => void
  className?: string
  compact?: boolean
}

const EmergencyTriage: React.FC<EmergencyTriageProps> = ({
  patients,
  assessments,
  onPatientUpdate,
  onAssessmentComplete,
  onEmergencyAlert,
  onProviderAssign,
  className,
  compact = false,
}) => {
  const theme = useTheme()
  const [selectedPatient, setSelectedPatient] = useState<TriagePatient | null>(null)
  const [isAssessing, setIsAssessing] = useState(false)
  const [currentAssessment, setCurrentAssessment] = useState<Partial<TriageAssessment>>({})
  const [activeTab, setActiveTab] = useState(0)
  const [filterLevel, setFilterLevel] = useState<string>('all')
  const [searchTerm, setSearchTerm] = useState('')

  const triageColors = {
    'resuscitation': theme.palette.error.main,
    'emergent': theme.palette.error.main,
    'urgent': theme.palette.warning.main,
    'less-urgent': theme.palette.info.main,
    'non-urgent': theme.palette.success.main,
  }

  const triageLabels = {
    'resuscitation': 'Resuscitation (ESI 1)',
    'emergent': 'Emergent (ESI 2)',
    'urgent': 'Urgent (ESI 3)',
    'less-urgent': 'Less Urgent (ESI 4)',
    'non-urgent': 'Non-Urgent (ESI 5)',
  }

  const triageDescriptions = {
    'resuscitation': 'Immediate life-threatening condition',
    'emergent': 'High-risk situation, confusion, severe pain/distress',
    'urgent': 'Condition could progress to serious if not treated',
    'less-urgent': 'Condition has potential to deteriorate',
    'non-urgent': 'Minor issues, time for treatment not critical',
  }

  const getFilteredPatients = () => {
    return patients
      .filter(patient => {
        const matchesFilter = filterLevel === 'all' || patient.triageLevel === filterLevel
        const matchesSearch = searchTerm === '' ||
          patient.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
          patient.chiefComplaint.toLowerCase().includes(searchTerm.toLowerCase())
        return matchesFilter && matchesSearch
      })
      .sort((a, b) => {
        const priorityOrder = ['resuscitation', 'emergent', 'urgent', 'less-urgent', 'non-urgent']
        return priorityOrder.indexOf(a.triageLevel) - priorityOrder.indexOf(b.triageLevel)
      })
  }

  const getWaitTimeColor = (waitTime: number) => {
    if (waitTime > 120) return theme.palette.error.main
    if (waitTime > 60) return theme.palette.warning.main
    if (waitTime > 30) return theme.palette.info.main
    return theme.palette.success.main
  }

  const getCriticalVitalStatus = (vitals: TriagePatient['vitalSigns']) => {
    const criticalValues = []

    if (vitals.temperature && (vitals.temperature < 35 || vitals.temperature > 39)) {
      criticalValues.push('Temperature')
    }
    if (vitals.bloodPressure &&
        (vitals.bloodPressure.systolic < 90 || vitals.bloodPressure.systolic > 180 ||
         vitals.bloodPressure.diastolic < 50 || vitals.bloodPressure.diastolic > 110)) {
      criticalValues.push('Blood Pressure')
    }
    if (vitals.heartRate && (vitals.heartRate < 50 || vitals.heartRate > 120)) {
      criticalValues.push('Heart Rate')
    }
    if (vitals.oxygenSaturation && vitals.oxygenSaturation < 95) {
      criticalValues.push('Oxygen Saturation')
    }
    if (vitals.painLevel && vitals.painLevel >= 7) {
      criticalValues.push('Severe Pain')
    }
    if (vitals.consciousness && vitals.consciousness !== 'alert') {
      criticalValues.push('Consciousness')
    }

    return criticalValues
  }

  const calculateESIScore = (patient: TriagePatient): 1 | 2 | 3 | 4 | 5 => {
    if (patient.triageLevel === 'resuscitation') return 1
    if (patient.isCritical) return 2
    if (patient.vitalSigns.heartRate > 120 || patient.vitalSigns.oxygenSaturation < 90) return 2
    if (patient.triageLevel === 'emergent') return 2
    if (patient.triageLevel === 'urgent') return 3
    if (patient.triageLevel === 'less-urgent') return 4
    return 5
  }

  const TriagePatientCard: React.FC<{
    patient: TriagePatient
    assessment?: TriageAssessment
  }> = ({ patient, assessment }) => {
    const waitTime = differenceInMinutes(new Date(), patient.arrivalTime)
    const criticalVitals = getCriticalVitalStatus(patient.vitalSigns)

    return (
      <Card
        sx={{
          border: `2px solid ${alpha(triageColors[patient.triageLevel], 0.5)}`,
          backgroundColor: alpha(triageColors[patient.triageLevel], 0.05),
          '&:hover': {
            boxShadow: theme.shadows[4],
          },
          transition: 'all 0.2s ease-in-out',
        }}
      >
        <CardContent sx={{ p: 3 }}>
          <Box display="flex" justifyContent="space-between" alignItems="start" mb={2}>
            <Box>
              <Typography variant="h6" fontWeight={600}>
                {patient.name}
              </Typography>
              <Typography variant="body2" color="textSecondary">
                {patient.age}y {patient.gender} • {patient.transportMethod.replace('-', ' ')}
              </Typography>
            </Box>
            <Box display="flex" alignItems="center" gap={1}>
              {patient.requiresIsolation && (
                <Tooltip title="Requires Isolation">
                  <Accessibility sx={{ color: theme.palette.warning.main }} />
                </Tooltip>
              )}
              {patient.requiresSpecialist && (
                <Tooltip title="Requires Specialist">
                  <MedicalServices sx={{ color: theme.palette.info.main }} />
                </Tooltip>
              )}
              <Chip
                label={triageLabels[patient.triageLevel]}
                size="small"
                sx={{
                  backgroundColor: alpha(triageColors[patient.triageLevel], 0.1),
                  color: triageColors[patient.triageLevel],
                  fontWeight: 600,
                }}
              />
            </Box>
          </Box>

          <Typography variant="body2" fontWeight={600} sx={{ mb: 1 }}>
            Chief Complaint: {patient.chiefComplaint}
          </Typography>

          <Grid container spacing={2} sx={{ mb: 2 }}>
            <Grid item xs={12} sm={6}>
              <Typography variant="caption" color="textSecondary">
                Arrival Time: {format(patient.arrivalTime, 'HH:mm')}
              </Typography>
              <Typography variant="caption" color={getWaitTimeColor(waitTime)} sx={{ display: 'block' }}>
                Wait Time: {waitTime} min
              </Typography>
            </Grid>
            <Grid item xs={12} sm={6}>
              <Typography variant="caption" color="textSecondary">
                Heart Rate: {patient.vitalSigns.heartRate} bpm
              </Typography>
              <Typography variant="caption" color="textSecondary" sx={{ display: 'block' }}>
                O2 Sat: {patient.vitalSigns.oxygenSaturation}%
              </Typography>
            </Grid>
          </Grid>

          {criticalVitals.length > 0 && (
            <Alert severity="error" sx={{ mb: 2 }}>
              <Typography variant="caption" fontWeight={600}>
                Critical Findings: {criticalVitals.join(', ')}
              </Typography>
            </Alert>
          )}

          <Box display="flex" alignItems="center" gap={1} sx={{ flexWrap: 'wrap' }}>
            <Typography variant="caption" fontWeight={600} color="textSecondary">
              Pain Level:
            </Typography>
            <LinearProgress
              variant="determinate"
              value={(patient.vitalSigns.painLevel / 10) * 100}
              sx={{
                width: 60,
                height: 6,
                borderRadius: 3,
                backgroundColor: alpha(theme.palette.error.main, 0.1),
                '& .MuiLinearProgress-bar': {
                  backgroundColor: patient.vitalSigns.painLevel >= 7 ? theme.palette.error.main :
                                  patient.vitalSigns.painLevel >= 4 ? theme.palette.warning.main :
                                  theme.palette.success.main,
                },
              }}
            />
            <Typography variant="caption" color="textSecondary">
              {patient.vitalSigns.painLevel}/10
            </Typography>
          </Box>

          <Box display="flex" justifyContent="space-between" alignItems="center" mt={2}>
            <Typography variant="caption" color="textSecondary">
              {patient.symptoms.length} symptoms • {patient.allergies.length} allergies
            </Typography>
            <Box display="flex" gap={1}>
              <Tooltip title="View Details">
                <IconButton
                  size="small"
                  onClick={() => setSelectedPatient(patient)}
                >
                  <Person />
                </IconButton>
              </Tooltip>
              <Tooltip title="Quick Assessment">
                <IconButton
                  size="small"
                  onClick={() => {
                    setSelectedPatient(patient)
                    setIsAssessing(true)
                  }}
                  sx={{ color: theme.palette.primary.main }}
                >
                  <Assessment />
                </IconButton>
              </Tooltip>
              {patient.isCritical && (
                <Tooltip title="Emergency Alert">
                  <IconButton
                    size="small"
                    onClick={() => onEmergencyAlert(patient.id)}
                    sx={{ color: theme.palette.error.main }}
                  >
                    <Emergency />
                  </IconButton>
                </Tooltip>
              )}
            </Box>
          </Box>
        </CardContent>
      </Card>
    )
  }

  if (compact) {
    const criticalPatients = patients.filter(p => p.triageLevel === 'resuscitation' || p.triageLevel === 'emergent')
    const totalWaitTime = patients.reduce((sum, p) => sum + differenceInMinutes(new Date(), p.arrivalTime), 0)
    const avgWaitTime = patients.length > 0 ? Math.round(totalWaitTime / patients.length) : 0

    return (
      <Card className={className}>
        <CardContent sx={{ p: 2 }}>
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
            <Typography variant="h6" fontWeight={600}>
              Emergency Triage
            </Typography>
            <Badge badgeContent={criticalPatients.length} color="error">
              <Emergency />
            </Badge>
          </Box>

          <Grid container spacing={2}>
            <Grid item xs={6}>
              <Box textAlign="center">
                <Typography variant="h4" fontWeight={600} color={theme.palette.primary.main}>
                  {patients.length}
                </Typography>
                <Typography variant="caption" color="textSecondary">
                  Total Patients
                </Typography>
              </Box>
            </Grid>
            <Grid item xs={6}>
              <Box textAlign="center">
                <Typography variant="h4" fontWeight={600} color={criticalPatients.length > 0 ? theme.palette.error.main : theme.palette.success.main}>
                  {avgWaitTime}m
                </Typography>
                <Typography variant="caption" color="textSecondary">
                  Avg Wait Time
                </Typography>
              </Box>
            </Grid>
          </Grid>

          {criticalPatients.length > 0 && (
            <Alert severity="error" sx={{ mt: 2 }}>
              {criticalPatients.length} critical patients waiting
            </Alert>
          )}

          <Box display="flex" justifyContent="space-between" alignItems="center" mt={2}>
            <Typography variant="body2" color="textSecondary">
              {criticalPatients.length} critical cases
            </Typography>
            <Button
              variant="outlined"
              size="small"
              onClick={() => setIsAssessing(true)}
              startIcon={<Add />}
            >
              New Assessment
            </Button>
          </Box>
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
            Emergency Triage
          </Typography>
          <Typography variant="subtitle1" color="textSecondary">
            Real-time patient assessment and prioritization
          </Typography>
        </Box>

        <Box display="flex" alignItems="center" gap={2}>
          <Button
            variant="contained"
            onClick={() => setIsAssessing(true)}
            startIcon={<Add />}
            color="error"
          >
            New Patient Assessment
          </Button>
        </Box>
      </Box>

      {/* Statistics */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={2}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <Typography variant="h3" fontWeight={600} color={theme.palette.error.main}>
                {patients.filter(p => p.triageLevel === 'resuscitation').length}
              </Typography>
              <Typography variant="body2" color="textSecondary">
                Resuscitation
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={2}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <Typography variant="h3" fontWeight={600} color={theme.palette.error.main}>
                {patients.filter(p => p.triageLevel === 'emergent').length}
              </Typography>
              <Typography variant="body2" color="textSecondary">
                Emergent
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={2}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <Typography variant="h3" fontWeight={600} color={theme.palette.warning.main}>
                {patients.filter(p => p.triageLevel === 'urgent').length}
              </Typography>
              <Typography variant="body2" color="textSecondary">
                Urgent
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={2}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <Typography variant="h3" fontWeight={600} color={theme.palette.info.main}>
                {patients.filter(p => p.triageLevel === 'less-urgent').length}
              </Typography>
              <Typography variant="body2" color="textSecondary">
                Less Urgent
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={2}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <Typography variant="h3" fontWeight={600} color={theme.palette.success.main}>
                {patients.filter(p => p.triageLevel === 'non-urgent').length}
              </Typography>
              <Typography variant="body2" color="textSecondary">
                Non-Urgent
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={2}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <Typography variant="h3" fontWeight={600} color={theme.palette.primary.main}>
                {patients.filter(p => p.isCritical).length}
              </Typography>
              <Typography variant="body2" color="textSecondary">
                Critical
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Filters and Search */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Box display="flex" alignItems="center" gap={2}>
          <TextField
            placeholder="Search patients..."
            size="small"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            sx={{ width: 250 }}
          />
          <Select
            value={filterLevel}
            onChange={(e) => setFilterLevel(e.target.value)}
            size="small"
            sx={{ width: 150 }}
          >
            <MenuItem value="all">All Levels</MenuItem>
            <MenuItem value="resuscitation">Resuscitation</MenuItem>
            <MenuItem value="emergent">Emergent</MenuItem>
            <MenuItem value="urgent">Urgent</MenuItem>
            <MenuItem value="less-urgent">Less Urgent</MenuItem>
            <MenuItem value="non-urgent">Non-Urgent</MenuItem>
          </Select>
        </Box>
        <Typography variant="body2" color="textSecondary">
          {getFilteredPatients().length} patients
        </Typography>
      </Box>

      {/* Patient Grid */}
      <Grid container spacing={3}>
        {getFilteredPatients().map(patient => (
          <Grid item xs={12} md={6} lg={4} key={patient.id}>
            <TriagePatientCard
              patient={patient}
              assessment={assessments.find(a => a.patientId === patient.id)}
            />
          </Grid>
        ))}
      </Grid>

      {/* Assessment Dialog */}
      <Dialog
        open={isAssessing}
        onClose={() => setIsAssessing(false)}
        maxWidth="md"
        fullWidth
        PaperProps={{
          sx: {
            maxHeight: '90vh',
          },
        }}
      >
        <DialogTitle>
          <Box display="flex" alignItems="center" gap={2}>
            <Assessment />
            <Typography variant="h6">
              {selectedPatient ? `Triage Assessment - ${selectedPatient.name}` : 'New Patient Assessment'}
            </Typography>
          </Box>
        </DialogTitle>
        <DialogContent>
          <Stepper activeStep={0} orientation="vertical">
            <Step>
              <StepLabel>Patient Information</StepLabel>
              <StepContent>
                <Grid container spacing={2}>
                  <Grid item xs={12} sm={6}>
                    <TextField
                      label="Patient Name"
                      fullWidth
                      value={selectedPatient?.name || ''}
                      disabled
                    />
                  </Grid>
                  <Grid item xs={12} sm={6}>
                    <TextField
                      label="Chief Complaint"
                      fullWidth
                      value={selectedPatient?.chiefComplaint || ''}
                      disabled
                    />
                  </Grid>
                </Grid>
              </StepContent>
            </Step>

            <Step>
              <StepLabel>Vital Signs Assessment</StepLabel>
              <StepContent>
                <Grid container spacing={2}>
                  <Grid item xs={12} sm={6}>
                    <TextField
                      label="Heart Rate (bpm)"
                      type="number"
                      fullWidth
                      value={currentAssessment?.vitalSigns?.heartRate || ''}
                      onChange={(e) => setCurrentAssessment(prev => ({
                        ...prev,
                        vitalSigns: { ...prev.vitalSigns, heartRate: parseInt(e.target.value) }
                      }))}
                    />
                  </Grid>
                  <Grid item xs={12} sm={6}>
                    <TextField
                      label="Oxygen Saturation (%)"
                      type="number"
                      fullWidth
                      value={currentAssessment?.vitalSigns?.oxygenSaturation || ''}
                      onChange={(e) => setCurrentAssessment(prev => ({
                        ...prev,
                        vitalSigns: { ...prev.vitalSigns, oxygenSaturation: parseInt(e.target.value) }
                      }))}
                    />
                  </Grid>
                </Grid>
              </StepContent>
            </Step>

            <Step>
              <StepLabel>Triage Level Assignment</StepLabel>
              <StepContent>
                <FormControl component="fieldset" fullWidth>
                  <FormLabel component="legend">Emergency Severity Index (ESI) Level</FormLabel>
                  <RadioGroup
                    value={currentAssessment?.triageLevel || ''}
                    onChange={(e) => setCurrentAssessment(prev => ({
                      ...prev,
                      triageLevel: e.target.value as any,
                      esiScore: parseInt(e.target.value.split('-')[0]) as any
                    }))}
                  >
                    {Object.entries(triageLabels).map(([key, label]) => (
                      <FormControlLabel
                        key={key}
                        value={key}
                        control={<Radio />}
                        label={
                          <Box>
                            <Typography variant="body2" fontWeight={600}>
                              {label}
                            </Typography>
                            <Typography variant="caption" color="textSecondary">
                              {triageDescriptions[key as keyof typeof triageDescriptions]}
                            </Typography>
                          </Box>
                        }
                      />
                    ))}
                  </RadioGroup>
                </FormControl>
              </StepContent>
            </Step>

            <Step>
              <StepLabel>Critical Findings</StepLabel>
              <StepContent>
                <TextField
                  label="Critical Findings"
                  multiline
                  rows={3}
                  fullWidth
                  placeholder="List any critical findings that require immediate attention..."
                  value={currentAssessment?.criticalFindings?.join('\n') || ''}
                  onChange={(e) => setCurrentAssessment(prev => ({
                    ...prev,
                    criticalFindings: e.target.value.split('\n').filter(f => f.trim())
                  }))}
                />
              </StepContent>
            </Step>

            <Step>
              <StepLabel>Disposition</StepLabel>
              <StepContent>
                <FormControl fullWidth>
                  <InputLabel>Disposition</InputLabel>
                  <Select
                    value={currentAssessment?.disposition || ''}
                    onChange={(e) => setCurrentAssessment(prev => ({
                      ...prev,
                      disposition: e.target.value as any
                    }))}
                  >
                    <MenuItem value="resuscitation">Resuscitation Room</MenuItem>
                    <MenuItem value="immediate">Immediate Bed</MenuItem>
                    <MenuItem value="ed">Emergency Department</MenuItem>
                    <MenuItem value="fast-track">Fast Track</MenuItem>
                    <MenuItem value="waiting-room">Waiting Room</MenuItem>
                  </Select>
                </FormControl>
              </StepContent>
            </Step>
          </Stepper>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setIsAssessing(false)}>Cancel</Button>
          <Button
            variant="contained"
            onClick={() => {
              if (selectedPatient && currentAssessment.triageLevel) {
                onAssessmentComplete({
                  id: `assessment-${Date.now()}`,
                  patientId: selectedPatient.id,
                  assessor: 'Current User',
                  assessmentTime: new Date(),
                  triageLevel: currentAssessment.triageLevel!,
                  esiScore: currentAssessment.esiScore!,
                  criticalFindings: currentAssessment.criticalFindings || [],
                  disposition: currentAssessment.disposition || 'waiting-room',
                  estimatedTreatmentTime: 30,
                  resourcesRequired: [],
                  specialConsiderations: [],
                })
                setIsAssessing(false)
                setCurrentAssessment({})
              }
            }}
          >
            Complete Assessment
          </Button>
        </DialogActions>
      </Dialog>

      {/* Patient Details Dialog */}
      <Dialog
        open={selectedPatient !== null && !isAssessing}
        onClose={() => setSelectedPatient(null)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>Patient Details</DialogTitle>
        <DialogContent>
          {selectedPatient && (
            <Box>
              <Typography variant="h6" fontWeight={600} mb={2}>
                {selectedPatient.name}
              </Typography>

              <Grid container spacing={2}>
                <Grid item xs={12} sm={6}>
                  <Typography variant="body2"><strong>Age:</strong> {selectedPatient.age}</Typography>
                  <Typography variant="body2"><strong>Gender:</strong> {selectedPatient.gender}</Typography>
                  <Typography variant="body2"><strong>Chief Complaint:</strong> {selectedPatient.chiefComplaint}</Typography>
                  <Typography variant="body2"><strong>Triage Level:</strong> {triageLabels[selectedPatient.triageLevel]}</Typography>
                </Grid>
                <Grid item xs={12} sm={6}>
                  <Typography variant="body2"><strong>Arrival Time:</strong> {format(selectedPatient.arrivalTime, 'MMM dd, yyyy HH:mm')}</Typography>
                  <Typography variant="body2"><strong>Transport Method:</strong> {selectedPatient.transportMethod.replace('-', ' ')}</Typography>
                  <Typography variant="body2"><strong>Location:</strong> {selectedPatient.location || 'Not assigned'}</Typography>
                  {selectedPatient.assignedProvider && (
                    <Typography variant="body2"><strong>Provider:</strong> {selectedPatient.assignedProvider}</Typography>
                  )}
                </Grid>
              </Grid>

              <Divider sx={{ my: 2 }} />

              <Typography variant="h6" fontWeight={600} mb={2}>
                Vital Signs
              </Typography>
              <Grid container spacing={2}>
                <Grid item xs={12} sm={6}>
                  <Typography variant="body2"><strong>Heart Rate:</strong> {selectedPatient.vitalSigns.heartRate} bpm</Typography>
                  <Typography variant="body2"><strong>Oxygen Saturation:</strong> {selectedPatient.vitalSigns.oxygenSaturation}%</Typography>
                  <Typography variant="body2"><strong>Temperature:</strong> {selectedPatient.vitalSigns.temperature || 'Not recorded'}°C</Typography>
                </Grid>
                <Grid item xs={12} sm={6}>
                  <Typography variant="body2"><strong>Blood Pressure:</strong> {selectedPatient.vitalSigns.bloodPressure ? `${selectedPatient.vitalSigns.bloodPressure.systolic}/${selectedPatient.vitalSigns.bloodPressure.diastolic}` : 'Not recorded'}</Typography>
                  <Typography variant="body2"><strong>Respiratory Rate:</strong> {selectedPatient.vitalSigns.respiratoryRate || 'Not recorded'}</Typography>
                  <Typography variant="body2"><strong>Pain Level:</strong> {selectedPatient.vitalSigns.painLevel}/10</Typography>
                </Grid>
              </Grid>

              <Divider sx={{ my: 2 }} />

              <Typography variant="h6" fontWeight={600} mb={2}>
                Clinical Information
              </Typography>
              <Grid container spacing={2}>
                <Grid item xs={12} sm={6}>
                  <Typography variant="body2"><strong>Consciousness:</strong> {selectedPatient.vitalSigns.consciousness}</Typography>
                  <Typography variant="body2"><strong>Symptoms:</strong> {selectedPatient.symptoms.join(', ')}</Typography>
                </Grid>
                <Grid item xs={12} sm={6}>
                  <Typography variant="body2"><strong>Allergies:</strong> {selectedPatient.allergies.join(', ') || 'None'}</Typography>
                  <Typography variant="body2"><strong>Medications:</strong> {selectedPatient.medications.join(', ') || 'None'}</Typography>
                </Grid>
              </Grid>

              {selectedPatient.notes && (
                <>
                  <Divider sx={{ my: 2 }} />
                  <Typography variant="h6" fontWeight={600} mb={1}>
                    Notes
                  </Typography>
                  <Typography variant="body2">
                    {selectedPatient.notes}
                  </Typography>
                </>
              )}
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setSelectedPatient(null)}>Close</Button>
          <Button
            variant="contained"
            onClick={() => {
              setIsAssessing(true)
            }}
          >
            Start Assessment
          </Button>
        </DialogActions>
      </Dialog>
    </Paper>
  )
}

export default EmergencyTriage