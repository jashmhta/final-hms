import { render, screen, fireEvent } from '@testing-library/react'
import { axe, toHaveNoViolations } from 'jest-axe'
import { matchers } from '@emotion/jest'
import healthcareTheme, { healthcareColors } from '../../theme/healthcareTheme'
import { ThemeProvider, createTheme } from '@mui/material/styles'
import PatientCard from '../components/healthcare/PatientCard'

// Extend Jest matchers
expect.extend(toHaveNoViolations)
expect.extend(matchers)

describe('Frontend Visual Design Tests', () => {
  const mockPatient = {
    id: '1',
    firstName: 'John',
    lastName: 'Doe',
    dateOfBirth: '1990-01-15',
    gender: 'male',
    patientId: 'PAT-001',
    condition: 'stable',
    primaryPhysician: 'Dr. Smith',
    allergies: ['Penicillin'],
    medications: 3,
    status: 'admitted',
    room: '101',
    bed: 'A',
    lastVitals: {
      temperature: 98.6,
      bloodPressure: '120/80',
      heartRate: 72,
      oxygenSaturation: 98
    }
  }

  const renderWithTheme = (component) => {
    const theme = createTheme(healthcareTheme)
    return render(
      <ThemeProvider theme={theme}>
        {component}
      </ThemeProvider>
    )
  }

  test('Button component maintains consistent styling', () => {
    const { container } = renderWithTheme(
      <button style={{
        backgroundColor: healthcareColors.primary.main,
        color: healthcareColors.primary.contrastText,
        padding: '12px 24px',
        borderRadius: '8px',
        border: 'none',
        cursor: 'pointer',
        fontFamily: 'Inter, sans-serif',
        fontSize: '16px',
        fontWeight: '500'
      }}>
        Submit
      </button>
    )

    const button = screen.getByRole('button', { name: /submit/i })

    // Check exact styling compliance
    expect(button).toHaveStyle({
      backgroundColor: '#0066CC',
      color: '#FFFFFF',
      padding: '12px 24px',
      borderRadius: '8px',
      fontFamily: 'Inter, sans-serif',
      fontSize: '16px',
      fontWeight: '500',
      border: 'none',
      cursor: 'pointer'
    })

    // Check hover states
    fireEvent.mouseEnter(button)
    expect(button).toHaveStyle({
      backgroundColor: '#0066CC' // Primary color remains
    })

    // Check focus states
    fireEvent.focus(button)
    expect(button).toHaveStyle({
      outline: '2px solid #0066CC',
      outlineOffset: '2px'
    })
  })

  test('Typography system compliance', () => {
    const { container } = renderWithTheme(
      <div>
        <h1 style={{
          fontFamily: 'Inter, sans-serif',
          fontSize: '2.5rem',
          fontWeight: '700',
          lineHeight: '1.2',
          letterSpacing: '-0.02em'
        }}>
          Heading 1
        </h1>
        <h2 style={{
          fontFamily: 'Inter, sans-serif',
          fontSize: '2rem',
          fontWeight: '600',
          lineHeight: '1.3',
          letterSpacing: '-0.01em'
        }}>
          Heading 2
        </h2>
        <p style={{
          fontFamily: 'Inter, sans-serif',
          fontSize: '1rem',
          fontWeight: '400',
          lineHeight: '1.6',
          letterSpacing: '0'
        }}>
          Body text
        </p>
        <small style={{
          fontFamily: 'Inter, sans-serif',
          fontSize: '0.75rem',
          fontWeight: '400',
          lineHeight: '1.5',
          letterSpacing: '0'
        }}>
          Small text
        </small>
      </div>
    )

    // Check font family consistency
    expect(container).toHaveStyle({
      fontFamily: 'Inter, sans-serif'
    })

    // Check specific typography styles
    const h1 = screen.getByRole('heading', { level: 1 })
    expect(h1).toHaveStyle({
      fontSize: '2.5rem',
      fontWeight: '700',
      lineHeight: '1.2',
      letterSpacing: '-0.02em'
    })

    const h2 = screen.getByRole('heading', { level: 2 })
    expect(h2).toHaveStyle({
      fontSize: '2rem',
      fontWeight: '600',
      lineHeight: '1.3',
      letterSpacing: '-0.01em'
    })

    const bodyText = screen.getByText('Body text')
    expect(bodyText).toHaveStyle({
      fontSize: '1rem',
      fontWeight: '400',
      lineHeight: '1.6',
      letterSpacing: '0'
    })

    const smallText = screen.getByText('Small text')
    expect(smallText).toHaveStyle({
      fontSize: '0.75rem',
      fontWeight: '400',
      lineHeight: '1.5',
      letterSpacing: '0'
    })
  })

  test('Color system consistency', () => {
    const { container } = renderWithTheme(
      <div>
        <div style={{
          backgroundColor: healthcareColors.success.main,
          color: healthcareColors.success.contrastText,
          padding: '8px 16px',
          borderRadius: '16px',
          display: 'inline-block',
          fontWeight: '500'
        }}>
          Active
        </div>
        <div style={{
          backgroundColor: healthcareColors.warning.main,
          color: healthcareColors.warning.contrastText,
          padding: '8px 16px',
          borderRadius: '16px',
          display: 'inline-block',
          fontWeight: '500'
        }}>
          Pending
        </div>
        <div style={{
          backgroundColor: healthcareColors.error.main,
          color: healthcareColors.error.contrastText,
          padding: '8px 16px',
          borderRadius: '16px',
          display: 'inline-block',
          fontWeight: '500'
        }}>
          Critical
        </div>
      </div>
    )

    // Check semantic color usage
    expect(screen.getByText('Active')).toHaveStyle({
      backgroundColor: '#10B981',
      color: '#FFFFFF'
    })

    expect(screen.getByText('Pending')).toHaveStyle({
      backgroundColor: '#F59E0B',
      color: '#1F2937'
    })

    expect(screen.getByText('Critical')).toHaveStyle({
      backgroundColor: '#DC2626',
      color: '#FFFFFF'
    })
  })

  test('Spacing and layout consistency', () => {
    const { container } = renderWithTheme(
      <div style={{ display: 'flex', gap: '12px' }}>
        <button style={{
          backgroundColor: healthcareColors.primary.main,
          color: healthcareColors.primary.contrastText,
          padding: '12px 24px',
          borderRadius: '8px',
          border: 'none',
          cursor: 'pointer'
        }}>
          Primary Action
        </button>
        <button style={{
          backgroundColor: 'transparent',
          color: healthcareColors.primary.main,
          padding: '12px 24px',
          borderRadius: '8px',
          border: `1px solid ${healthcareColors.primary.main}`,
          cursor: 'pointer'
        }}>
          Secondary Action
        </button>
      </div>
    )

    const buttons = screen.getAllByRole('button')

    // Check consistent padding
    buttons.forEach(button => {
      expect(button).toHaveStyle({
        padding: '12px 24px'
      })
    })

    // Check consistent border radius
    buttons.forEach(button => {
      expect(button).toHaveStyle({
        borderRadius: '8px'
      })
    })
  })

  test('Patient Card visual design compliance', () => {
    const mockOnViewDetails = jest.fn()

    const { container } = renderWithTheme(
      <PatientCard
        patient={mockPatient}
        onViewDetails={mockOnViewDetails}
      />
    )

    // Check card renders with proper structure
    expect(screen.getByText('John Doe')).toBeInTheDocument()
    expect(screen.getByText('PAT-001')).toBeInTheDocument()
    expect(screen.getByText('stable')).toBeInTheDocument()
    expect(screen.getByText('admitted')).toBeInTheDocument()

    // Check color system usage
    const stableChip = screen.getByText('stable')
    expect(stableChip).toHaveStyle({
      backgroundColor: 'rgba(0, 102, 204, 0.1)', // alpha(primary.main, 0.1)
      color: '#0066CC' // primary.main
    })

    // Check typography consistency
    const patientName = screen.getByText('John Doe')
    expect(patientName).toHaveStyle({
      fontFamily: 'Inter, sans-serif',
      fontWeight: '600'
    })

    // Check spacing and layout
    const card = container.querySelector('.MuiCard-root')
    expect(card).toHaveStyle({
      borderRadius: '12px',
      border: '1px solid rgba(226, 232, 240, 0.5)',
      transition: 'all 0.2s ease-in-out'
    })
  })

  test('Healthcare color palette consistency', () => {
    const { container } = renderWithTheme(
      <div>
        <div style={{ backgroundColor: healthcareColors.clinical.emergency, padding: '8px' }}>
          Emergency
        </div>
        <div style={{ backgroundColor: healthcareColors.clinical.critical, padding: '8px' }}>
          Critical
        </div>
        <div style={{ backgroundColor: healthcareColors.clinical.normal, padding: '8px' }}>
          Normal
        </div>
        <div style={{ backgroundColor: healthcareColors.departments.emergency, padding: '8px' }}>
          Emergency Dept
        </div>
        <div style={{ backgroundColor: healthcareColors.departments.icu, padding: '8px' }}>
          ICU
        </div>
      </div>
    )

    expect(screen.getByText('Emergency')).toHaveStyle({
      backgroundColor: '#DC2626'
    })

    expect(screen.getByText('Critical')).toHaveStyle({
      backgroundColor: '#F59E0B'
    })

    expect(screen.getByText('Normal')).toHaveStyle({
      backgroundColor: '#10B981'
    })

    expect(screen.getByText('Emergency Dept')).toHaveStyle({
      backgroundColor: '#DC2626'
    })

    expect(screen.getByText('ICU')).toHaveStyle({
      backgroundColor: '#8B5CF6'
    })
  })

  test('Visual consistency across different states', () => {
    const mockOnViewDetails = jest.fn()

    // Test emergency patient
    const emergencyPatient = { ...mockPatient, isEmergency: true, condition: 'critical' }

    const { container, rerender } = renderWithTheme(
      <PatientCard
        patient={emergencyPatient}
        onViewDetails={mockOnViewDetails}
      />
    )

    const emergencyCard = container.querySelector('.MuiCard-root')
    expect(emergencyCard).toHaveStyle({
      border: '2px solid #DC2626' // error.main for emergency
    })

    // Test discharged patient
    const dischargedPatient = { ...mockPatient, status: 'discharged' }
    rerender(
      <PatientCard
        patient={dischargedPatient}
        onViewDetails={mockOnViewDetails}
      />
    )

    const dischargedCard = container.querySelector('.MuiCard-root')
    expect(dischargedCard).toHaveStyle({
      border: '1px solid rgba(226, 232, 240, 0.5)' // default border
    })
  })

  test('No accessibility violations in visual design', async () => {
    const { container } = renderWithTheme(
      <div>
        <h1>Patient Dashboard</h1>
        <button aria-label="Add patient">Add Patient</button>
        <div role="status">Loading patient data...</div>
        <nav aria-label="Main navigation">
          <ul>
            <li><a href="#dashboard">Dashboard</a></li>
            <li><a href="#patients">Patients</a></li>
            <li><a href="#appointments">Appointments</a></li>
          </ul>
        </nav>
      </div>
    )

    const results = await axe(container)
    expect(results).toHaveNoViolations()
  })

  test('Visual hierarchy and contrast compliance', () => {
    const { container } = renderWithTheme(
      <div>
        <h1 style={{ color: healthcareColors.text.primary }}>Main Title</h1>
        <h2 style={{ color: healthcareColors.text.secondary }}>Subtitle</h2>
        <p style={{ color: healthcareColors.text.primary }}>Body content</p>
        <small style={{ color: healthcareColors.text.disabled }}>Secondary info</small>
      </div>
    )

    expect(screen.getByText('Main Title')).toHaveStyle({
      color: '#0F172A' // text.primary
    })

    expect(screen.getByText('Subtitle')).toHaveStyle({
      color: '#475569' // text.secondary
    })

    expect(screen.getByText('Body content')).toHaveStyle({
      color: '#0F172A' // text.primary
    })

    expect(screen.getByText('Secondary info')).toHaveStyle({
      color: '#94A3B8' // text.disabled
    })
  })

  test('Interactive element states and transitions', () => {
    const { container } = renderWithTheme(
      <button style={{
        backgroundColor: healthcareColors.primary.main,
        color: healthcareColors.primary.contrastText,
        padding: '12px 24px',
        borderRadius: '8px',
        border: 'none',
        cursor: 'pointer',
        transition: 'all 0.2s ease-in-out',
        transform: 'none'
      }}>
        Interactive Button
      </button>
    )

    const button = screen.getByRole('button', { name: /interactive button/i })

    // Check initial state
    expect(button).toHaveStyle({
      transform: 'none',
      transition: 'all 0.2s ease-in-out'
    })

    // Test hover state
    fireEvent.mouseEnter(button)
    expect(button).toHaveStyle({
      transform: 'translateY(-1px)'
    })

    // Test active state
    fireEvent.mouseDown(button)
    expect(button).toHaveStyle({
      transform: 'translateY(0px)'
    })

    // Test focus state
    fireEvent.focus(button)
    expect(button).toHaveStyle({
      outline: '2px solid #0066CC',
      outlineOffset: '2px'
    })
  })
})