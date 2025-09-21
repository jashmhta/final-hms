import React, { useState, useMemo } from 'react'
import {
  Box,
  Typography,
  TextField,
  InputAdornment,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Grid,
  Card,
  CardContent,
  Button,
  Pagination,
  Chip,
  useTheme,
} from '@mui/material'
import {
  Search as SearchIcon,
  Add as AddIcon,
  FilterList as FilterIcon,
  Sort as SortIcon,
} from '@mui/icons-material'
import { useTranslation } from 'react-i18next'
import { useSelector, useDispatch } from 'react-redux'
import { RootState } from '../../../store/store'
import {
  selectPatients,
  selectPatientsLoading,
  selectPatientsFilters,
  selectPatientsPagination,
  setFilters,
  setPagination,
} from '../../../store/slices/patientsSlice'
import PatientCard from './PatientCard'

const PatientList: React.FC = () => {
  const { t } = useTranslation()
  const theme = useTheme()
  const dispatch = useDispatch()

  const patients = useSelector(selectPatients)
  const loading = useSelector(selectPatientsLoading)
  const filters = useSelector(selectPatientsFilters)
  const pagination = useSelector(selectPatientsPagination)

  const [searchTerm, setSearchTerm] = useState(filters.search)
  const [statusFilter, setStatusFilter] = useState(filters.status)

  // Filter and search patients
  const filteredPatients = useMemo(() => {
    return patients.filter((patient) => {
      const matchesSearch = !searchTerm ||
        patient.firstName.toLowerCase().includes(searchTerm.toLowerCase()) ||
        patient.lastName.toLowerCase().includes(searchTerm.toLowerCase()) ||
        patient.medicalRecordNumber.toLowerCase().includes(searchTerm.toLowerCase()) ||
        patient.email.toLowerCase().includes(searchTerm.toLowerCase())

      const matchesStatus = !statusFilter || statusFilter === 'all' ||
        (statusFilter === 'active' && patient.isActive) ||
        (statusFilter === 'inactive' && !patient.isActive)

      return matchesSearch && matchesStatus
    })
  }, [patients, searchTerm, statusFilter])

  // Paginate patients
  const paginatedPatients = useMemo(() => {
    const startIndex = (pagination.page - 1) * pagination.limit
    const endIndex = startIndex + pagination.limit
    return filteredPatients.slice(startIndex, endIndex)
  }, [filteredPatients, pagination.page, pagination.limit])

  const handleSearchChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setSearchTerm(event.target.value)
    dispatch(setFilters({ search: event.target.value }))
  }

  const handleStatusChange = (event: React.ChangeEvent<{ value: unknown }>) => {
    const newStatus = event.target.value as string
    setStatusFilter(newStatus)
    dispatch(setFilters({ status: newStatus }))
    dispatch(setPagination({ page: 1 })) // Reset to first page
  }

  const handlePageChange = (event: React.ChangeEvent<unknown>, value: number) => {
    dispatch(setPagination({ page: value }))
  }

  const totalPages = Math.ceil(filteredPatients.length / pagination.limit)

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '400px' }}>
        <Typography>{t('common.loading')}</Typography>
      </Box>
    )
  }

  return (
    <Box>
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          {t('patients.title')}
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Manage patient records and information
        </Typography>
      </Box>

      {/* Search and Filters */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Grid container spacing={2} alignItems="center">
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                placeholder={t('patients.searchPatients')}
                value={searchTerm}
                onChange={handleSearchChange}
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <SearchIcon />
                    </InputAdornment>
                  ),
                }}
                size="small"
              />
            </Grid>
            <Grid item xs={12} md={3}>
              <FormControl fullWidth size="small">
                <InputLabel id="status-filter-label">
                  {t('common.status')}
                </InputLabel>
                <Select
                  labelId="status-filter-label"
                  value={statusFilter}
                  onChange={handleStatusChange}
                  label={t('common.status')}
                >
                  <MenuItem value="all">{t('common.selectAll')}</MenuItem>
                  <MenuItem value="active">{t('common.active')}</MenuItem>
                  <MenuItem value="inactive">{t('common.inactive')}</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={3}>
              <Button
                fullWidth
                variant="contained"
                startIcon={<AddIcon />}
                size="medium"
              >
                {t('patients.addPatient')}
              </Button>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Results Summary */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="body2" color="text.secondary">
          Showing {paginatedPatients.length} of {filteredPatients.length} patients
        </Typography>
        <Chip
          icon={<FilterIcon />}
          label={`${filters.search ? 'Search: ' + filters.search : 'No filters'}${
            filters.status !== 'all' ? ', Status: ' + filters.status : ''
          }`}
          size="small"
          variant="outlined"
        />
      </Box>

      {/* Patient Grid */}
      <Grid container spacing={3}>
        {paginatedPatients.map((patient) => (
          <Grid item xs={12} sm={6} md={4} lg={3} key={patient.id}>
            <PatientCard
              patient={patient}
              onView={(patient) => console.log('View patient:', patient)}
              onEdit={(patient) => console.log('Edit patient:', patient)}
            />
          </Grid>
        ))}
      </Grid>

      {/* Empty State */}
      {paginatedPatients.length === 0 && (
        <Card sx={{ textAlign: 'center', py: 8 }}>
          <CardContent>
            <Typography variant="h6" color="text.secondary">
              {t('patients.noPatientsFound')}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Try adjusting your search criteria or add a new patient.
            </Typography>
          </CardContent>
        </Card>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
          <Pagination
            count={totalPages}
            page={pagination.page}
            onChange={handlePageChange}
            color="primary"
            showFirstButton
            showLastButton
          />
        </Box>
      )}
    </Box>
  )
}

export default PatientList