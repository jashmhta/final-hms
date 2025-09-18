import React from 'react'
import { render, screen, fireEvent } from '@testing-library/react'
import { ThemeProvider, createTheme } from '@mui/material/styles'
import { CssBaseline } from '@mui/material'
import DashboardModule from '../modules/DashboardModule'
const theme = createTheme({
  palette: {
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
  },
})
const renderWithTheme = (component: React.ReactElement) => {
  return render(
    <ThemeProvider theme={theme}>
      <CssBaseline />
      {component}
    </ThemeProvider>
  )
}
describe('DashboardModule', () => {
  test('renders dashboard header', () => {
    renderWithTheme(<DashboardModule />)
    expect(screen.getByText('Healthcare Management System')).toBeInTheDocument()
  })
  test('renders total patients card', () => {
    renderWithTheme(<DashboardModule />)
    expect(screen.getByText('Total Patients')).toBeInTheDocument()
    expect(screen.getByText('1,247')).toBeInTheDocument()
  })
  test('renders appointments card', () => {
    renderWithTheme(<DashboardModule />)
    expect(screen.getByText('Appointments Today')).toBeInTheDocument()
    expect(screen.getByText('84')).toBeInTheDocument()
  })
  test('renders available beds card', () => {
    renderWithTheme(<DashboardModule />)
    expect(screen.getByText('Available Beds')).toBeInTheDocument()
    expect(screen.getByText('23/150')).toBeInTheDocument()
  })
  test('renders staff on duty card', () => {
    renderWithTheme(<DashboardModule />)
    expect(screen.getByText('Staff On Duty')).toBeInTheDocument()
    expect(screen.getByText('67')).toBeInTheDocument()
  })
  test('renders system status alert', () => {
    renderWithTheme(<DashboardModule />)
    expect(screen.getByText(/System Status: All services operational/)).toBeInTheDocument()
  })
  test('renders navigation menu items', () => {
    renderWithTheme(<DashboardModule />)
    const patientsNav = screen.getAllByText('Patients')[0] 
    const appointmentsNav = screen.getAllByText('Appointments')[0] 
    const medicalRecordsNav = screen.getAllByText('Medical Records')[0] 
    expect(patientsNav).toBeInTheDocument()
    expect(appointmentsNav).toBeInTheDocument()
    expect(medicalRecordsNav).toBeInTheDocument()
  })
  test('tab switching works', () => {
    renderWithTheme(<DashboardModule />)
    expect(screen.getByText('Total Patients')).toBeInTheDocument()
    const analyticsTab = screen.getByRole('tab', { name: 'Analytics' })
    fireEvent.click(analyticsTab)
    expect(screen.getByText('Department Performance Metrics')).toBeInTheDocument()
  })
  test('renders charts in overview tab', () => {
    renderWithTheme(<DashboardModule />)
    expect(screen.getByText('Patient Admissions Trend')).toBeInTheDocument()
    expect(screen.getByText('Department Distribution')).toBeInTheDocument()
  })
  test('renders online status chip', () => {
    renderWithTheme(<DashboardModule />)
    expect(screen.getByText('Online')).toBeInTheDocument()
  })
  test('mobile menu button is present', () => {
    renderWithTheme(<DashboardModule />)
    const menuButton = screen.getByRole('button', { name: /open drawer/i })
    expect(menuButton).toBeInTheDocument()
  })
})