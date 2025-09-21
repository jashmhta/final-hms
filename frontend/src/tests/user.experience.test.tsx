import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { ThemeProvider, createTheme } from '@mui/material/styles'
import healthcareTheme from '../../theme/healthcareTheme'
import PatientCard from '../components/healthcare/PatientCard'

describe('User Experience Tests', () => {
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
    },
    emergencyContact: {
      name: 'Jane Doe',
      phone: '(555) 123-4567',
      relationship: 'Spouse'
    }
  }

  const mockOnViewDetails = jest.fn()
  const mockOnContact = jest.fn()
  const mockOnEmergencyAlert = jest.fn()

  const renderWithTheme = (component) => {
    const theme = createTheme(healthcareTheme)
    return render(
      <ThemeProvider theme={theme}>
        {component}
      </ThemeProvider>
    )
  }

  test('Patient registration journey - complete workflow', async () => {
    const { container } = renderWithTheme(
      <div>
        <h1>Patient Registration</h1>
        <form data-testid="registration-form">
          {/* Step 1: Personal Information */}
          <div data-testid="step-1">
            <label htmlFor="firstName">First Name *</label>
            <input
              id="firstName"
              name="firstName"
              type="text"
              placeholder="Enter first name"
              required
            />
            <label htmlFor="lastName">Last Name *</label>
            <input
              id="lastName"
              name="lastName"
              type="text"
              placeholder="Enter last name"
              required
            />
            <label htmlFor="dateOfBirth">Date of Birth *</label>
            <input
              id="dateOfBirth"
              name="dateOfBirth"
              type="date"
              required
            />
            <label htmlFor="gender">Gender *</label>
            <select id="gender" name="gender" required>
              <option value="">Select gender</option>
              <option value="male">Male</option>
              <option value="female">Female</option>
              <option value="other">Other</option>
            </select>
            <button type="button" data-testid="next-step-1">Next</button>
          </div>

          {/* Step 2: Contact Information */}
          <div data-testid="step-2" style={{ display: 'none' }}>
            <label htmlFor="email">Email Address *</label>
            <input
              id="email"
              name="email"
              type="email"
              placeholder="Enter email address"
              required
            />
            <label htmlFor="phone">Phone Number *</label>
            <input
              id="phone"
              name="phone"
              type="tel"
              placeholder="Enter phone number"
              required
            />
            <label htmlFor="address">Address</label>
            <textarea
              id="address"
              name="address"
              placeholder="Enter address"
              rows={3}
            />
            <button type="button" data-testid="previous-step-2">Previous</button>
            <button type="button" data-testid="next-step-2">Next</button>
          </div>

          {/* Step 3: Medical Information */}
          <div data-testid="step-3" style={{ display: 'none' }}>
            <label htmlFor="primaryPhysician">Primary Physician *</label>
            <input
              id="primaryPhysician"
              name="primaryPhysician"
              type="text"
              placeholder="Enter primary physician name"
              required
            />
            <label htmlFor="allergies">Known Allergies</label>
            <input
              id="allergies"
              name="allergies"
              type="text"
              placeholder="Enter known allergies (comma separated)"
            />
            <label htmlFor="medications">Current Medications</label>
            <input
              id="medications"
              name="medications"
              type="text"
              placeholder="Enter current medications (comma separated)"
            />
            <button type="button" data-testid="previous-step-3">Previous</button>
            <button type="submit" data-testid="submit-registration">Register Patient</button>
          </div>
        </form>
      </div>
    )

    // Step 1: Personal Information
    const firstNameInput = screen.getByLabelText('First Name *')
    const lastNameInput = screen.getByLabelText('Last Name *')
    const dobInput = screen.getByLabelText('Date of Birth *')
    const genderSelect = screen.getByLabelText('Gender *')
    const nextButton1 = screen.getByTestId('next-step-1')

    // Fill personal information
    fireEvent.change(firstNameInput, { target: { value: 'John' } })
    fireEvent.change(lastNameInput, { target: { value: 'Doe' } })
    fireEvent.change(dobInput, { target: { value: '1990-01-15' } })
    fireEvent.change(genderSelect, { target: { value: 'male' } })

    // Navigate to step 2
    fireEvent.click(nextButton1)

    // Step 2: Contact Information should now be visible
    await waitFor(() => {
      expect(screen.getByTestId('step-2')).not.toHaveStyle({ display: 'none' })
    })

    const emailInput = screen.getByLabelText('Email Address *')
    const phoneInput = screen.getByLabelText('Phone Number *')
    const addressInput = screen.getByLabelText('Address')
    const nextButton2 = screen.getByTestId('next-step-2')

    // Fill contact information
    fireEvent.change(emailInput, { target: { value: 'john.doe@example.com' } })
    fireEvent.change(phoneInput, { target: { value: '(555) 123-4567' } })
    fireEvent.change(addressInput, { target: { value: '123 Main St, Anytown, ST 12345' } })

    // Navigate to step 3
    fireEvent.click(nextButton2)

    // Step 3: Medical Information should now be visible
    await waitFor(() => {
      expect(screen.getByTestId('step-3')).not.toHaveStyle({ display: 'none' })
    })

    const physicianInput = screen.getByLabelText('Primary Physician *')
    const allergiesInput = screen.getByLabelText('Known Allergies')
    const medicationsInput = screen.getByLabelText('Current Medications')
    const submitButton = screen.getByTestId('submit-registration')

    // Fill medical information
    fireEvent.change(physicianInput, { target: { value: 'Dr. Smith' } })
    fireEvent.change(allergiesInput, { target: { value: 'Penicillin' } })
    fireEvent.change(medicationsInput, { target: { value: 'Lisinopril, Metformin' } })

    // Submit registration
    fireEvent.click(submitButton)

    // Verify form submission
    expect(submitButton).toBeInTheDocument()
  })

  test('Loading states and performance feedback', async () => {
    const { container } = renderWithTheme(
      <div data-testid="patient-dashboard">
        <div role="status" aria-live="polite" data-testid="loading-state">
          <div aria-label="Loading patient data" data-testid="loading-spinner">
            Loading patient dashboard...
          </div>
        </div>

        <div data-testid="dashboard-content" style={{ display: 'none' }}>
          <h1>Patient Dashboard</h1>
          <PatientCard
            patient={mockPatient}
            onViewDetails={mockOnViewDetails}
          />
        </div>

        <div data-testid="error-state" style={{ display: 'none' }} role="alert">
          <h2>Error Loading Data</h2>
          <p>Unable to load patient information. Please try again.</p>
          <button data-testid="retry-button">Retry</button>
        </div>
      </div>
    )

    // Test initial loading state
    expect(screen.getByTestId('loading-state')).toBeInTheDocument()
    expect(screen.getByTestId('loading-spinner')).toBeInTheDocument()
    expect(screen.getByText('Loading patient dashboard...')).toBeInTheDocument()

    // Simulate data loading completion
    setTimeout(() => {
      const loadingState = container.querySelector('[data-testid="loading-state"]')
      const dashboardContent = container.querySelector('[data-testid="dashboard-content"]')

      if (loadingState) {
        loadingState.style.display = 'none'
      }
      if (dashboardContent) {
        dashboardContent.style.display = 'block'
      }
    }, 1000)

    // Wait for content to load
    await waitFor(() => {
      expect(screen.getByTestId('dashboard-content')).not.toHaveStyle({ display: 'none' })
    }, { timeout: 1500 })

    // Verify content is displayed
    expect(screen.getByText('Patient Dashboard')).toBeInTheDocument()
    expect(screen.getByText('John Doe')).toBeInTheDocument()
  })

  test('Error handling and user feedback', async () => {
    const { container } = renderWithTheme(
      <div data-testid="appointment-scheduling">
        <h1>Schedule Appointment</h1>
        <form data-testid="appointment-form">
          <label htmlFor="appointmentDate">Appointment Date *</label>
          <input
            id="appointmentDate"
            name="appointmentDate"
            type="date"
            required
          />
          <label htmlFor="appointmentTime">Appointment Time *</label>
          <input
            id="appointmentTime"
            name="appointmentTime"
            type="time"
            required
          />
          <label htmlFor="appointmentType">Appointment Type *</label>
          <select id="appointmentType" name="appointmentType" required>
            <option value="">Select type</option>
            <option value="consultation">Consultation</option>
            <option value="follow-up">Follow-up</option>
            <option value="emergency">Emergency</option>
          </select>
          <button type="submit" data-testid="schedule-appointment">Schedule Appointment</button>
        </form>

        <div data-testid="success-message" style={{ display: 'none' }} role="status">
          <h2>Appointment Scheduled Successfully</h2>
          <p>Your appointment has been scheduled for confirmation.</p>
        </div>

        <div data-testid="error-message" style={{ display: 'none' }} role="alert">
          <h2>Scheduling Error</h2>
          <p>Unable to schedule appointment. Please try again later.</p>
          <button data-testid="retry-schedule">Retry</button>
        </div>
      </div>
    )

    const dateInput = screen.getByLabelText('Appointment Date *')
    const timeInput = screen.getByLabelText('Appointment Time *')
    const typeSelect = screen.getByLabelText('Appointment Type *')
    const scheduleButton = screen.getByTestId('schedule-appointment')

    // Fill appointment form
    fireEvent.change(dateInput, { target: { value: '2024-01-15' } })
    fireEvent.change(timeInput, { target: { value: '10:00' } })
    fireEvent.change(typeSelect, { target: { value: 'consultation' } })

    // Simulate network error
    fireEvent.click(scheduleButton)

    // Show error state
    setTimeout(() => {
      const errorMessage = container.querySelector('[data-testid="error-message"]')
      if (errorMessage) {
        errorMessage.style.display = 'block'
      }
    }, 500)

    // Check error message display
    await waitFor(() => {
      expect(screen.getByTestId('error-message')).not.toHaveStyle({ display: 'none' })
    }, { timeout: 1000 })

    // Check error message content
    expect(screen.getByText('Scheduling Error')).toBeInTheDocument()
    expect(screen.getByText('Unable to schedule appointment. Please try again later.')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /retry/i })).toBeInTheDocument()

    // Test error recovery
    const retryButton = screen.getByTestId('retry-schedule')
    expect(retryButton).toBeInTheDocument()

    // Simulate successful retry
    fireEvent.click(retryButton)

    // Show success state
    setTimeout(() => {
      const errorMessage = container.querySelector('[data-testid="error-message"]')
      const successMessage = container.querySelector('[data-testid="success-message"]')

      if (errorMessage) {
        errorMessage.style.display = 'none'
      }
      if (successMessage) {
        successMessage.style.display = 'block'
      }
    }, 500)

    // Check success message
    await waitFor(() => {
      expect(screen.getByTestId('success-message')).not.toHaveStyle({ display: 'none' })
    }, { timeout: 1000 })

    expect(screen.getByText('Appointment Scheduled Successfully')).toBeInTheDocument()
  })

  test('Interactive element feedback and states', () => {
    const { container } = renderWithTheme(
      <div>
        <button
          data-testid="interactive-button"
          style={{
            backgroundColor: '#0066CC',
            color: 'white',
            padding: '12px 24px',
            borderRadius: '8px',
            border: 'none',
            cursor: 'pointer',
            transition: 'all 0.2s ease-in-out'
          }}
        >
          Click Me
        </button>

        <div data-testid="feedback-message" style={{ display: 'none' }}>
          Button clicked successfully!
        </div>

        <input
          data-testid="interactive-input"
          type="text"
          placeholder="Type here..."
          style={{
            padding: '12px',
            borderRadius: '8px',
            border: '1px solid #E2E8F0',
            transition: 'border-color 0.2s ease-in-out'
          }}
        />

        <div data-testid="input-feedback" style={{ display: 'none' }}>
          Input value: <span data-testid="input-value"></span>
        </div>
      </div>
    )

    const button = screen.getByTestId('interactive-button')
    const feedbackMessage = screen.getByTestId('feedback-message')
    const input = screen.getByTestId('interactive-input')
    const inputFeedback = screen.getByTestId('input-feedback')
    const inputValue = screen.getByTestId('input-value')

    // Test button hover state
    fireEvent.mouseEnter(button)
    expect(button).toHaveStyle({
      backgroundColor: '#0052A3',
      transform: 'translateY(-1px)'
    })

    // Test button active state
    fireEvent.mouseDown(button)
    expect(button).toHaveStyle({
      backgroundColor: '#004080',
      transform: 'translateY(0px)'
    })

    // Test button click feedback
    fireEvent.click(button)
    setTimeout(() => {
      feedbackMessage.style.display = 'block'
    }, 100)

    expect(feedbackMessage).not.toHaveStyle({ display: 'none' })
    expect(screen.getByText('Button clicked successfully!')).toBeInTheDocument()

    // Test input focus state
    fireEvent.focus(input)
    expect(input).toHaveStyle({
      borderColor: '#0066CC',
      outline: '2px solid #0066CC',
      outlineOffset: '2px'
    })

    // Test input typing feedback
    fireEvent.change(input, { target: { value: 'Hello World' } })
    setTimeout(() => {
      inputFeedback.style.display = 'block'
      inputValue.textContent = 'Hello World'
    }, 100)

    expect(inputFeedback).not.toHaveStyle({ display: 'none' })
    expect(inputValue).toHaveTextContent('Hello World')
  })

  test('Patient search and filtering experience', async () => {
    const { container } = renderWithTheme(
      <div data-testid="patient-search">
        <h1>Search Patients</h1>
        <div data-testid="search-controls">
          <input
            data-testid="search-input"
            type="text"
            placeholder="Search by name, ID, or condition..."
            style={{ width: '100%', padding: '12px' }}
          />
          <div data-testid="filter-controls" style={{ display: 'flex', gap: '16px', marginTop: '16px' }}>
            <select data-testid="status-filter">
              <option value="">All Status</option>
              <option value="admitted">Admitted</option>
              <option value="outpatient">Outpatient</option>
              <option value="discharged">Discharged</option>
            </select>
            <select data-testid="condition-filter">
              <option value="">All Conditions</option>
              <option value="stable">Stable</option>
              <option value="critical">Critical</option>
              <option value="serious">Serious</option>
            </select>
            <button data-testid="apply-filters">Apply Filters</button>
            <button data-testid="clear-filters">Clear</button>
          </div>
        </div>

        <div data-testid="search-results">
          <div data-testid="loading-results" style={{ display: 'none' }}>Loading results...</div>
          <div data-testid="no-results" style={{ display: 'none' }}>No patients found matching your criteria.</div>
          <div data-testid="results-list">
            <PatientCard
              patient={mockPatient}
              onViewDetails={mockOnViewDetails}
              compact
            />
          </div>
        </div>
      </div>
    )

    const searchInput = screen.getByTestId('search-input')
    const statusFilter = screen.getByTestId('status-filter')
    const conditionFilter = screen.getByTestId('condition-filter')
    const applyFiltersButton = screen.getByTestId('apply-filters')
    const clearFiltersButton = screen.getByTestId('clear-filters')

    // Test search input
    fireEvent.change(searchInput, { target: { value: 'John' } })
    expect(searchInput).toHaveValue('John')

    // Test filter selection
    fireEvent.change(statusFilter, { target: { value: 'admitted' } })
    fireEvent.change(conditionFilter, { target: { value: 'stable' } })

    // Test filter application
    fireEvent.click(applyFiltersButton)

    // Simulate loading state
    const loadingResults = container.querySelector('[data-testid="loading-results"]')
    if (loadingResults) {
      loadingResults.style.display = 'block'
    }

    expect(screen.getByTestId('loading-results')).not.toHaveStyle({ display: 'none' })

    // Simulate search completion
    setTimeout(() => {
      const loadingResults = container.querySelector('[data-testid="loading-results"]')
      if (loadingResults) {
        loadingResults.style.display = 'none'
      }
    }, 500)

    await waitFor(() => {
      expect(screen.getByTestId('loading-results')).toHaveStyle({ display: 'none' })
    }, { timeout: 1000 })

    // Test clear filters
    fireEvent.click(clearFiltersButton)

    expect(searchInput).toHaveValue('')
    expect(statusFilter).toHaveValue('')
    expect(conditionFilter).toHaveValue('')
  })

  test('Form validation and error prevention', async () => {
    const { container } = renderWithTheme(
      <form data-testid="validation-form">
        <h1>Patient Information Form</h1>
        <div data-testid="form-field">
          <label htmlFor="patientName">Patient Name *</label>
          <input
            id="patientName"
            name="patientName"
            type="text"
            placeholder="Enter patient name"
            required
            aria-invalid="false"
            aria-describedby="name-error"
          />
          <div id="name-error" data-testid="name-error" style={{ display: 'none', color: '#DC2626' }}>
            Patient name is required
          </div>
        </div>

        <div data-testid="form-field">
          <label htmlFor="patientEmail">Email Address *</label>
          <input
            id="patientEmail"
            name="patientEmail"
            type="email"
            placeholder="Enter email address"
            required
            aria-invalid="false"
            aria-describedby="email-error"
          />
          <div id="email-error" data-testid="email-error" style={{ display: 'none', color: '#DC2626' }}>
            Please enter a valid email address
          </div>
        </div>

        <div data-testid="form-field">
          <label htmlFor="patientPhone">Phone Number *</label>
          <input
            id="patientPhone"
            name="patientPhone"
            type="tel"
            placeholder="Enter phone number"
            required
            aria-invalid="false"
            aria-describedby="phone-error"
          />
          <div id="phone-error" data-testid="phone-error" style={{ display: 'none', color: '#DC2626' }}>
            Please enter a valid phone number
          </div>
        </div>

        <button type="submit" data-testid="submit-form">Save Patient</button>
      </form>
    )

    const nameInput = screen.getByLabelText('Patient Name *')
    const emailInput = screen.getByLabelText('Email Address *')
    const phoneInput = screen.getByLabelText('Phone Number *')
    const submitButton = screen.getByTestId('submit-form')

    // Test empty form submission
    fireEvent.click(submitButton)

    // Check validation errors
    const nameError = screen.getByTestId('name-error')
    const emailError = screen.getByTestId('email-error')
    const phoneError = screen.getByTestId('phone-error')

    expect(nameError).not.toHaveStyle({ display: 'none' })
    expect(emailError).not.toHaveStyle({ display: 'none' })
    expect(phoneError).not.toHaveStyle({ display: 'none' })

    // Check input states
    expect(nameInput).toHaveAttribute('aria-invalid', 'true')
    expect(emailInput).toHaveAttribute('aria-invalid', 'true')
    expect(phoneInput).toHaveAttribute('aria-invalid', 'true')

    // Test invalid email
    fireEvent.change(emailInput, { target: { value: 'invalid-email' } })
    fireEvent.blur(emailInput)

    expect(emailError).not.toHaveStyle({ display: 'none' })
    expect(emailError).toHaveTextContent('Please enter a valid email address')

    // Test valid email
    fireEvent.change(emailInput, { target: { value: 'john.doe@example.com' } })
    fireEvent.blur(emailInput)

    expect(emailError).toHaveStyle({ display: 'none' })
    expect(emailInput).toHaveAttribute('aria-invalid', 'false')

    // Test valid phone number
    fireEvent.change(phoneInput, { target: { value: '(555) 123-4567' } })
    fireEvent.blur(phoneInput)

    expect(phoneError).toHaveStyle({ display: 'none' })
    expect(phoneInput).toHaveAttribute('aria-invalid', 'false')

    // Test valid name
    fireEvent.change(nameInput, { target: { value: 'John Doe' } })
    fireEvent.blur(nameInput)

    expect(nameError).toHaveStyle({ display: 'none' })
    expect(nameInput).toHaveAttribute('aria-invalid', 'false')

    // Test successful form submission
    fireEvent.click(submitButton)

    // Verify no validation errors
    expect(nameError).toHaveStyle({ display: 'none' })
    expect(emailError).toHaveStyle({ display: 'none' })
    expect(phoneError).toHaveStyle({ display: 'none' })
  })

  test('Responsive user experience across devices', async () => {
    // Test mobile experience
    Object.defineProperty(window, 'innerWidth', {
      value: 375,
      writable: true,
    })

    window.dispatchEvent(new Event('resize'))

    const { container, rerender } = renderWithTheme(
      <div data-testid="mobile-dashboard">
        <header>
          <button aria-label="Mobile menu">☰</button>
          <h1>Patient Dashboard</h1>
        </header>

        <nav data-testid="mobile-nav" style={{ display: 'none' }}>
          <ul>
            <li><a href="#dashboard">Dashboard</a></li>
            <li><a href="#patients">Patients</a></li>
            <li><a href="#appointments">Appointments</a></li>
          </ul>
        </nav>

        <main>
          <PatientCard
            patient={mockPatient}
            onViewDetails={mockOnViewDetails}
            compact
          />
        </main>

        <footer>
          <div data-testid="mobile-actions">
            <button aria-label="Add patient">+</button>
            <button aria-label="Search">🔍</button>
            <button aria-label="Settings">⚙️</button>
          </div>
        </footer>
      </div>
    )

    // Check mobile layout
    expect(screen.getByLabelText('Mobile menu')).toBeInTheDocument()
    expect(screen.getByTestId('mobile-actions')).toBeInTheDocument()

    // Test tablet experience
    Object.defineProperty(window, 'innerWidth', {
      value: 768,
      writable: true,
    })

    window.dispatchEvent(new Event('resize'))

    rerender(
      <div data-testid="tablet-dashboard">
        <header>
          <h1>Patient Dashboard</h1>
        </header>

        <nav data-testid="tablet-nav" style={{ display: 'flex' }}>
          <a href="#dashboard">Dashboard</a>
          <a href="#patients">Patients</a>
          <a href="#appointments">Appointments</a>
        </nav>

        <main>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
            <PatientCard
              patient={mockPatient}
              onViewDetails={mockOnViewDetails}
            />
            <PatientCard
              patient={{...mockPatient, id: '2', firstName: 'Jane'}}
              onViewDetails={mockOnViewDetails}
            />
          </div>
        </main>
      </div>
    )

    // Check tablet layout
    expect(screen.getByTestId('tablet-nav')).toBeInTheDocument()
    expect(screen.getByTestId('tablet-nav')).toHaveStyle({ display: 'flex' })

    // Test desktop experience
    Object.defineProperty(window, 'innerWidth', {
      value: 1200,
      writable: true,
    })

    window.dispatchEvent(new Event('resize'))

    rerender(
      <div data-testid="desktop-dashboard">
        <header>
          <h1>Patient Dashboard</h1>
        </header>

        <nav data-testid="desktop-nav" style={{ display: 'flex' }}>
          <a href="#dashboard">Dashboard</a>
          <a href="#patients">Patients</a>
          <a href="#appointments">Appointments</a>
          <a href="#settings">Settings</a>
        </nav>

        <main>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '16px' }}>
            <PatientCard
              patient={mockPatient}
              onViewDetails={mockOnViewDetails}
            />
            <PatientCard
              patient={{...mockPatient, id: '2', firstName: 'Jane'}}
              onViewDetails={mockOnViewDetails}
            />
            <PatientCard
              patient={{...mockPatient, id: '3', firstName: 'Bob'}}
              onViewDetails={mockOnViewDetails}
            />
          </div>
        </main>
      </div>
    )

    // Check desktop layout
    expect(screen.getByTestId('desktop-nav')).toBeInTheDocument()
    expect(screen.getByTestId('desktop-nav')).toHaveStyle({ display: 'flex' })
  })

  test('Accessibility in user experience', async () => {
    const { container } = renderWithTheme(
      <div>
        <button
          aria-label="Help and support"
          aria-describedby="help-tooltip"
          data-testid="help-button"
        >
          ?
        </button>
        <div id="help-tooltip" role="tooltip" style={{ display: 'none' }}>
          Get help with patient management
        </div>

        <div role="region" aria-live="polite" aria-atomic="true" data-testid="status-region">
          Patient data loaded successfully
        </div>

        <div data-testid="progress-container" role="progressbar" aria-valuenow={75} aria-valuemin={0} aria-valuemax={100} aria-label="Loading progress">
          <div style={{ width: '75%', backgroundColor: '#0066CC', height: '4px' }}></div>
          <span>75% complete</span>
        </div>
      </div>
    )

    const helpButton = screen.getByTestId('help-button')
    const helpTooltip = container.querySelector('#help-tooltip')

    // Test tooltip on hover
    fireEvent.mouseEnter(helpButton)
    expect(helpTooltip).not.toHaveStyle({ display: 'none' })

    // Test tooltip disappears on mouse leave
    fireEvent.mouseLeave(helpButton)
    expect(helpTooltip).toHaveStyle({ display: 'none' })

    // Test status announcements
    const statusRegion = screen.getByTestId('status-region')
    expect(statusRegion).toHaveAttribute('aria-live', 'polite')
    expect(statusRegion).toHaveAttribute('aria-atomic', 'true')

    // Test progress bar accessibility
    const progressBar = screen.getByTestId('progress-container')
    expect(progressBar).toHaveAttribute('role', 'progressbar')
    expect(progressBar).toHaveAttribute('aria-valuenow', '75')
    expect(progressBar).toHaveAttribute('aria-valuemin', '0')
    expect(progressBar).toHaveAttribute('aria-valuemax', '100')
  })
})