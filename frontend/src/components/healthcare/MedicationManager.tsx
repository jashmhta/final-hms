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
  Badge,
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
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  useTheme,
  alpha,
  Divider,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  Switch,
  FormControlLabel,
} from '@mui/material'
import {
  Medication,
  LocalPharmacy,
  AccessTime,
  Warning,
  CheckCircle,
  Error,
  Add,
  Edit,
  Delete,
  Schedule,
  Today,
  NotificationsActive,
  Search,
  FilterList,
  History,
  Info,
  Science,
  Bloodtype,
  PregnantWoman,
  NoFood,
  NoDrinks,
} from '@mui/icons-material'
import { format, addDays, subDays, isToday, isBefore, parseISO } from 'date-fns'

export interface Medication {
  id: string
  name: string
  genericName?: string
  dosage: string
  frequency: string
  route: 'oral' | 'intravenous' | 'intramuscular' | 'subcutaneous' | 'topical' | 'inhalation'
  strength: string
  form: 'tablet' | 'capsule' | 'liquid' | 'injection' | 'cream' | 'inhaler' | 'patch'
  instructions: string
  startDate: string
  endDate?: string
  status: 'active' | 'completed' | 'discontinued' | 'on-hold'
  prescribedBy: string
  prescribedDate: string
  reason: string
  refills: number
  refillsRemaining: number
  interactions?: string[]
  sideEffects?: string[]
  contraindications?: string[]
  requiresMonitoring: boolean
  monitoringParameters?: string[]
  isControlled: boolean
  isHighRisk: boolean
  prn: boolean
  prnReason?: string
  lastAdministered?: string
  nextDose?: string
  adherence?: number
}

export interface MedicationInteraction {
  id: string
  medication1: string
  medication2: string
  severity: 'minor' | 'moderate' | 'major' | 'contraindicated'
  description: string
  recommendation: string
  lastChecked: string
}

export interface MedicationSchedule {
  id: string
  medicationId: string
  time: string
  frequency: string
  status: 'scheduled' | 'administered' | 'missed' | 'skipped' | 'late'
  administeredBy?: string
  notes?: string
}

interface MedicationManagerProps {
  patientId: string
  patientName: string
  medications: Medication[]
  schedules: MedicationSchedule[]
  interactions: MedicationInteraction[]
  onMedicationUpdate: (medication: Medication) => void
  onMedicationAdd: (medication: Omit<Medication, 'id'>) => void
  onMedicationDelete: (medicationId: string) => void
  onScheduleUpdate: (schedule: MedicationSchedule) => void
  onInteractionCheck: (medicationId: string) => void
  className?: string
  compact?: boolean
}

