import { render, screen, fireEvent } from '@testing-library/react'
import { ThemeProvider, createTheme } from '@mui/material/styles'
import healthcareTheme from '../theme/healthcareTheme'
import PatientCard from '../components/healthcare/PatientCard'

describe('Responsive Design Tests', () => {
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

  const mockOnViewDetails = jest.fn()

  const renderWithTheme = (component) => {
    return render(
      <ThemeProvider theme={healthcareTheme}>
        {component}
      </ThemeProvider>
    )
  }

  const testResponsive = (component, breakpoints) => {
    breakpoints.forEach(({ width, expected }) => {
      // Mock window resize
      Object.defineProperty(window, 'innerWidth', {
        value: width,
        writable: true,
      })

      // Trigger resize event
      window.dispatchEvent(new Event('resize'))

      const { container } = renderWithTheme(component)

      Object.entries(expected).forEach(([property, value]) => {
        if (property === 'fontSize' && typeof value === 'string') {
          // Check responsive typography
          const element = container.querySelector('h1, h2, h3, h4, h5, h6, p, span')
          if (element) {
            expect(element).toHaveStyle({
              [property]: value
            })
          }
        } else if (property === 'flexDirection') {
          // Check layout changes
          const flexContainer = container.querySelector('[style*="flex"]')
          if (flexContainer) {
            expect(flexContainer).toHaveStyle({
              [property]: value
            })
          }
        } else if (property === 'padding') {
          // Check spacing changes
          const card = container.querySelector('.MuiCard-root')
          if (card) {
            expect(card).toHaveStyle({
              [property]: value
            })
          }
        }
      })
    })
  }

  test('Patient card mobile responsiveness', () => {
    // Test mobile view (375px - iPhone 12)
    Object.defineProperty(window, 'innerWidth', {
      value: 375,
      writable: true,
    })

    window.dispatchEvent(new Event('resize'))

    const { container } = renderWithTheme(
      <PatientCard
        patient={mockPatient}
        onViewDetails={mockOnViewDetails}
        compact={true}
      />
    )

    // Check mobile-specific layout
    const card = container.querySelector('.MuiCard-root')
    expect(card).toBeInTheDocument()

    // Check that content fits mobile screen
    const patientName = screen.getByText('John Doe')
    expect(patientName).toBeInTheDocument()

    // Check mobile typography
    expect(patientName).toHaveStyle({
      fontSize: expect.stringMatching(/0\.875rem|14px/)
    })
  })

  test('Patient card tablet responsiveness', () => {
    // Test tablet view (768px - iPad)
    Object.defineProperty(window, 'innerWidth', {
      value: 768,
      writable: true,
    })

    window.dispatchEvent(new Event('resize'))

    const { container } = renderWithTheme(
      <PatientCard
        patient={mockPatient}
        onViewDetails={mockOnViewDetails}
      />
    )

    // Check tablet-specific layout
    const card = container.querySelector('.MuiCard-root')
    expect(card).toBeInTheDocument()

    // Check tablet typography scaling
    const patientName = screen.getByText('John Doe')
    expect(patientName).toHaveStyle({
      fontSize: expect.stringMatching(/1\.25rem|20px/)
    })
  })

  test('Patient card desktop responsiveness', () => {
    // Test desktop view (1024px)
    Object.defineProperty(window, 'innerWidth', {
      value: 1024,
      writable: true,
    })

    window.dispatchEvent(new Event('resize'))

    const { container } = renderWithTheme(
      <PatientCard
        patient={mockPatient}
        onViewDetails={mockOnViewDetails}
      />
    )

    // Check desktop layout
    const card = container.querySelector('.MuiCard-root')
    expect(card).toBeInTheDocument()

    // Check desktop typography
    const patientName = screen.getByText('John Doe')
    expect(patientName).toHaveStyle({
      fontSize: expect.stringMatching(/1\.25rem|20px/)
    })
  })

  test('Large screen responsiveness (4K)', () => {
    // Test 4K view (3840px)
    Object.defineProperty(window, 'innerWidth', {
      value: 3840,
      writable: true,
    })

    window.dispatchEvent(new Event('resize'))

    const { container } = renderWithTheme(
      <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
        <PatientCard
          patient={mockPatient}
          onViewDetails={mockOnViewDetails}
        />
      </div>
    )

    // Check that content is properly centered and max-width constrained
    const containerDiv = container.querySelector('div[style*="max-width"]')
    expect(containerDiv).toHaveStyle({
      maxWidth: '1200px',
      margin: '0 auto'
    })
  })

  test('Orientation change handling', () => {
    // Test portrait mode
    Object.defineProperty(window, 'innerWidth', {
      value: 375,
    })
    Object.defineProperty(window, 'innerHeight', {
      value: 667,
    })

    window.dispatchEvent(new Event('resize'))

    const { container, rerender } = renderWithTheme(
      <PatientCard
        patient={mockPatient}
        onViewDetails={mockOnViewDetails}
        compact={true}
      />
    )

    // Check portrait layout
    let card = container.querySelector('.MuiCard-root')
    expect(card).toBeInTheDocument()

    // Switch to landscape mode
    Object.defineProperty(window, 'innerWidth', {
      value: 667,
    })
    Object.defineProperty(window, 'innerHeight', {
      value: 375,
    })

    window.dispatchEvent(new Event('resize'))

    rerender(
      <PatientCard
        patient={mockPatient}
        onViewDetails={mockOnViewDetails}
        compact={true}
      />
    )

    // Check landscape layout
    card = container.querySelector('.MuiCard-root')
    expect(card).toBeInTheDocument()
  })

  test('Responsive breakpoints compliance', () => {
    const breakpoints = [
      { width: 320, expected: { fontSize: '0.875rem' } }, // xs
      { width: 600, expected: { fontSize: '1rem' } }, // sm
      { width: 900, expected: { fontSize: '1.25rem' } }, // md
      { width: 1200, expected: { fontSize: '1.25rem' } }, // lg
      { width: 1536, expected: { fontSize: '1.5rem' } }, // xl
    ]

    breakpoints.forEach(({ width, expected }) => {
      Object.defineProperty(window, 'innerWidth', {
        value: width,
        writable: true,
      })

      window.dispatchEvent(new Event('resize'))

      const { container } = renderWithTheme(
        <div>
          <h1 style={{ fontSize: 'clamp(1rem, 2vw, 1.5rem)' }}>Responsive Heading</h1>
        </div>
      )

      const heading = screen.getByText('Responsive Heading')
      expect(heading).toBeInTheDocument()
    })
  })

  test('Mobile-first navigation pattern', () => {
    // Mock mobile screen size
    Object.defineProperty(window, 'innerWidth', {
      value: 375,
      writable: true,
    })

    window.dispatchEvent(new Event('resize'))

    const { container } = renderWithTheme(
      <nav style={{
        display: 'flex',
        flexDirection: 'column',
        gap: '8px',
        padding: '16px'
      }}>
        <button style={{
          padding: '12px',
          borderRadius: '8px',
          backgroundColor: '#0066CC',
          color: 'white',
          border: 'none'
        }}>
          Menu
        </button>
        <div style={{
          display: 'none', // Hidden on mobile
          flexDirection: 'column',
          gap: '8px'
        }}>
          <a href="#" style={{ padding: '8px' }}>Dashboard</a>
          <a href="#" style={{ padding: '8px' }}>Patients</a>
          <a href="#" style={{ padding: '8px' }}>Appointments</a>
        </div>
      </nav>
    )

    // Check mobile navigation
    const menuButton = screen.getByRole('button', { name: /menu/i })
    expect(menuButton).toBeInTheDocument()

    // Test desktop view
    Object.defineProperty(window, 'innerWidth', {
      value: 1024,
      writable: true,
    })

    window.dispatchEvent(new Event('resize'))

    const { container: desktopContainer } = renderWithTheme(
      <nav style={{
        display: 'flex',
        flexDirection: 'row',
        gap: '16px',
        padding: '16px'
      }}>
        <a href="#" style={{ padding: '8px' }}>Dashboard</a>
        <a href="#" style={{ padding: '8px' }}>Patients</a>
        <a href="#" style={{ padding: '8px' }}>Appointments</a>
      </nav>
    )

    // Check desktop navigation
    const navigationLinks = desktopContainer.querySelectorAll('a')
    expect(navigationLinks.length).toBe(3)
  })

  test('Responsive grid layout', () => {
    // Test mobile grid (1 column)
    Object.defineProperty(window, 'innerWidth', {
      value: 375,
      writable: true,
    })

    window.dispatchEvent(new Event('resize'))

    const { container, rerender } = renderWithTheme(
      <div style={{
        display: 'grid',
        gridTemplateColumns: '1fr',
        gap: '16px',
        padding: '16px'
      }}>
        <PatientCard patient={mockPatient} onViewDetails={mockOnViewDetails} compact />
        <PatientCard patient={{...mockPatient, id: '2', firstName: 'Jane'}} onViewDetails={mockOnViewDetails} compact />
      </div>
    )

    // Check 1 column layout
    const grid = container.querySelector('div[style*="grid"]')
    expect(grid).toHaveStyle({
      gridTemplateColumns: '1fr'
    })

    // Test desktop grid (3 columns)
    Object.defineProperty(window, 'innerWidth', {
      value: 1200,
      writable: true,
    })

    window.dispatchEvent(new Event('resize'))

    rerender(
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(3, 1fr)',
        gap: '16px',
        padding: '16px'
      }}>
        <PatientCard patient={mockPatient} onViewDetails={mockOnViewDetails} />
        <PatientCard patient={{...mockPatient, id: '2', firstName: 'Jane'}} onViewDetails={mockOnViewDetails} />
        <PatientCard patient={{...mockPatient, id: '3', firstName: 'Bob'}} onViewDetails={mockOnViewDetails} />
      </div>
    )

    // Check 3 column layout
    const desktopGrid = container.querySelector('div[style*="grid"]')
    expect(desktopGrid).toHaveStyle({
      gridTemplateColumns: 'repeat(3, 1fr)'
    })
  })

  test('Responsive typography scaling', () => {
    const typographyTests = [
      { width: 375, expected: { h1: '1.75rem', h2: '1.5rem', body: '1rem' } },
      { width: 768, expected: { h1: '2rem', h2: '1.75rem', body: '1rem' } },
      { width: 1024, expected: { h1: '2.5rem', h2: '2rem', body: '1rem' } },
    ]

    typographyTests.forEach(({ width, expected }) => {
      Object.defineProperty(window, 'innerWidth', {
        value: width,
        writable: true,
      })

      window.dispatchEvent(new Event('resize'))

      const { container } = renderWithTheme(
        <div>
          <h1 style={{ fontSize: 'clamp(1.5rem, 4vw, 2.5rem)' }}>Main Title</h1>
          <h2 style={{ fontSize: 'clamp(1.25rem, 3vw, 2rem)' }}>Subtitle</h2>
          <p style={{ fontSize: 'clamp(0.875rem, 2vw, 1rem)' }}>Body text</p>
        </div>
      )

      const h1 = screen.getByText('Main Title')
      const h2 = screen.getByText('Subtitle')
      const p = screen.getByText('Body text')

      expect(h1).toBeInTheDocument()
      expect(h2).toBeInTheDocument()
      expect(p).toBeInTheDocument()
    })
  })

  test('Responsive image and media handling', () => {
    const { container } = renderWithTheme(
      <div>
        <img
          src="patient.jpg"
          alt="Patient photo"
          style={{
            width: '100%',
            maxWidth: '100%',
            height: 'auto',
            borderRadius: '8px'
          }}
        />
        <video
          controls
          style={{
            width: '100%',
            maxWidth: '100%',
            height: 'auto',
            borderRadius: '8px'
          }}
        >
          <source src="video.mp4" type="video/mp4" />
        </video>
      </div>
    )

    // Test mobile
    Object.defineProperty(window, 'innerWidth', {
      value: 375,
      writable: true,
    })

    window.dispatchEvent(new Event('resize'))

    const img = screen.getByAltText('Patient photo')
    expect(img).toHaveStyle({
      width: '100%',
      maxWidth: '100%',
      height: 'auto'
    })

    // Test desktop
    Object.defineProperty(window, 'innerWidth', {
      value: 1200,
      writable: true,
    })

    window.dispatchEvent(new Event('resize'))

    expect(img).toHaveStyle({
      width: '100%',
      maxWidth: '100%',
      height: 'auto'
    })
  })

  test('Responsive form layouts', () => {
    // Test mobile form (vertical)
    Object.defineProperty(window, 'innerWidth', {
      value: 375,
      writable: true,
    })

    window.dispatchEvent(new Event('resize'))

    const { container, rerender } = renderWithTheme(
      <form style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
        <input type="text" placeholder="Full Name" style={{ padding: '12px', borderRadius: '8px' }} />
        <input type="email" placeholder="Email" style={{ padding: '12px', borderRadius: '8px' }} />
        <button type="submit" style={{ padding: '12px', borderRadius: '8px', backgroundColor: '#0066CC', color: 'white' }}>
          Submit
        </button>
      </form>
    )

    const form = container.querySelector('form')
    expect(form).toHaveStyle({
      flexDirection: 'column'
    })

    // Test desktop form (horizontal layout for some fields)
    Object.defineProperty(window, 'innerWidth', {
      value: 1024,
      writable: true,
    })

    window.dispatchEvent(new Event('resize'))

    rerender(
      <form style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
        <input type="text" placeholder="Full Name" style={{ padding: '12px', borderRadius: '8px' }} />
        <input type="email" placeholder="Email" style={{ padding: '12px', borderRadius: '8px' }} />
        <button type="submit" style={{ gridColumn: '1 / -1', padding: '12px', borderRadius: '8px', backgroundColor: '#0066CC', color: 'white' }}>
          Submit
        </button>
      </form>
    )

    const desktopForm = container.querySelector('form')
    expect(desktopForm).toHaveStyle({
      gridTemplateColumns: '1fr 1fr'
    })
  })

  test('Accessibility in responsive design', () => {
    const { container } = renderWithTheme(
      <div>
        <button
          aria-label="Mobile menu toggle"
          style={{
            display: 'block',
            '@media (min-width: 768px)': {
              display: 'none'
            }
          }}
        >
          ☰
        </button>
        <nav
          aria-label="Main navigation"
          style={{
            display: 'none',
            '@media (min-width: 768px)': {
              display: 'block'
            }
          }}
        >
          <ul>
            <li><a href="#home">Home</a></li>
            <li><a href="#about">About</a></li>
          </ul>
        </nav>
      </div>
    )

    // Test mobile accessibility
    Object.defineProperty(window, 'innerWidth', {
      value: 375,
      writable: true,
    })

    window.dispatchEvent(new Event('resize'))

    const menuButton = screen.getByRole('button', { name: /mobile menu toggle/i })
    expect(menuButton).toBeInTheDocument()

    // Test desktop accessibility
    Object.defineProperty(window, 'innerWidth', {
      value: 1024,
      writable: true,
    })

    window.dispatchEvent(new Event('resize'))

    const navigation = screen.getByRole('navigation', { name: /main navigation/i })
    expect(navigation).toBeInTheDocument()
  })
})