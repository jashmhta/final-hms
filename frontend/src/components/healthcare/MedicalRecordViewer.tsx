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
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  Tabs,
  Tab,
  List,
  ListItem,
  ListItemText,
  ListItemAvatar,
  Avatar,
  Badge,
  useTheme,
  alpha,
  Divider,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  FormControlLabel,
  Switch,
  InputAdornment,
  OutlinedInput,
} from '@mui/material'
import {
  Description,
  Download,
  Print,
  Share,
  Edit,
  Delete,
  Add,
  Search,
  FilterList,
  CalendarToday,
  Person,
  MedicalServices,
  Medication,
  LocalHospital,
  Science,
  Attachment,
  ExpandMore,
  PictureAsPdf,
  Image,
  Videocam,
  AudioFile,
  TextSnippet,
  Timeline,
  Assessment,
  Note,
  Favorite,
  WaterDrop,
  Speed,
  MonitorWeight,
  Height,
} from '@mui/icons-material'
import { format, addDays, subDays, isAfter, isBefore, parseISO } from 'date-fns'

export interface MedicalRecord {
  id: string
  patientId: string
  type: 'consultation' | 'diagnosis' | 'procedure' | 'medication' | 'lab-result' | 'imaging' | 'vital-signs' | 'discharge-summary' | 'progress-note' | 'referral'
  title: string
  description: string
  date: Date
  provider: {
    id: string
    name: string
    specialty: string
    role: string
  }
  facility: string
  department: string
  encounterId?: string
  icdCodes?: string[]
  cptCodes?: string[]
  medications?: string[]
  procedures?: string[]
  labResults?: any[]
  imagingResults?: any[]
  vitalSigns?: {
    temperature?: number
    bloodPressure?: { systolic: number; diastolic: number }
    heartRate: number
    oxygenSaturation: number
    respiratoryRate?: number
    weight?: number
    height?: number
    bmi?: number
  }
  attachments?: Attachment[]
  notes?: string
  followUpRequired: boolean
  followUpDate?: Date
  isConfidential: boolean
  isCritical: boolean
  lastModified: Date
  createdBy: string
  tags: string[]
}

export interface Attachment {
  id: string
  name: string
  type: 'pdf' | 'image' | 'video' | 'audio' | 'document'
  size: number
  url: string
  description: string
  uploadedBy: string
  uploadDate: Date
}

interface MedicalRecordViewerProps {
  patientId: string
  patientName: string
  records: MedicalRecord[]
  onRecordAdd: (record: Omit<MedicalRecord, 'id'>) => void
  onRecordUpdate: (record: MedicalRecord) => void
  onRecordDelete: (recordId: string) => void
  onRecordShare: (recordId: string, recipients: string[]) => void
  onRecordExport: (recordId: string, format: 'pdf' | 'xml') => void
  className?: string
  compact?: boolean
}

