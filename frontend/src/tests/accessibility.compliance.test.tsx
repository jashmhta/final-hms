import { render, screen, fireEvent } from '@testing-library/react'
import { axe, toHaveNoViolations } from 'jest-axe'
import { ThemeProvider, createTheme } from '@mui/material/styles'
import healthcareTheme from '../theme/healthcareTheme'
import PatientCard from '../components/healthcare/PatientCard'

// Extend Jest matchers
expect.extend(toHaveNoViolations)

describe('Accessibility Tests - WCAG 2.1 AA Compliance', () => {
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

  test('No accessibility violations in PatientCard component', async () => {
    const { container } = renderWithTheme(
      <PatientCard
        patient={mockPatient}
        onViewDetails={mockOnViewDetails}
      />
    )

    const results = await axe(container)
    expect(results).toHaveNoViolations()
  })

  test('Keyboard navigation support', () => {
    const { container } = renderWithTheme(
      <form aria-label="Patient registration">
        <label htmlFor="fullName">Full Name</label>
        <input
          id="fullName"
          type="text"
          placeholder="Full Name"
          aria-required="true"
          aria-describedby="fullName-error"
        />
        <div id="fullName-error" role="alert" style={{ display: 'none' }}></div>

        <label htmlFor="email">Email Address</label>
        <input
          id="email"
          type="email"
          placeholder="Email Address"
          aria-required="true"
          aria-describedby="email-error"
        />
        <div id="email-error" role="alert" style={{ display: 'none' }}></div>

        <button type="submit">Register Patient</button>
      </form>
    )

    // Test Tab navigation
    const fullNameInput = screen.getByLabelText('Full Name')
    const emailInput = screen.getByLabelText('Email Address')
    const submitButton = screen.getByRole('button', { name: /register patient/i })

    // Simulate Tab navigation
    fireEvent.keyDown(document.activeElement, { key: 'Tab' })
    expect(document.activeElement).toBe(fullNameInput)

    fireEvent.keyDown(fullNameInput, { key: 'Tab' })
    expect(document.activeElement).toBe(emailInput)

    fireEvent.keyDown(emailInput, { key: 'Tab' })
    expect(document.activeElement).toBe(submitButton)

    // Test Shift+Tab navigation
    fireEvent.keyDown(submitButton, { key: 'Tab', shiftKey: true })
    expect(document.activeElement).toBe(emailInput)

    fireEvent.keyDown(emailInput, { key: 'Tab', shiftKey: true })
    expect(document.activeElement).toBe(fullNameInput)
  })

  test('Screen reader compatibility', () => {
    const { container } = renderWithTheme(
      <div>
        <button aria-label="Close dialog" aria-expanded="false">
          X
        </button>
        <img
          src="patient.jpg"
          alt="Patient portrait for John Doe"
          width="100"
          height="100"
        />
        <progress value={75} max={100} aria-label="Loading progress: 75% complete">
          75% complete
        </progress>
        <div role="status" aria-live="polite">
          Patient data loaded successfully
        </div>
        <div role="alert" aria-live="assertive">
          Emergency alert: Patient condition critical
        </div>
      </div>
    )

    // Check ARIA labels
    expect(screen.getByLabelText('Close dialog')).toBeInTheDocument()
    expect(screen.getByAltText('Patient portrait for John Doe')).toBeInTheDocument()

    // Check accessible form controls
    const progress = screen.getByText(/75% complete/)
    expect(progress).toBeInTheDocument()

    // Check live regions
    expect(screen.getByRole('status')).toBeInTheDocument()
    expect(screen.getByRole('alert')).toBeInTheDocument()
  })

  test('Color contrast compliance', () => {
    const { container } = renderWithTheme(
      <div>
        <h1 style={{ color: '#0F172A', backgroundColor: '#FFFFFF' }}>
          Patient Information
        </h1>
        <p style={{ color: '#475569', backgroundColor: '#FFFFFF' }}>
          Supporting details about the patient
        </p>
        <button style={{
          backgroundColor: '#0066CC',
          color: '#FFFFFF',
          padding: '12px 24px',
          border: 'none',
          borderRadius: '8px'
        }}>
          Primary Action
        </button>
        <button style={{
          backgroundColor: '#F3F4F6',
          color: '#0066CC',
          padding: '12px 24px',
          border: '1px solid #0066CC',
          borderRadius: '8px'
        }}>
          Secondary Action
        </button>
      </div>
    )

    const title = screen.getByText('Patient Information')
    const computedTitleStyle = window.getComputedStyle(title)
    const titleBgColor = computedTitleStyle.backgroundColor
    const titleColor = computedTitleStyle.color

    // Convert RGB to hex for contrast calculation
    const rgbToHex = (rgb) => {
      const result = rgb.match(/\d+/g)
      if (!result) return '#000000'
      return '#' + result.slice(0, 3).map(x => {
        const hex = parseInt(x).toString(16)
        return hex.length === 1 ? '0' + hex : hex
      }).join('')
    }

    const calculateContrastRatio = (color1, color2) => {
      const getLuminance = (color) => {
        const rgb = color.match(/\w\w/g).map(x => parseInt(x, 16) / 255)
        const [r, g, b] = rgb.map(c => c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4))
        return 0.2126 * r + 0.7152 * g + 0.0722 * b
      }

      const l1 = getLuminance(color1)
      const l2 = getLuminance(color2)
      const lighter = Math.max(l1, l2)
      const darker = Math.min(l1, l2)
      return (lighter + 0.05) / (darker + 0.05)
    }

    const titleBgHex = rgbToHex(titleBgColor)
    const titleColorHex = rgbToHex(titleColor)
    const titleContrast = calculateContrastRatio(titleBgHex, titleColorHex)

    expect(titleContrast).toBeGreaterThanOrEqual(4.5) // WCAG AA standard
  })

  test('Focus management and indicators', () => {
    const { container } = renderWithTheme(
      <div>
        <button
          className="focus-button"
          style={{
            padding: '12px 24px',
            borderRadius: '8px',
            border: '2px solid transparent',
            backgroundColor: '#0066CC',
            color: 'white',
            outline: 'none'
          }}
        >
          Focus Test Button
        </button>
        <a
          href="#"
          className="focus-link"
          style={{
            color: '#0066CC',
            textDecoration: 'none',
            padding: '8px 16px',
            borderRadius: '4px',
            outline: 'none'
          }}
        >
          Focus Test Link
        </a>
      </div>
    )

    const button = screen.getByRole('button', { name: /focus test button/i })
    const link = screen.getByRole('link', { name: /focus test link/i })

    // Test focus states
    fireEvent.focus(button)
    expect(button).toHaveStyle({
      outline: '2px solid #0066CC',
      outlineOffset: '2px'
    })

    fireEvent.focus(link)
    expect(link).toHaveStyle({
      outline: '2px solid #0066CC',
      outlineOffset: '2px'
    })

    // Test focus trap in modal
    const { container: modalContainer } = renderWithTheme(
      <div role="dialog" aria-modal="true" aria-labelledby="modal-title">
        <h2 id="modal-title">Patient Details</h2>
        <button>Close</button>
        <button>Save</button>
      </div>
    )

    // Test keyboard navigation within modal
    const modalButtons = modalContainer.querySelectorAll('button')
    modalButtons.forEach(button => {
      fireEvent.focus(button)
      expect(modalContainer.contains(document.activeElement)).toBe(true)
    })
  })

  test('ARIA landmarks and roles', () => {
    const { container } = renderWithTheme(
      <div>
        <header role="banner">
          <h1>Hospital Management System</h1>
        </header>

        <nav role="navigation" aria-label="Main navigation">
          <ul>
            <li><a href="#dashboard">Dashboard</a></li>
            <li><a href="#patients">Patients</a></li>
            <li><a href="#appointments">Appointments</a></li>
          </ul>
        </nav>

        <main role="main">
          <section aria-labelledby="patients-heading">
            <h2 id="patients-heading">Patient List</h2>
            <PatientCard
              patient={mockPatient}
              onViewDetails={mockOnViewDetails}
            />
          </section>
        </main>

        <aside role="complementary" aria-labelledby="sidebar-heading">
          <h3 id="sidebar-heading">Quick Actions</h3>
          <button>Add New Patient</button>
        </aside>

        <footer role="contentinfo">
          <p>&copy; 2024 Hospital Management System</p>
        </footer>
      </div>
    )

    // Check ARIA landmarks
    expect(screen.getByRole('banner')).toBeInTheDocument()
    expect(screen.getByRole('navigation', { name: /main navigation/i })).toBeInTheDocument()
    expect(screen.getByRole('main')).toBeInTheDocument()
    expect(screen.getByRole('complementary')).toBeInTheDocument()
    expect(screen.getByRole('contentinfo')).toBeInTheDocument()
  })

  test('Form accessibility validation', () => {
    const { container } = renderWithTheme(
      <form aria-label="Patient registration form" noValidate>
        <fieldset>
          <legend>Personal Information</legend>

          <div>
            <label htmlFor="firstName" id="firstName-label">
              First Name <span aria-hidden="true">*</span>
            </label>
            <input
              id="firstName"
              name="firstName"
              type="text"
              aria-required="true"
              aria-labelledby="firstName-label"
              aria-invalid="false"
              aria-describedby="firstName-error"
            />
            <div id="firstName-error" role="alert" style={{ display: 'none' }}></div>
          </div>

          <div>
            <label htmlFor="lastName" id="lastName-label">
              Last Name <span aria-hidden="true">*</span>
            </label>
            <input
              id="lastName"
              name="lastName"
              type="text"
              aria-required="true"
              aria-labelledby="lastName-label"
              aria-invalid="false"
              aria-describedby="lastName-error"
            />
            <div id="lastName-error" role="alert" style={{ display: 'none' }}></div>
          </div>

          <div>
            <label htmlFor="dateOfBirth" id="dob-label">
              Date of Birth <span aria-hidden="true">*</span>
            </label>
            <input
              id="dateOfBirth"
              name="dateOfBirth"
              type="date"
              aria-required="true"
              aria-labelledby="dob-label"
              aria-invalid="false"
              aria-describedby="dob-error"
            />
            <div id="dob-error" role="alert" style={{ display: 'none' }}></div>
          </div>
        </fieldset>

        <div>
          <button type="submit">Register Patient</button>
          <button type="button">Cancel</button>
        </div>
      </form>
    )

    // Check form accessibility
    expect(screen.getByLabelText('First Name')).toBeInTheDocument()
    expect(screen.getByLabelText('Last Name')).toBeInTheDocument()
    expect(screen.getByLabelText('Date of Birth')).toBeInTheDocument()

    const firstNameInput = screen.getByLabelText('First Name')
    expect(firstNameInput).toHaveAttribute('aria-required', 'true')
    expect(firstNameInput).toHaveAttribute('aria-invalid', 'false')

    // Test form validation accessibility
    fireEvent.change(firstNameInput, { target: { value: '' } })
    fireEvent.blur(firstNameInput)

    const errorDiv = container.querySelector('#firstName-error')
    expect(errorDiv).toBeInTheDocument()
    expect(errorDiv).toHaveAttribute('role', 'alert')
  })

  test('Table accessibility', () => {
    const { container } = renderWithTheme(
      <table role="table" aria-label="Patient appointments">
        <caption>Scheduled Patient Appointments</caption>
        <thead>
          <tr>
            <th scope="col">Patient Name</th>
            <th scope="col">Date</th>
            <th scope="col">Time</th>
            <th scope="col">Status</th>
            <th scope="col">Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <th scope="row">John Doe</th>
            <td>2024-01-15</td>
            <td>10:00 AM</td>
            <td>
              <span role="status" aria-label="Confirmed">
                Confirmed
              </span>
            </td>
            <td>
              <button aria-label="Edit appointment for John Doe">Edit</button>
              <button aria-label="Cancel appointment for John Doe">Cancel</button>
            </td>
          </tr>
        </tbody>
      </table>
    )

    // Check table accessibility
    expect(screen.getByRole('table')).toBeInTheDocument()
    expect(screen.getByRole('columnheader', { name: /patient name/i })).toBeInTheDocument()
    expect(screen.getByRole('rowheader', { name: /john doe/i })).toBeInTheDocument()
  })

  test('Interactive element accessibility', () => {
    const { container } = renderWithTheme(
      <div>
        <button
          aria-pressed="false"
          aria-label="Favorite patient"
          onClick={() => {}}
        >
          ♡
        </button>

        <div role="tablist" aria-label="Patient information tabs">
          <button
            role="tab"
            aria-selected="true"
            aria-controls="personal-info-panel"
            id="personal-info-tab"
          >
            Personal Info
          </button>
          <button
            role="tab"
            aria-selected="false"
            aria-controls="medical-info-panel"
            id="medical-info-tab"
          >
            Medical Info
          </button>
        </div>

        <div
          role="tabpanel"
          id="personal-info-panel"
          aria-labelledby="personal-info-tab"
        >
          <PatientCard
            patient={mockPatient}
            onViewDetails={mockOnViewDetails}
          />
        </div>

        <div
          role="tabpanel"
          id="medical-info-panel"
          aria-labelledby="medical-info-tab"
          hidden
        >
          Medical information content
        </div>
      </div>
    )

    // Check button states
    const favoriteButton = screen.getByRole('button', { name: /favorite patient/i })
    expect(favoriteButton).toHaveAttribute('aria-pressed', 'false')

    // Check tab accessibility
    const personalTab = screen.getByRole('tab', { name: /personal info/i })
    const medicalTab = screen.getByRole('tab', { name: /medical info/i })

    expect(personalTab).toHaveAttribute('aria-selected', 'true')
    expect(medicalTab).toHaveAttribute('aria-selected', 'false')

    // Check tab panel accessibility
    const personalPanel = screen.getByRole('tabpanel', { name: /personal info/i })
    const medicalPanel = container.querySelector('#medical-info-panel')

    expect(personalPanel).toBeInTheDocument()
    expect(personalPanel).toHaveAttribute('aria-labelledby', 'personal-info-tab')
    expect(medicalPanel).toHaveAttribute('hidden')
  })

  test('Skip links and navigation accessibility', () => {
    const { container } = renderWithTheme(
      <div>
        <a href="#main-content" className="skip-link">
          Skip to main content
        </a>

        <nav aria-label="Main navigation">
          <ul>
            <li><a href="#home">Home</a></li>
            <li><a href="#patients">Patients</a></li>
            <li><a href="#appointments">Appointments</a></li>
          </ul>
        </nav>

        <main id="main-content" tabIndex={-1}>
          <h1>Patient Dashboard</h1>
          <PatientCard
            patient={mockPatient}
            onViewDetails={mockOnViewDetails}
          />
        </main>
      </div>
    )

    // Check skip link
    const skipLink = screen.getByText('Skip to main content')
    expect(skipLink).toBeInTheDocument()
    expect(skipLink).toHaveAttribute('href', '#main-content')

    // Check main content area
    const mainContent = screen.getByRole('main')
    expect(mainContent).toHaveAttribute('id', 'main-content')
    expect(mainContent).toHaveAttribute('tabIndex', '-1')
  })

  test('Error handling accessibility', () => {
    const { container } = renderWithTheme(
      <div role="alert" aria-live="assertive">
        <h2>Error: Unable to load patient data</h2>
        <p>Please try again later or contact support.</p>
        <button aria-label="Dismiss error message">Dismiss</button>
      </div>
    )

    // Check error accessibility
    const errorAlert = screen.getByRole('alert')
    expect(errorAlert).toBeInTheDocument()
    expect(errorAlert).toHaveAttribute('aria-live', 'assertive')

    // Check error message is announced
    expect(screen.getByText(/unable to load patient data/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /dismiss error message/i })).toBeInTheDocument()
  })

  test('Responsive accessibility', () => {
    // Test mobile accessibility
    Object.defineProperty(window, 'innerWidth', {
      value: 375,
      writable: true,
    })

    window.dispatchEvent(new Event('resize'))

    const { container, rerender } = renderWithTheme(
      <div>
        <button
          aria-label="Mobile menu toggle"
          aria-expanded="false"
          aria-controls="mobile-menu"
        >
          ☰
        </button>
        <nav
          id="mobile-menu"
          aria-label="Mobile navigation"
          style={{ display: 'none' }}
        >
          <ul>
            <li><a href="#home">Home</a></li>
            <li><a href="#patients">Patients</a></li>
          </ul>
        </nav>
      </div>
    )

    // Check mobile menu accessibility
    const menuButton = screen.getByRole('button', { name: /mobile menu toggle/i })
    expect(menuButton).toHaveAttribute('aria-expanded', 'false')
    expect(menuButton).toHaveAttribute('aria-controls', 'mobile-menu')

    // Test desktop accessibility
    Object.defineProperty(window, 'innerWidth', {
      value: 1024,
      writable: true,
    })

    window.dispatchEvent(new Event('resize'))

    rerender(
      <nav aria-label="Desktop navigation">
        <ul>
          <li><a href="#home">Home</a></li>
          <li><a href="#patients">Patients</a></li>
        </ul>
      </nav>
    )

    // Check desktop navigation accessibility
    const desktopNav = screen.getByRole('navigation', { name: /desktop navigation/i })
    expect(desktopNav).toBeInTheDocument()
  })

  test('Dynamic content accessibility', () => {
    const { container } = renderWithTheme(
      <div>
        <div role="status" aria-live="polite" aria-atomic="true">
          Loading patient data...
        </div>
        <div role="status" aria-live="assertive" aria-atomic="true">
          Emergency: Critical patient admitted
        </div>
        <div aria-busy="true" aria-label="Processing patient registration">
          Registering patient...
        </div>
      </div>
    )

    // Check live regions
    const politeRegion = screen.getByText('Loading patient data...')
    expect(politeRegion).toHaveAttribute('aria-live', 'polite')
    expect(politeRegion).toHaveAttribute('aria-atomic', 'true')

    const assertiveRegion = screen.getByText(/emergency: critical patient admitted/i)
    expect(assertiveRegion).toHaveAttribute('aria-live', 'assertive')
    expect(assertiveRegion).toHaveAttribute('aria-atomic', 'true')

    // Check busy state
    const busyDiv = screen.getByText('Registering patient...')
    expect(busyDiv).toHaveAttribute('aria-busy', 'true')
    expect(busyDiv).toHaveAttribute('aria-label', 'Processing patient registration')
  })
})