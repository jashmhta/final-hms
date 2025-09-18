import React, { useState, useCallback } from 'react'
import {
  Box,
  Paper,
  Typography,
  Button,
  Chip,
  IconButton,
  Tooltip,
  Badge,
  useTheme,
  alpha,
} from '@mui/material'
import {
  CalendarToday,
  Today,
  ChevronLeft,
  ChevronRight,
  Add,
  FilterList,
  ViewWeek,
  ViewDay,
  ViewAgenda,
  Person,
  LocalHospital,
  AccessTime,
  VideoCameraFront,
  Phone,
  LocationOn,
} from '@mui/icons-material'
import { format, addDays, subDays, startOfWeek, endOfWeek, eachDayOfInterval, isToday, isSameDay } from 'date-fns'

export interface Appointment {
  id: string
  title: string
  patient: {
    id: string
    name: string
    age: number
    gender: string
  }
  physician: {
    id: string
    name: string
    specialty: string
  }
  startTime: Date
  endTime: Date
  type: 'in-person' | 'video' | 'phone' | 'follow-up' | 'consultation' | 'procedure' | 'emergency'
  status: 'scheduled' | 'confirmed' | 'in-progress' | 'completed' | 'cancelled' | 'no-show'
  priority: 'low' | 'normal' | 'high' | 'urgent' | 'emergency'
  location?: string
  notes?: string
  reminders: boolean
  telemedicineLink?: string
}

interface AppointmentCalendarProps {
  appointments: Appointment[]
  onAppointmentClick: (appointment: Appointment) => void
  onAppointmentCreate: (date: Date, time?: string) => void
  onDateChange: (date: Date) => void
  onViewChange: (view: 'day' | 'week' | 'month') => void
  className?: string
}