const MedicationManager: React.FC<MedicationManagerProps> = ({
  patientId,
  patientName,
  medications,
  schedules,
  interactions,
  onMedicationUpdate,
  onMedicationAdd,
  onMedicationDelete,
  onScheduleUpdate,
  onInteractionCheck,
  className,
  compact = false,
}) => {
  const theme = useTheme()
  const [selectedMedication, setSelectedMedication] = useState<Medication | null>(null)
  const [isEditing, setIsEditing] = useState(false)
  const [isAdding, setIsAdding] = useState(false)
  const [showInteractions, setShowInteractions] = useState(false)
  const [filterStatus, setFilterStatus] = useState<string>('all')
  const [searchTerm, setSearchTerm] = useState('')
  const [page, setPage] = useState(0)
  const [rowsPerPage, setRowsPerPage] = useState(10)

  const getMedicationStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return theme.palette.success.main
      case 'completed':
        return theme.palette.primary.main
      case 'discontinued':
        return theme.palette.error.main
      case 'on-hold':
        return theme.palette.warning.main
      default:
        return theme.palette.grey[500]
    }
  }

  const getInteractionSeverityColor = (severity: string) => {
    switch (severity) {
      case 'contraindicated':
        return theme.palette.error.main
      case 'major':
        return theme.palette.error.main
      case 'moderate':
        return theme.palette.warning.main
      case 'minor':
        return theme.palette.info.main
      default:
        return theme.palette.grey[500]
    }
  }

  const getRouteIcon = (route: string) => {
    const icons: Record<string, React.ReactNode> = {
      oral: <Medication />,
      intravenous: <Bloodtype />,
      intramuscular: <Science />,
      subcutaneous: <Science />,
      topical: <Medication />,
      inhalation: <Science />,
    }
    return icons[route] || <Medication />
  }

  const getFilteredMedications = () => {
    return medications
      .filter(med => {
        const matchesFilter = filterStatus === 'all' || med.status === filterStatus
        const matchesSearch = searchTerm === '' ||
          med.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
          med.genericName?.toLowerCase().includes(searchTerm.toLowerCase())
        return matchesFilter && matchesSearch
      })
  }

  const getTodaysSchedule = () => {
    const today = format(new Date(), 'yyyy-MM-dd')
    return schedules
      .filter(schedule => {
        const scheduleDate = new Date(schedule.time).toISOString().split('T')[0]
        return scheduleDate === today
      })
      .sort((a, b) => new Date(a.time).getTime() - new Date(b.time).getTime())
  }

  const getUpcomingMedications = () => {
    const now = new Date()
    const next24Hours = addDays(now, 1)

    return schedules
      .filter(schedule => {
        const scheduleTime = new Date(schedule.time)
        return scheduleTime > now && scheduleTime <= next24Hours && schedule.status === 'scheduled'
      })
      .sort((a, b) => new Date(a.time).getTime() - new Date(b.time).getTime())
  }

  const getOverdueMedications = () => {
    const now = new Date()
    return schedules
      .filter(schedule => {
        const scheduleTime = new Date(schedule.time)
        return scheduleTime < now && schedule.status === 'scheduled'
      })
      .sort((a, b) => new Date(a.time).getTime() - new Date(b.time).getTime())
  }

  const calculateAdherence = (medicationId: string) => {
    const medSchedules = schedules.filter(s => s.medicationId === medicationId)
    if (medSchedules.length === 0) return 0

    const administered = medSchedules.filter(s => s.status === 'administered').length
    return Math.round((administered / medSchedules.length) * 100)
  }

  const MedicationCard: React.FC<{
    medication: Medication
    adherence?: number
    upcomingDose?: string
  }> = ({ medication, adherence, upcomingDose }) => (
    <Card
      sx={{
        border: medication.isHighRisk ? `2px solid ${theme.palette.error.main}` : `1px solid ${theme.palette.divider}`,
        backgroundColor: medication.isHighRisk ? alpha(theme.palette.error.main, 0.05) : theme.palette.background.paper,
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
              {medication.name}
            </Typography>
            {medication.genericName && (
              <Typography variant="body2" color="textSecondary">
                {medication.genericName}
              </Typography>
            )}
          </Box>
          <Box display="flex" alignItems="center" gap={1}>
            {medication.isHighRisk && (
              <Tooltip title="High Risk Medication">
                <Error sx={{ color: theme.palette.error.main }} />
              </Tooltip>
            )}
            {medication.isControlled && (
              <Tooltip title="Controlled Substance">
                <Warning sx={{ color: theme.palette.warning.main }} />
              </Tooltip>
            )}
            <Chip
              label={medication.status}
              size="small"
              sx={{
                backgroundColor: alpha(getMedicationStatusColor(medication.status), 0.1),
                color: getMedicationStatusColor(medication.status),
              }}
            />
          </Box>
        </Box>

        <Grid container spacing={2}>
          <Grid item xs={12} sm={6}>
            <Typography variant="body2">
              <strong>Dosage:</strong> {medication.dosage}
            </Typography>
            <Typography variant="body2">
              <strong>Strength:</strong> {medication.strength}
            </Typography>
            <Typography variant="body2">
              <strong>Form:</strong> {medication.form}
            </Typography>
            <Typography variant="body2">
              <strong>Route:</strong> {medication.route}
            </Typography>
          </Grid>
          <Grid item xs={12} sm={6}>
            <Typography variant="body2">
              <strong>Frequency:</strong> {medication.frequency}
            </Typography>
            <Typography variant="body2">
              <strong>Started:</strong> {format(new Date(medication.startDate), 'MMM dd, yyyy')}
            </Typography>
            {medication.endDate && (
              <Typography variant="body2">
                <strong>Ends:</strong> {format(new Date(medication.endDate), 'MMM dd, yyyy')}
              </Typography>
            )}
            {medication.refillsRemaining > 0 && (
              <Typography variant="body2">
                <strong>Refills:</strong> {medication.refillsRemaining} of {medication.refills}
              </Typography>
            )}
          </Grid>
        </Grid>

        <Typography variant="body2" sx={{ mt: 2 }}>
          <strong>Instructions:</strong> {medication.instructions}
        </Typography>
        {medication.reason && (
          <Typography variant="body2" sx={{ mt: 1 }}>
            <strong>Reason:</strong> {medication.reason}
          </Typography>
        )}

        {adherence !== undefined && (
          <Box sx={{ mt: 2 }}>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
              <Typography variant="body2" fontWeight={600}>
                Adherence
              </Typography>
              <Typography variant="body2" fontWeight={600}>
                {adherence}%
              </Typography>
            </Box>
            <LinearProgress
              variant="determinate"
              value={adherence}
              sx={{
                height: 8,
                borderRadius: 4,
                backgroundColor: alpha(theme.palette.primary.main, 0.1),
                '& .MuiLinearProgress-bar': {
                  backgroundColor: adherence >= 80 ? theme.palette.success.main :
                                  adherence >= 60 ? theme.palette.warning.main :
                                  theme.palette.error.main,
                },
              }}
            />
          </Box>
        )}

        {upcomingDose && (
          <Alert severity="info" sx={{ mt: 2 }}>
            <Box display="flex" alignItems="center" gap={1}>
              <AccessTime />
              <Typography variant="body2">
                Next dose: {format(new Date(upcomingDose), 'MMM dd, yyyy HH:mm')}
              </Typography>
            </Box>
          </Alert>
        )}

        <Box display="flex" justifyContent="flex-end" gap={1} mt={2}>
          <Tooltip title="View Details">
            <IconButton
              size="small"
              onClick={() => setSelectedMedication(medication)}
            >
              <Info />
            </IconButton>
          </Tooltip>
          <Tooltip title="Edit">
            <IconButton
              size="small"
              onClick={() => {
                setSelectedMedication(medication)
                setIsEditing(true)
              }}
            >
              <Edit />
            </IconButton>
          </Tooltip>
          <Tooltip title="Check Interactions">
            <IconButton
              size="small"
              onClick={() => onInteractionCheck(medication.id)}
              sx={{ color: theme.palette.warning.main }}
            >
              <Warning />
            </IconButton>
          </Tooltip>
          {medication.status === 'active' && (
            <Tooltip title="Discontinue">
              <IconButton
                size="small"
                onClick={() => onMedicationUpdate({ ...medication, status: 'discontinued' })}
                sx={{ color: theme.palette.error.main }}
              >
                <Delete />
              </IconButton>
            </Tooltip>
          )}
        </Box>
      </CardContent>
    </Card>
  )

  if (compact) {
    const activeMeds = medications.filter(med => med.status === 'active')
    const todaySchedule = getTodaysSchedule()
    const overdueMeds = getOverdueMedications()

    return (
      <Card className={className}>
        <CardContent sx={{ p: 2 }}>
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
            <Typography variant="h6" fontWeight={600}>
              Medications
            </Typography>
            <Badge badgeContent={activeMeds.length} color="primary">
              <LocalPharmacy />
            </Badge>
          </Box>

          {overdueMeds.length > 0 && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {overdueMeds.length} overdue medication(s)
            </Alert>
          )}

          <Box sx={{ mb: 2 }}>
            <Typography variant="subtitle2" fontWeight={600} mb={1}>
              Today's Schedule
            </Typography>
            <List dense>
              {todaySchedule.slice(0, 5).map(schedule => {
                const medication = medications.find(med => med.id === schedule.medicationId)
                return (
                  <ListItem key={schedule.id}>
                    <ListItemText
                      primary={medication?.name}
                      secondary={`${format(new Date(schedule.time), 'HH:mm')} • ${schedule.status}`}
                    />
                    <ListItemSecondaryAction>
                      <Chip
                        label={schedule.status}
                        size="small"
                        sx={{
                          backgroundColor: alpha(
                            schedule.status === 'administered' ? theme.palette.success.main :
                            schedule.status === 'missed' ? theme.palette.error.main :
                            theme.palette.warning.main, 0.1
                          ),
                          color: schedule.status === 'administered' ? theme.palette.success.main :
                                 schedule.status === 'missed' ? theme.palette.error.main :
                                 theme.palette.warning.main,
                        }}
                      />
                    </ListItemSecondaryAction>
                  </ListItem>
                )
              })}
            </List>
          </Box>

          <Box display="flex" justifyContent="space-between" alignItems="center">
            <Typography variant="body2" color="textSecondary">
              {activeMeds.length} active medications
            </Typography>
            <Button
              variant="outlined"
              size="small"
              onClick={() => setIsAdding(true)}
              startIcon={<Add />}
            >
              Add
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
            Medication Management
          </Typography>
          <Typography variant="subtitle1" color="textSecondary">
            {patientName} • Patient ID: {patientId}
          </Typography>
        </Box>

        <Box display="flex" alignItems="center" gap={2}>
          <Button
            variant="outlined"
            onClick={() => setShowInteractions(!showInteractions)}
            startIcon={<Warning />}
            color={interactions.length > 0 ? 'warning' : 'default'}
          >
            Interactions ({interactions.length})
          </Button>
          <Button
            variant="contained"
            onClick={() => setIsAdding(true)}
            startIcon={<Add />}
          >
            Add Medication
          </Button>
        </Box>
      </Box>

      {/* Quick Stats */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <Typography variant="h3" fontWeight={600} color={theme.palette.primary.main}>
                {medications.filter(med => med.status === 'active').length}
              </Typography>
              <Typography variant="body2" color="textSecondary">
                Active Medications
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <Typography variant="h3" fontWeight={600} color={theme.palette.success.main}>
                {getTodaysSchedule().filter(s => s.status === 'administered').length}
              </Typography>
              <Typography variant="body2" color="textSecondary">
                Administered Today
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <Typography variant="h3" fontWeight={600} color={theme.palette.warning.main}>
                {getOverdueMedications().length}
              </Typography>
              <Typography variant="body2" color="textSecondary">
                Overdue
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <Typography variant="h3" fontWeight={600} color={theme.palette.info.main}>
                {getUpcomingMedications().length}
              </Typography>
              <Typography variant="body2" color="textSecondary">
                Next 24 Hours
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Critical Alerts */}
      {(getOverdueMedications().length > 0 || interactions.length > 0) && (
        <Box sx={{ mb: 3 }}>
          <Typography variant="h6" fontWeight={600} mb={2}>
            Critical Alerts
          </Typography>
          <Grid container spacing={2}>
            {getOverdueMedications().length > 0 && (
              <Grid item xs={12} md={6}>
                <Alert severity="error">
                  <Typography variant="subtitle2" fontWeight={600}>
                    {getOverdueMedications().length} Overdue Medications
                  </Typography>
                  <Typography variant="body2">
                    Immediate attention required for medication administration
                  </Typography>
                </Alert>
              </Grid>
            )}
            {interactions.filter(i => i.severity === 'major' || i.severity === 'contraindicated').length > 0 && (
              <Grid item xs={12} md={6}>
                <Alert severity="warning">
                  <Typography variant="subtitle2" fontWeight={600}>
                    {interactions.filter(i => i.severity === 'major' || i.severity === 'contraindicated').length} Serious Interactions
                  </Typography>
                  <Typography variant="body2">
                    Potential drug interactions require review
                  </Typography>
                </Alert>
              </Grid>
            )}
          </Grid>
        </Box>
      )}

      {/* Drug Interactions */}
      {showInteractions && (
        <Box sx={{ mb: 3 }}>
          <Typography variant="h6" fontWeight={600} mb={2}>
            Drug Interactions
          </Typography>
          <Card>
            <CardContent>
              {interactions.length === 0 ? (
                <Typography variant="body2" color="textSecondary">
                  No known drug interactions detected.
                </Typography>
              ) : (
                <List>
                  {interactions.map(interaction => (
                    <ListItem key={interaction.id} divider>
                      <ListItemText
                        primary={
                          <Box display="flex" alignItems="center" gap={1}>
                            <Chip
                              label={interaction.severity}
                              size="small"
                              sx={{
                                backgroundColor: alpha(getInteractionSeverityColor(interaction.severity), 0.1),
                                color: getInteractionSeverityColor(interaction.severity),
                              }}
                            />
                            <Typography variant="subtitle2" fontWeight={600}>
                              {interaction.medication1} ↔ {interaction.medication2}
                            </Typography>
                          </Box>
                        }
                        secondary={
                          <Box>
                            <Typography variant="body2" sx={{ mt: 1 }}>
                              {interaction.description}
                            </Typography>
                            <Typography variant="body2" color="textSecondary" sx={{ mt: 0.5 }}>
                              <strong>Recommendation:</strong> {interaction.recommendation}
                            </Typography>
                          </Box>
                        }
                      />
                    </ListItem>
                  ))}
                </List>
              )}
            </CardContent>
          </Card>
        </Box>
      )}

      {/* Today's Schedule */}
      <Box sx={{ mb: 3 }}>
        <Typography variant="h6" fontWeight={600} mb={2}>
          Today's Schedule
        </Typography>
        <Card>
          <CardContent>
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Time</TableCell>
                    <TableCell>Medication</TableCell>
                    <TableCell>Dosage</TableCell>
                    <TableCell>Status</TableCell>
                    <TableCell>Administered By</TableCell>
                    <TableCell>Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {getTodaysSchedule().map(schedule => {
                    const medication = medications.find(med => med.id === schedule.medicationId)
                    return (
                      <TableRow key={schedule.id}>
                        <TableCell>{format(new Date(schedule.time), 'HH:mm')}</TableCell>
                        <TableCell>{medication?.name}</TableCell>
                        <TableCell>{medication?.dosage}</TableCell>
                        <TableCell>
                          <Chip
                            label={schedule.status}
                            size="small"
                            sx={{
                              backgroundColor: alpha(
                                schedule.status === 'administered' ? theme.palette.success.main :
                                schedule.status === 'missed' ? theme.palette.error.main :
                                schedule.status === 'late' ? theme.palette.warning.main :
                                theme.palette.info.main, 0.1
                              ),
                              color: schedule.status === 'administered' ? theme.palette.success.main :
                                     schedule.status === 'missed' ? theme.palette.error.main :
                                     schedule.status === 'late' ? theme.palette.warning.main :
                                     theme.palette.info.main,
                            }}
                          />
                        </TableCell>
                        <TableCell>{schedule.administeredBy || '-'}</TableCell>
                        <TableCell>
                          {schedule.status === 'scheduled' && (
                            <Button
                              size="small"
                              variant="outlined"
                              onClick={() => onScheduleUpdate({ ...schedule, status: 'administered', administeredBy: 'Nurse' })}
                            >
                              Administer
                            </Button>
                          )}
                        </TableCell>
                      </TableRow>
                    )
                  })}
                </TableBody>
              </Table>
            </TableContainer>
          </CardContent>
        </Card>
      </Box>

      {/* Medications List */}
      <Box>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
          <Typography variant="h6" fontWeight={600}>
            All Medications
          </Typography>
          <Box display="flex" alignItems="center" gap={2}>
            <TextField
              placeholder="Search medications..."
              size="small"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              sx={{ width: 200 }}
            />
            <Select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              size="small"
              sx={{ width: 120 }}
            >
              <MenuItem value="all">All</MenuItem>
              <MenuItem value="active">Active</MenuItem>
              <MenuItem value="completed">Completed</MenuItem>
              <MenuItem value="discontinued">Discontinued</MenuItem>
              <MenuItem value="on-hold">On Hold</MenuItem>
            </Select>
          </Box>
        </Box>

        <Grid container spacing={3}>
          {getFilteredMedications()
            .slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage)
            .map(medication => (
              <Grid item xs={12} md={6} lg={4} key={medication.id}>
                <MedicationCard
                  medication={medication}
                  adherence={calculateAdherence(medication.id)}
                  upcomingDose={getUpcomingMedications().find(s => s.medicationId === medication.id)?.time}
                />
              </Grid>
            ))}
        </Grid>

        {getFilteredMedications().length > rowsPerPage && (
          <Box display="flex" justifyContent="center" mt={3}>
            <TablePagination
              component="div"
              count={getFilteredMedications().length}
              page={page}
              onPageChange={(_, newPage) => setPage(newPage)}
              rowsPerPage={rowsPerPage}
              onRowsPerPageChange={(e) => setRowsPerPage(parseInt(e.target.value, 10))}
            />
          </Box>
        )}
      </Box>

      {/* Medication Details Dialog */}
      <Dialog
        open={selectedMedication !== null && !isEditing}
        onClose={() => setSelectedMedication(null)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>Medication Details</DialogTitle>
        <DialogContent>
          {selectedMedication && (
            <Box>
              <Typography variant="h6" fontWeight={600} mb={2}>
                {selectedMedication.name}
              </Typography>
              {selectedMedication.genericName && (
                <Typography variant="body2" color="textSecondary" mb={2}>
                  Generic: {selectedMedication.genericName}
                </Typography>
              )}

              <Grid container spacing={2}>
                <Grid item xs={12} sm={6}>
                  <Typography variant="body2"><strong>Dosage:</strong> {selectedMedication.dosage}</Typography>
                  <Typography variant="body2"><strong>Strength:</strong> {selectedMedication.strength}</Typography>
                  <Typography variant="body2"><strong>Form:</strong> {selectedMedication.form}</Typography>
                  <Typography variant="body2"><strong>Route:</strong> {selectedMedication.route}</Typography>
                  <Typography variant="body2"><strong>Frequency:</strong> {selectedMedication.frequency}</Typography>
                </Grid>
                <Grid item xs={12} sm={6}>
                  <Typography variant="body2"><strong>Started:</strong> {format(new Date(selectedMedication.startDate), 'MMM dd, yyyy')}</Typography>
                  {selectedMedication.endDate && (
                    <Typography variant="body2"><strong>Ends:</strong> {format(new Date(selectedMedication.endDate), 'MMM dd, yyyy')}</Typography>
                  )}
                  <Typography variant="body2"><strong>Prescribed by:</strong> {selectedMedication.prescribedBy}</Typography>
                  <Typography variant="body2"><strong>Refills:</strong> {selectedMedication.refillsRemaining} of {selectedMedication.refills}</Typography>
                  <Typography variant="body2"><strong>Status:</strong> {selectedMedication.status}</Typography>
                </Grid>
              </Grid>

              <Divider sx={{ my: 2 }} />

              <Typography variant="body2" sx={{ mb: 1 }}>
                <strong>Instructions:</strong> {selectedMedication.instructions}
              </Typography>
              <Typography variant="body2" sx={{ mb: 1 }}>
                <strong>Reason:</strong> {selectedMedication.reason}
              </Typography>

              {selectedMedication.sideEffects && selectedMedication.sideEffects.length > 0 && (
                <Box sx={{ mt: 2 }}>
                  <Typography variant="body2" fontWeight={600} sx={{ mb: 1 }}>
                    Side Effects:
                  </Typography>
                  <List dense>
                    {selectedMedication.sideEffects.map((effect, index) => (
                      <ListItem key={index}>
                        <ListItemText primary={effect} />
                      </ListItem>
                    ))}
                  </List>
                </Box>
              )}

              {selectedMedication.contraindications && selectedMedication.contraindications.length > 0 && (
                <Box sx={{ mt: 2 }}>
                  <Typography variant="body2" fontWeight={600} sx={{ mb: 1 }}>
                    Contraindications:
                  </Typography>
                  <List dense>
                    {selectedMedication.contraindications.map((contraindication, index) => (
                      <ListItem key={index}>
                        <ListItemText primary={contraindication} />
                      </ListItem>
                    ))}
                  </List>
                </Box>
              )}
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setSelectedMedication(null)}>Close</Button>
          <Button
            onClick={() => {
              setIsEditing(true)
            }}
            variant="contained"
          >
            Edit
          </Button>
        </DialogActions>
      </Dialog>
    </Paper>
  )
}

export default MedicationManager