const MedicalRecordViewer: React.FC<MedicalRecordViewerProps> = ({
  patientId,
  patientName,
  records,
  onRecordAdd,
  onRecordUpdate,
  onRecordDelete,
  onRecordShare,
  onRecordExport,
  className,
  compact = false,
}) => {
  const theme = useTheme()
  const [selectedRecord, setSelectedRecord] = useState<MedicalRecord | null>(null)
  const [isEditing, setIsEditing] = useState(false)
  const [isAdding, setIsAdding] = useState(false)
  const [activeTab, setActiveTab] = useState(0)
  const [searchTerm, setSearchTerm] = useState('')
  const [filterType, setFilterType] = useState<string>('all')
  const [dateRange, setDateRange] = useState({ start: null as Date | null, end: null as Date | null })
  const [sortBy, setSortBy] = useState<'date' | 'type' | 'provider'>('date')
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc')
  const [page, setPage] = useState(0)
  const [rowsPerPage, setRowsPerPage] = useState(10)

  const recordTypeColors = {
    'consultation': theme.palette.info.main,
    'diagnosis': theme.palette.error.main,
    'procedure': theme.palette.warning.main,
    'medication': theme.palette.success.main,
    'lab-result': theme.palette.secondary.main,
    'imaging': theme.palette.primary.main,
    'vital-signs': theme.palette.info.main,
    'discharge-summary': theme.palette.grey[600],
    'progress-note': theme.palette.warning.main,
    'referral': theme.palette.info.main,
  }

  const recordTypeIcons = {
    'consultation': <Person />,
    'diagnosis': <Assessment />,
    'procedure': <MedicalServices />,
    'medication': <Medication />,
    'lab-result': <Science />,
    'imaging': <LocalHospital />,
    'vital-signs': <Favorite />,
    'discharge-summary': <Description />,
    'progress-note': <Note />,
    'referral': <Share />,
  }

  const getFilteredRecords = () => {
    return records
      .filter(record => {
        const matchesSearch = searchTerm === '' ||
          record.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
          record.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
          record.provider.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
          record.tags.some(tag => tag.toLowerCase().includes(searchTerm.toLowerCase()))

        const matchesType = filterType === 'all' || record.type === filterType

        const matchesDateRange = (!dateRange.start || !isBefore(record.date, dateRange.start)) &&
                                 (!dateRange.end || !isAfter(record.date, dateRange.end))

        return matchesSearch && matchesType && matchesDateRange
      })
      .sort((a, b) => {
        let comparison = 0
        switch (sortBy) {
          case 'date':
            comparison = a.date.getTime() - b.date.getTime()
            break
          case 'type':
            comparison = a.type.localeCompare(b.type)
            break
          case 'provider':
            comparison = a.provider.name.localeCompare(b.provider.name)
            break
        }
        return sortOrder === 'asc' ? comparison : -comparison
      })
  }

  const getRecordStats = () => {
    const totalRecords = records.length
    const criticalRecords = records.filter(r => r.isCritical).length
    const confidentialRecords = records.filter(r => r.isConfidential).length
    const recentRecords = records.filter(r => {
      const thirtyDaysAgo = subDays(new Date(), 30)
      return isAfter(r.date, thirtyDaysAgo)
    }).length

    return { totalRecords, criticalRecords, confidentialRecords, recentRecords }
  }

  const getAttachmentIcon = (type: string) => {
    switch (type) {
      case 'pdf':
        return <PictureAsPdf />
      case 'image':
        return <Image />
      case 'video':
        return <Videocam />
      case 'audio':
        return <AudioFile />
      default:
        return <TextSnippet />
    }
  }

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  const VitalSignsDisplay: React.FC<{ vitalSigns: MedicalRecord['vitalSigns'] }> = ({ vitalSigns }) => {
    if (!vitalSigns) return null

    return (
      <Grid container spacing={1}>
        {vitalSigns.temperature && (
          <Grid item xs={6} sm={3}>
            <Typography variant="caption" color="textSecondary">Temperature</Typography>
            <Typography variant="body2">{vitalSigns.temperature}°C</Typography>
          </Grid>
        )}
        {vitalSigns.bloodPressure && (
          <Grid item xs={6} sm={3}>
            <Typography variant="caption" color="textSecondary">Blood Pressure</Typography>
            <Typography variant="body2">{vitalSigns.bloodPressure.systolic}/{vitalSigns.bloodPressure.diastolic}</Typography>
          </Grid>
        )}
        {vitalSigns.heartRate && (
          <Grid item xs={6} sm={3}>
            <Typography variant="caption" color="textSecondary">Heart Rate</Typography>
            <Typography variant="body2">{vitalSigns.heartRate} bpm</Typography>
          </Grid>
        )}
        {vitalSigns.oxygenSaturation && (
          <Grid item xs={6} sm={3}>
            <Typography variant="caption" color="textSecondary">O2 Saturation</Typography>
            <Typography variant="body2">{vitalSigns.oxygenSaturation}%</Typography>
          </Grid>
        )}
        {vitalSigns.weight && (
          <Grid item xs={6} sm={3}>
            <Typography variant="caption" color="textSecondary">Weight</Typography>
            <Typography variant="body2">{vitalSigns.weight} kg</Typography>
          </Grid>
        )}
        {vitalSigns.height && (
          <Grid item xs={6} sm={3}>
            <Typography variant="caption" color="textSecondary">Height</Typography>
            <Typography variant="body2">{vitalSigns.height} cm</Typography>
          </Grid>
        )}
        {vitalSigns.bmi && (
          <Grid item xs={6} sm={3}>
            <Typography variant="caption" color="textSecondary">BMI</Typography>
            <Typography variant="body2">{vitalSigns.bmi}</Typography>
          </Grid>
        )}
        {vitalSigns.respiratoryRate && (
          <Grid item xs={6} sm={3}>
            <Typography variant="caption" color="textSecondary">Resp. Rate</Typography>
            <Typography variant="body2">{vitalSigns.respiratoryRate}</Typography>
          </Grid>
        )}
      </Grid>
    )
  }

  const RecordCard: React.FC<{ record: MedicalRecord }> = ({ record }) => (
    <Card
      sx={{
        border: record.isCritical ? `2px solid ${theme.palette.error.main}` :
               record.isConfidential ? `2px solid ${theme.palette.warning.main}` :
               `1px solid ${theme.palette.divider}`,
        backgroundColor: record.isCritical ? alpha(theme.palette.error.main, 0.05) :
                          record.isConfidential ? alpha(theme.palette.warning.main, 0.05) :
                          theme.palette.background.paper,
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
              {record.title}
            </Typography>
            <Typography variant="body2" color="textSecondary">
              {format(record.date, 'MMM dd, yyyy')}
            </Typography>
          </Box>
          <Box display="flex" alignItems="center" gap={1}>
            {record.isCritical && (
              <Tooltip title="Critical Record">
                <Error sx={{ color: theme.palette.error.main }} />
              </Tooltip>
            )}
            {record.isConfidential && (
              <Tooltip title="Confidential">
                <Lock sx={{ color: theme.palette.warning.main }} />
              </Tooltip>
            )}
            {record.followUpRequired && (
              <Tooltip title="Follow-up Required">
                <Schedule sx={{ color: theme.palette.info.main }} />
              </Tooltip>
            )}
            <Chip
              label={record.type.replace('-', ' ')}
              size="small"
              sx={{
                backgroundColor: alpha(recordTypeColors[record.type], 0.1),
                color: recordTypeColors[record.type],
              }}
              icon={recordTypeIcons[record.type]}
            />
          </Box>
        </Box>

        <Typography variant="body2" sx={{ mb: 2 }}>
          {record.description}
        </Typography>

        <Box display="flex" alignItems="center" gap={2} sx={{ mb: 2 }}>
          <Typography variant="caption" color="textSecondary">
            Provider: {record.provider.name}
          </Typography>
          <Typography variant="caption" color="textSecondary">
            Department: {record.department}
          </Typography>
          <Typography variant="caption" color="textSecondary">
            Facility: {record.facility}
          </Typography>
        </Box>

        {record.vitalSigns && (
          <Box sx={{ mb: 2 }}>
            <Typography variant="caption" fontWeight={600} color="textSecondary" sx={{ display: 'block', mb: 1 }}>
              Vital Signs:
            </Typography>
            <VitalSignsDisplay vitalSigns={record.vitalSigns} />
          </Box>
        )}

        {record.attachments && record.attachments.length > 0 && (
          <Box sx={{ mb: 2 }}>
            <Typography variant="caption" fontWeight={600} color="textSecondary" sx={{ display: 'block', mb: 1 }}>
              Attachments ({record.attachments.length}):
            </Typography>
            <Box display="flex" flexWrap="wrap" gap={1}>
              {record.attachments.slice(0, 3).map(attachment => (
                <Chip
                  key={attachment.id}
                  label={attachment.name}
                  size="small"
                  variant="outlined"
                  icon={getAttachmentIcon(attachment.type)}
                  sx={{ fontSize: '0.7rem' }}
                />
              ))}
              {record.attachments.length > 3 && (
                <Chip
                  label={`+${record.attachments.length - 3} more`}
                  size="small"
                  variant="outlined"
                  sx={{ fontSize: '0.7rem' }}
                />
              )}
            </Box>
          </Box>
        )}

        {record.tags.length > 0 && (
          <Box sx={{ mb: 2 }}>
            <Typography variant="caption" fontWeight={600} color="textSecondary" sx={{ display: 'block', mb: 1 }}>
              Tags:
            </Typography>
            <Box display="flex" flexWrap="wrap" gap={1}>
              {record.tags.map((tag, index) => (
                <Chip
                  key={index}
                  label={tag}
                  size="small"
                  variant="outlined"
                  sx={{ fontSize: '0.7rem' }}
                />
              ))}
            </Box>
          </Box>
        )}

        <Box display="flex" justifyContent="space-between" alignItems="center">
          <Typography variant="caption" color="textSecondary">
            Last modified: {format(record.lastModified, 'MMM dd, yyyy HH:mm')}
          </Typography>
          <Box display="flex" gap={1}>
            <Tooltip title="View Details">
              <IconButton
                size="small"
                onClick={() => setSelectedRecord(record)}
              >
                <Description />
              </IconButton>
            </Tooltip>
            <Tooltip title="Edit">
              <IconButton
                size="small"
                onClick={() => {
                  setSelectedRecord(record)
                  setIsEditing(true)
                }}
              >
                <Edit />
              </IconButton>
            </Tooltip>
            <Tooltip title="Export">
              <IconButton
                size="small"
                onClick={() => onRecordExport(record.id, 'pdf')}
              >
                <Download />
              </IconButton>
            </Tooltip>
            <Tooltip title="Share">
              <IconButton
                size="small"
                onClick={() => onRecordShare(record.id, [])}
              >
                <Share />
              </IconButton>
            </Tooltip>
          </Box>
        </Box>
      </CardContent>
    </Card>
  )

  if (compact) {
    const stats = getRecordStats()
    const recentRecords = records.filter(r => {
      const thirtyDaysAgo = subDays(new Date(), 30)
      return isAfter(r.date, thirtyDaysAgo)
    })

    return (
      <Card className={className}>
        <CardContent sx={{ p: 2 }}>
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
            <Typography variant="h6" fontWeight={600}>
              Medical Records
            </Typography>
            <Badge badgeContent={stats.totalRecords} color="primary">
              <Description />
            </Badge>
          </Box>

          <Grid container spacing={2} sx={{ mb: 2 }}>
            <Grid item xs={6}>
              <Box textAlign="center">
                <Typography variant="h4" fontWeight={600} color={theme.palette.primary.main}>
                  {stats.totalRecords}
                </Typography>
                <Typography variant="caption" color="textSecondary">
                  Total Records
                </Typography>
              </Box>
            </Grid>
            <Grid item xs={6}>
              <Box textAlign="center">
                <Typography variant="h4" fontWeight={600} color={theme.palette.info.main}>
                  {recentRecords.length}
                </Typography>
                <Typography variant="caption" color="textSecondary">
                  Recent (30d)
                </Typography>
              </Box>
            </Grid>
          </Grid>

          <List dense>
            {recentRecords.slice(0, 3).map(record => (
              <ListItem key={record.id} divider>
                <ListItemText
                  primary={record.title}
                  secondary={`${format(record.date, 'MMM dd')} • ${record.type.replace('-', ' ')}`}
                />
              </ListItem>
            ))}
          </List>

          <Box display="flex" justifyContent="space-between" alignItems="center">
            <Typography variant="body2" color="textSecondary">
              {stats.criticalRecords} critical records
            </Typography>
            <Button
              variant="outlined"
              size="small"
              onClick={() => setIsAdding(true)}
              startIcon={<Add />}
            >
              Add Record
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
            Medical Records
          </Typography>
          <Typography variant="subtitle1" color="textSecondary">
            {patientName} • Patient ID: {patientId}
          </Typography>
        </Box>

        <Box display="flex" alignItems="center" gap={2}>
          <Button
            variant="contained"
            onClick={() => setIsAdding(true)}
            startIcon={<Add />}
          >
            Add Medical Record
          </Button>
        </Box>
      </Box>

      {/* Statistics */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <Typography variant="h3" fontWeight={600} color={theme.palette.primary.main}>
                {getRecordStats().totalRecords}
              </Typography>
              <Typography variant="body2" color="textSecondary">
                Total Records
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <Typography variant="h3" fontWeight={600} color={theme.palette.error.main}>
                {getRecordStats().criticalRecords}
              </Typography>
              <Typography variant="body2" color="textSecondary">
                Critical Records
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <Typography variant="h3" fontWeight={600} color={theme.palette.warning.main}>
                {getRecordStats().confidentialRecords}
              </Typography>
              <Typography variant="body2" color="textSecondary">
                Confidential Records
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <Typography variant="h3" fontWeight={600} color={theme.palette.info.main}>
                {getRecordStats().recentRecords}
              </Typography>
              <Typography variant="body2" color="textSecondary">
                Recent (30 days)
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Filters and Search */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Box display="flex" alignItems="center" gap={2}>
          <OutlinedInput
            placeholder="Search records..."
            size="small"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            startAdornment={<Search />}
            sx={{ width: 250 }}
          />
          <Select
            value={filterType}
            onChange={(e) => setFilterType(e.target.value)}
            size="small"
            sx={{ width: 150 }}
          >
            <MenuItem value="all">All Types</MenuItem>
            <MenuItem value="consultation">Consultation</MenuItem>
            <MenuItem value="diagnosis">Diagnosis</MenuItem>
            <MenuItem value="procedure">Procedure</MenuItem>
            <MenuItem value="medication">Medication</MenuItem>
            <MenuItem value="lab-result">Lab Results</MenuItem>
            <MenuItem value="imaging">Imaging</MenuItem>
            <MenuItem value="vital-signs">Vital Signs</MenuItem>
            <MenuItem value="discharge-summary">Discharge Summary</MenuItem>
            <MenuItem value="progress-note">Progress Note</MenuItem>
            <MenuItem value="referral">Referral</MenuItem>
          </Select>
          <Select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as any)}
            size="small"
            sx={{ width: 120 }}
          >
            <MenuItem value="date">Date</MenuItem>
            <MenuItem value="type">Type</MenuItem>
            <MenuItem value="provider">Provider</MenuItem>
          </Select>
          <Select
            value={sortOrder}
            onChange={(e) => setSortOrder(e.target.value as any)}
            size="small"
            sx={{ width: 100 }}
          >
            <MenuItem value="desc">Newest</MenuItem>
            <MenuItem value="asc">Oldest</MenuItem>
          </Select>
        </Box>
        <Typography variant="body2" color="textSecondary">
          {getFilteredRecords().length} records
        </Typography>
      </Box>

      {/* Records Grid */}
      <Grid container spacing={3}>
        {getFilteredRecords()
          .slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage)
          .map(record => (
            <Grid item xs={12} key={record.id}>
              <RecordCard record={record} />
            </Grid>
          ))}
      </Grid>

      {/* Pagination */}
      {getFilteredRecords().length > rowsPerPage && (
        <Box display="flex" justifyContent="center" mt={3}>
          <TablePagination
            component="div"
            count={getFilteredRecords().length}
            page={page}
            onPageChange={(_, newPage) => setPage(newPage)}
            rowsPerPage={rowsPerPage}
            onRowsPerPageChange={(e) => setRowsPerPage(parseInt(e.target.value, 10))}
          />
        </Box>
      )}

      {/* Record Details Dialog */}
      <Dialog
        open={selectedRecord !== null && !isEditing}
        onClose={() => setSelectedRecord(null)}
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
            <Description />
            <Typography variant="h6">
              {selectedRecord?.title}
            </Typography>
          </Box>
        </DialogTitle>
        <DialogContent>
          {selectedRecord && (
            <Box>
              <Grid container spacing={2} sx={{ mb: 2 }}>
                <Grid item xs={12} sm={6}>
                  <Typography variant="body2"><strong>Type:</strong> {selectedRecord.type.replace('-', ' ')}</Typography>
                  <Typography variant="body2"><strong>Date:</strong> {format(selectedRecord.date, 'MMM dd, yyyy')}</Typography>
                  <Typography variant="body2"><strong>Provider:</strong> {selectedRecord.provider.name}</Typography>
                  <Typography variant="body2"><strong>Department:</strong> {selectedRecord.department}</Typography>
                </Grid>
                <Grid item xs={12} sm={6}>
                  <Typography variant="body2"><strong>Facility:</strong> {selectedRecord.facility}</Typography>
                  <Typography variant="body2"><strong>Created By:</strong> {selectedRecord.createdBy}</Typography>
                  <Typography variant="body2"><strong>Last Modified:</strong> {format(selectedRecord.lastModified, 'MMM dd, yyyy HH:mm')}</Typography>
                  {selectedRecord.encounterId && (
                    <Typography variant="body2"><strong>Encounter ID:</strong> {selectedRecord.encounterId}</Typography>
                  )}
                </Grid>
              </Grid>

              <Divider sx={{ my: 2 }} />

              <Typography variant="h6" fontWeight={600} mb={2}>
                Description
              </Typography>
              <Typography variant="body2" sx={{ mb: 2 }}>
                {selectedRecord.description}
              </Typography>

              {selectedRecord.vitalSigns && (
                <>
                  <Typography variant="h6" fontWeight={600} mb={2}>
                    Vital Signs
                  </Typography>
                  <VitalSignsDisplay vitalSigns={selectedRecord.vitalSigns} />
                  <Divider sx={{ my: 2 }} />
                </>
              )}

              {selectedRecord.attachments && selectedRecord.attachments.length > 0 && (
                <>
                  <Typography variant="h6" fontWeight={600} mb={2}>
                    Attachments
                  </Typography>
                  <List>
                    {selectedRecord.attachments.map(attachment => (
                      <ListItem key={attachment.id}>
                        <ListItemAvatar>
                          <Avatar sx={{ backgroundColor: alpha(theme.palette.primary.main, 0.1) }}>
                            {getAttachmentIcon(attachment.type)}
                          </Avatar>
                        </ListItemAvatar>
                        <ListItemText
                          primary={attachment.name}
                          secondary={
                            <Box>
                              <Typography variant="caption" color="textSecondary">
                                {formatFileSize(attachment.size)} • {attachment.type}
                              </Typography>
                              <Typography variant="caption" color="textSecondary" sx={{ display: 'block' }}>
                                Uploaded by {attachment.uploadedBy} on {format(attachment.uploadDate, 'MMM dd, yyyy')}
                              </Typography>
                            </Box>
                          }
                        />
                        <ListItemSecondaryAction>
                          <Tooltip title="Download">
                            <IconButton>
                              <Download />
                            </IconButton>
                          </Tooltip>
                        </ListItemSecondaryAction>
                      </ListItem>
                    ))}
                  </List>
                  <Divider sx={{ my: 2 }} />
                </>
              )}

              {selectedRecord.tags.length > 0 && (
                <>
                  <Typography variant="h6" fontWeight={600} mb={2}>
                    Tags
                  </Typography>
                  <Box display="flex" flexWrap="wrap" gap={1} sx={{ mb: 2 }}>
                    {selectedRecord.tags.map((tag, index) => (
                      <Chip
                        key={index}
                        label={tag}
                        size="small"
                        variant="outlined"
                      />
                    ))}
                  </Box>
                  <Divider sx={{ my: 2 }} />
                </>
              )}

              {selectedRecord.notes && (
                <>
                  <Typography variant="h6" fontWeight={600} mb={2}>
                    Notes
                  </Typography>
                  <Typography variant="body2" sx={{ mb: 2 }}>
                    {selectedRecord.notes}
                  </Typography>
                  <Divider sx={{ my: 2 }} />
                </>
              )}

              {selectedRecord.icdCodes && selectedRecord.icdCodes.length > 0 && (
                <>
                  <Typography variant="h6" fontWeight={600} mb={2}>
                    ICD Codes
                  </Typography>
                  <Box display="flex" flexWrap="wrap" gap={1} sx={{ mb: 2 }}>
                    {selectedRecord.icdCodes.map((code, index) => (
                      <Chip
                        key={index}
                        label={code}
                        size="small"
                        variant="outlined"
                      />
                    ))}
                  </Box>
                  <Divider sx={{ my: 2 }} />
                </>
              )}

              {selectedRecord.cptCodes && selectedRecord.cptCodes.length > 0 && (
                <>
                  <Typography variant="h6" fontWeight={600} mb={2}>
                    CPT Codes
                  </Typography>
                  <Box display="flex" flexWrap="wrap" gap={1} sx={{ mb: 2 }}>
                    {selectedRecord.cptCodes.map((code, index) => (
                      <Chip
                        key={index}
                        label={code}
                        size="small"
                        variant="outlined"
                      />
                    ))}
                  </Box>
                  <Divider sx={{ my: 2 }} />
                </>
              )}
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setSelectedRecord(null)}>Close</Button>
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

export default MedicalRecordViewer