const AppointmentCalendar: React.FC<AppointmentCalendarProps> = ({
  appointments,
  onAppointmentClick,
  onAppointmentCreate,
  onDateChange,
  onViewChange,
  className,
}) => {
  const theme = useTheme()
  const [currentDate, setCurrentDate] = useState(new Date())
  const [viewMode, setViewMode] = useState<'day' | 'week' | 'month'>('week')
  const [selectedFilter, setSelectedFilter] = useState<string>('all')

  const getAppointmentColor = (appointment: Appointment) => {
    const statusColors = {
      scheduled: theme.palette.info.main,
      confirmed: theme.palette.success.main,
      'in-progress': theme.palette.warning.main,
      completed: theme.palette.primary.main,
      cancelled: theme.palette.error.main,
      'no-show': theme.palette.grey[500],
    }
    return statusColors[appointment.status] || theme.palette.grey[500]
  }

  const getAppointmentTypeIcon = (type: string) => {
    const icons = {
      'in-person': <LocationOn fontSize="small" />,
      video: <VideoCameraFront fontSize="small" />,
      phone: <Phone fontSize="small" />,
      'follow-up': <AccessTime fontSize="small" />,
      consultation: <Person fontSize="small" />,
      procedure: <LocalHospital fontSize="small" />,
      emergency: <LocalHospital fontSize="small" />,
    }
    return icons[type as keyof typeof icons] || <CalendarToday fontSize="small" />
  }

  const getPriorityColor = (priority: string) => {
    const colors = {
      low: theme.palette.success.main,
      normal: theme.palette.info.main,
      high: theme.palette.warning.main,
      urgent: theme.palette.error.main,
      emergency: theme.palette.error.main,
    }
    return colors[priority as keyof typeof colors] || theme.palette.grey[500]
  }

  const navigateDate = useCallback((direction: 'prev' | 'next') => {
    const newDate = direction === 'prev' ? subDays(currentDate, viewMode === 'week' ? 7 : 1) : addDays(currentDate, viewMode === 'week' ? 7 : 1)
    setCurrentDate(newDate)
    onDateChange(newDate)
  }, [currentDate, viewMode, onDateChange])

  const goToToday = useCallback(() => {
    setCurrentDate(new Date())
    onDateChange(new Date())
  }, [onDateChange])

  const handleViewChange = (view: 'day' | 'week' | 'month') => {
    setViewMode(view)
    onViewChange(view)
  }

  const getWeekDates = () => {
    const start = startOfWeek(currentDate, { weekStartsOn: 0 })
    const end = endOfWeek(currentDate, { weekStartsOn: 0 })
    return eachDayOfInterval({ start, end })
  }

  const getFilteredAppointments = () => {
    if (selectedFilter === 'all') return appointments

    const filterMap: Record<string, (appt: Appointment) => boolean> = {
      'today': (appt) => isToday(appt.startTime),
      'urgent': (appt) => ['urgent', 'emergency'].includes(appt.priority),
      'video': (appt) => appt.type === 'video',
      'in-person': (appt) => appt.type === 'in-person',
      'confirmed': (appt) => appt.status === 'confirmed',
      'pending': (appt) => ['scheduled', 'no-show'].includes(appt.status),
    }

    return appointments.filter(filterMap[selectedFilter] || (() => true))
  }

  const getAppointmentsForDate = (date: Date) => {
    return getFilteredAppointments().filter(appt => isSameDay(appt.startTime, date))
  }

  const getTimeSlots = () => {
    const slots = []
    for (let hour = 8; hour <= 17; hour++) {
      for (let minute = 0; minute < 60; minute += 30) {
        slots.push(`${hour.toString().padStart(2, '0')}:${minute.toString().padStart(2, '0')}`)
      }
    }
    return slots
  }

  const renderWeekView = () => {
    const weekDays = getWeekDates()
    const timeSlots = getTimeSlots()

    return (
      <Box sx={{ overflowX: 'auto' }}>
        <Box sx={{ minWidth: 1200 }}>
          {/* Header */}
          <Box sx={{ display: 'flex', borderBottom: `2px solid ${theme.palette.divider}`, backgroundColor: theme.palette.background.paper }}>
            <Box sx={{ width: 80, p: 2, borderRight: `1px solid ${theme.palette.divider}` }}>
              <Typography variant="caption" fontWeight={600}>Time</Typography>
            </Box>
            {weekDays.map(day => (
              <Box key={day.toString()} sx={{ flex: 1, p: 2, textAlign: 'center', borderRight: `1px solid ${theme.palette.divider}` }}>
                <Typography variant="caption" fontWeight={600}>
                  {format(day, 'EEE')}
                </Typography>
                <Typography
                  variant="h6"
                  fontWeight={600}
                  color={isToday(day) ? theme.palette.primary.main : 'text.primary'}
                >
                  {format(day, 'd')}
                </Typography>
              </Box>
            ))}
          </Box>

          {/* Time Grid */}
          <Box sx={{ backgroundColor: theme.palette.background.default }}>
            {timeSlots.map(timeSlot => (
              <Box key={timeSlot} sx={{ display: 'flex', borderBottom: `1px solid ${alpha(theme.palette.divider, 0.5)}` }}>
                <Box sx={{ width: 80, p: 2, borderRight: `1px solid ${theme.palette.divider}`, backgroundColor: theme.palette.background.paper }}>
                  <Typography variant="caption" color="textSecondary">
                    {timeSlot}
                  </Typography>
                </Box>
                {weekDays.map(day => {
                  const dayAppointments = getAppointmentsForDate(day).filter(appt => {
                    const apptTime = format(appt.startTime, 'HH:mm')
                    return apptTime === timeSlot
                  })

                  return (
                    <Box
                      key={`${day.toString()}-${timeSlot}`}
                      sx={{
                        flex: 1,
                        p: 1,
                        borderRight: `1px solid ${theme.palette.divider}`,
                        minHeight: 60,
                        backgroundColor: alpha(theme.palette.background.paper, 0.5),
                        '&:hover': {
                          backgroundColor: alpha(theme.palette.primary.main, 0.05),
                        },
                        cursor: 'pointer',
                      }}
                      onClick={() => onAppointmentCreate(day, timeSlot)}
                    >
                      {dayAppointments.map(appointment => (
                        <Box
                          key={appointment.id}
                          sx={{
                            p: 1,
                            mb: 0.5,
                            backgroundColor: alpha(getAppointmentColor(appointment), 0.1),
                            border: `1px solid ${alpha(getAppointmentColor(appointment), 0.3)}`,
                            borderRadius: 1,
                            cursor: 'pointer',
                            '&:hover': {
                              backgroundColor: alpha(getAppointmentColor(appointment), 0.2),
                            },
                          }}
                          onClick={(e) => {
                            e.stopPropagation()
                            onAppointmentClick(appointment)
                          }}
                        >
                          <Box display="flex" alignItems="center" gap={1} mb={0.5}>
                            {getAppointmentTypeIcon(appointment.type)}
                            <Typography variant="caption" fontWeight={600} noWrap>
                              {appointment.title}
                            </Typography>
                            {appointment.priority !== 'normal' && (
                              <Box
                                sx={{
                                  width: 8,
                                  height: 8,
                                  borderRadius: '50%',
                                  backgroundColor: getPriorityColor(appointment.priority),
                                }}
                              />
                            )}
                          </Box>
                          <Typography variant="caption" color="textSecondary" noWrap>
                            {appointment.patient.name}
                          </Typography>
                          <Typography variant="caption" color="textSecondary" noWrap>
                            Dr. {appointment.physician.name}
                          </Typography>
                        </Box>
                      ))}
                    </Box>
                  )
                })}
              </Box>
            ))}
          </Box>
        </Box>
      </Box>
    )
  }

  const renderDayView = () => {
    const dayAppointments = getAppointmentsForDate(currentDate)
    const timeSlots = getTimeSlots()

    return (
      <Box sx={{ maxWidth: 800, mx: 'auto' }}>
        <Box sx={{ mb: 3, textAlign: 'center' }}>
          <Typography variant="h4" fontWeight={600}>
            {format(currentDate, 'EEEE, MMMM d, yyyy')}
          </Typography>
        </Box>

        {timeSlots.map(timeSlot => {
          const slotAppointments = dayAppointments.filter(appt =>
            format(appt.startTime, 'HH:mm') === timeSlot
          )

          return (
            <Box key={timeSlot} sx={{ display: 'flex', mb: 2 }}>
              <Box sx={{ width: 100, pt: 1 }}>
                <Typography variant="caption" color="textSecondary">
                  {timeSlot}
                </Typography>
              </Box>
              <Box
                sx={{
                  flex: 1,
                  minHeight: 60,
                  backgroundColor: alpha(theme.palette.background.paper, 0.5),
                  borderRadius: 1,
                  p: 1,
                  border: `1px dashed ${theme.palette.divider}`,
                  cursor: 'pointer',
                  '&:hover': {
                    backgroundColor: alpha(theme.palette.primary.main, 0.05),
                  },
                }}
                onClick={() => onAppointmentCreate(currentDate, timeSlot)}
              >
                {slotAppointments.map(appointment => (
                  <Box
                    key={appointment.id}
                    sx={{
                      p: 1.5,
                      mb: 1,
                      backgroundColor: alpha(getAppointmentColor(appointment), 0.1),
                      border: `1px solid ${alpha(getAppointmentColor(appointment), 0.3)}`,
                      borderRadius: 1,
                      cursor: 'pointer',
                      '&:hover': {
                        backgroundColor: alpha(getAppointmentColor(appointment), 0.2),
                      },
                    }}
                    onClick={(e) => {
                      e.stopPropagation()
                      onAppointmentClick(appointment)
                    }}
                  >
                    <Box display="flex" justifyContent="space-between" alignItems="start" mb={1}>
                      <Typography variant="subtitle2" fontWeight={600}>
                        {appointment.title}
                      </Typography>
                      <Box display="flex" alignItems="center" gap={1}>
                        {getAppointmentTypeIcon(appointment.type)}
                        {appointment.priority !== 'normal' && (
                          <Box
                            sx={{
                              width: 8,
                              height: 8,
                              borderRadius: '50%',
                              backgroundColor: getPriorityColor(appointment.priority),
                            }}
                          />
                        )}
                      </Box>
                    </Box>

                    <Box display="flex" alignItems="center" gap={2} mb={1}>
                      <Typography variant="caption" color="textSecondary">
                        {appointment.patient.name}, {appointment.patient.age}y
                      </Typography>
                      <Typography variant="caption" color="textSecondary">
                        Dr. {appointment.physician.name}
                      </Typography>
                    </Box>

                    {appointment.location && (
                      <Box display="flex" alignItems="center" gap={1}>
                        <LocationOn fontSize="small" />
                        <Typography variant="caption" color="textSecondary">
                          {appointment.location}
                        </Typography>
                      </Box>
                    )}

                    <Box display="flex" alignItems="center" gap={1} mt={1}>
                      <Chip
                        label={appointment.status}
                        size="small"
                        sx={{
                          backgroundColor: alpha(getAppointmentColor(appointment), 0.1),
                          color: getAppointmentColor(appointment),
                          fontSize: '0.7rem',
                          height: 20,
                        }}
                      />
                      <Typography variant="caption" color="textSecondary">
                        {format(appointment.startTime, 'HH:mm')} - {format(appointment.endTime, 'HH:mm')}
                      </Typography>
                    </Box>
                  </Box>
                ))}
              </Box>
            </Box>
          )
        })}
      </Box>
    )
  }

  const renderMonthView = () => {
    const monthDays = eachDayOfInterval({
      start: startOfWeek(startOfWeek(currentDate, { weekStartsOn: 0 }), { weekStartsOn: 0 }),
      end: endOfWeek(endOfWeek(currentDate, { weekStartsOn: 0 }), { weekStartsOn: 0 }),
    })

    return (
      <Box sx={{ p: 2 }}>
        <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(7, 1fr)', gap: 1 }}>
          {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map(day => (
            <Box key={day} sx={{ textAlign: 'center', p: 1 }}>
              <Typography variant="caption" fontWeight={600}>
                {day}
              </Typography>
            </Box>
          ))}

          {monthDays.map(day => {
            const dayAppointments = getAppointmentsForDate(day)

            return (
              <Box
                key={day.toString()}
                sx={{
                  minHeight: 100,
                  border: `1px solid ${theme.palette.divider}`,
                  borderRadius: 1,
                  p: 1,
                  backgroundColor: isToday(day)
                    ? alpha(theme.palette.primary.main, 0.05)
                    : 'transparent',
                  cursor: 'pointer',
                  '&:hover': {
                    backgroundColor: alpha(theme.palette.primary.main, 0.1),
                  },
                }}
                onClick={() => onAppointmentCreate(day)}
              >
                <Typography
                  variant="caption"
                  fontWeight={600}
                  color={isToday(day) ? theme.palette.primary.main : 'text.primary'}
                  sx={{ display: 'block', mb: 1 }}
                >
                  {format(day, 'd')}
                </Typography>

                {dayAppointments.slice(0, 3).map(appointment => (
                  <Box
                    key={appointment.id}
                    sx={{
                      p: 0.5,
                      mb: 0.5,
                      backgroundColor: alpha(getAppointmentColor(appointment), 0.1),
                      border: `1px solid ${alpha(getAppointmentColor(appointment), 0.3)}`,
                      borderRadius: 0.5,
                      fontSize: '0.7rem',
                      lineHeight: 1.2,
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      whiteSpace: 'nowrap',
                    }}
                    onClick={(e) => {
                      e.stopPropagation()
                      onAppointmentClick(appointment)
                    }}
                  >
                    {appointment.title}
                  </Box>
                ))}

                {dayAppointments.length > 3 && (
                  <Typography variant="caption" color="textSecondary">
                    +{dayAppointments.length - 3} more
                  </Typography>
                )}
              </Box>
            )
          })}
        </Box>
      </Box>
    )
  }

  const filterOptions = [
    { id: 'all', label: 'All Appointments', count: appointments.length },
    { id: 'today', label: 'Today', count: appointments.filter(appt => isToday(appt.startTime)).length },
    { id: 'urgent', label: 'Urgent', count: appointments.filter(appt => ['urgent', 'emergency'].includes(appt.priority)).length },
    { id: 'video', label: 'Video Calls', count: appointments.filter(appt => appt.type === 'video').length },
    { id: 'in-person', label: 'In-Person', count: appointments.filter(appt => appt.type === 'in-person').length },
    { id: 'confirmed', label: 'Confirmed', count: appointments.filter(appt => appt.status === 'confirmed').length },
    { id: 'pending', label: 'Pending', count: appointments.filter(appt => ['scheduled', 'no-show'].includes(appt.status)).length },
  ]

  return (
    <Paper className={className} sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Typography variant="h4" fontWeight={600}>
            {viewMode === 'day' ? format(currentDate, 'MMMM d, yyyy') : format(currentDate, 'MMMM yyyy')}
          </Typography>
          <Box sx={{ display: 'flex', gap: 1 }}>
            <IconButton onClick={() => navigateDate('prev')} size="small">
              <ChevronLeft />
            </IconButton>
            <Button
              variant="outlined"
              size="small"
              startIcon={<Today />}
              onClick={goToToday}
            >
              Today
            </Button>
            <IconButton onClick={() => navigateDate('next')} size="small">
              <ChevronRight />
            </IconButton>
          </Box>
        </Box>

        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Box sx={{ display: 'flex', gap: 1 }}>
            <Tooltip title="Day View">
              <IconButton
                size="small"
                color={viewMode === 'day' ? 'primary' : 'default'}
                onClick={() => handleViewChange('day')}
              >
                <ViewDay />
              </IconButton>
            </Tooltip>
            <Tooltip title="Week View">
              <IconButton
                size="small"
                color={viewMode === 'week' ? 'primary' : 'default'}
                onClick={() => handleViewChange('week')}
              >
                <ViewWeek />
              </IconButton>
            </Tooltip>
            <Tooltip title="Month View">
              <IconButton
                size="small"
                color={viewMode === 'month' ? 'primary' : 'default'}
                onClick={() => handleViewChange('month')}
              >
                <ViewAgenda />
              </IconButton>
            </Tooltip>
          </Box>

          <Button
            variant="contained"
            startIcon={<Add />}
            onClick={() => onAppointmentCreate(currentDate)}
          >
            New Appointment
          </Button>
        </Box>
      </Box>

      {/* Filters */}
      <Box sx={{ display: 'flex', gap: 1, mb: 3, flexWrap: 'wrap' }}>
        {filterOptions.map(option => (
          <Chip
            key={option.id}
            label={`${option.label} (${option.count})`}
            clickable
            color={selectedFilter === option.id ? 'primary' : 'default'}
            variant={selectedFilter === option.id ? 'filled' : 'outlined'}
            onClick={() => setSelectedFilter(option.id)}
            size="small"
          />
        ))}
      </Box>

      {/* Calendar Content */}
      <Box sx={{ minHeight: 600 }}>
        {viewMode === 'week' && renderWeekView()}
        {viewMode === 'day' && renderDayView()}
        {viewMode === 'month' && renderMonthView()}
      </Box>
    </Paper>
  )
}

export default AppointmentCalendar