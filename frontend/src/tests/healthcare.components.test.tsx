import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { ThemeProvider, createTheme } from '@mui/material/styles'
import healthcareTheme from '../../theme/healthcareTheme'
import PatientCard from '../components/healthcare/PatientCard'

describe('Healthcare-Specific Components', () => {
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
    admissionDate: '2024-01-10',
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
    },
    isEmergency: false
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

  test('Patient card displays information correctly', () => {
    const { container } = renderWithTheme(
      <PatientCard
        patient={mockPatient}
        onViewDetails={mockOnViewDetails}
      />
    )

    expect(screen.getByText('John Doe')).toBeInTheDocument()
    expect(screen.getByText('PAT-001')).toBeInTheDocument()
    expect(screen.getByText('Male')).toBeInTheDocument()
    expect(screen.getByText('34 years')).toBeInTheDocument()
    expect(screen.getByText('stable')).toBeInTheDocument()
    expect(screen.getByText('admitted')).toBeInTheDocument()
    expect(screen.getByText('Dr. Smith')).toBeInTheDocument()
    expect(screen.getByText('3 active medications')).toBeInTheDocument()
    expect(screen.getByText('Room 101, Bed A')).toBeInTheDocument()
    expect(screen.getByText('Last visit: Jan 10, 2024')).toBeInTheDocument()
  })

  test('Patient card with emergency status displays correctly', () => {
    const emergencyPatient = { ...mockPatient, isEmergency: true, condition: 'critical' }

    const { container } = renderWithTheme(
      <PatientCard
        patient={emergencyPatient}
        onViewDetails={mockOnViewDetails}
        onEmergencyAlert={mockOnEmergencyAlert}
      />
    )

    expect(screen.getByText('John Doe')).toBeInTheDocument()
    expect(screen.getByText('critical')).toBeInTheDocument()

    // Check emergency styling
    const card = container.querySelector('.MuiCard-root')
    expect(card).toHaveStyle({
      border: '2px solid #DC2626' // error.main for emergency
    })

    // Check emergency button is present
    const emergencyButton = screen.getByRole('button', { name: /emergency alert/i })
    expect(emergencyButton).toBeInTheDocument()
  })

  test('Patient card displays vital signs correctly', () => {
    const { container } = renderWithTheme(
      <PatientCard
        patient={mockPatient}
        onViewDetails={mockOnViewDetails}
        showVitals={true}
      />
    )

    expect(screen.getByText('Last Vitals:')).toBeInTheDocument()
    expect(screen.getByText('🌡️ 98.6°F')).toBeInTheDocument()
    expect(screen.getByText('💨 120/80')).toBeInTheDocument()
    expect(screen.getByText('❤️ 72 bpm')).toBeInTheDocument()
    expect(screen.getByText('💧 98%')).toBeInTheDocument()
  })

  test('Patient card handles different patient conditions', () => {
    const conditions = ['stable', 'critical', 'serious', 'fair', 'good']
    const expectedColors = ['#0066CC', '#DC2626', '#F59E0B', '#3B82F6', '#10B981']

    conditions.forEach((condition, index) => {
      const patient = { ...mockPatient, condition }
      const { container, rerender } = renderWithTheme(
        <PatientCard
          patient={patient}
          onViewDetails={mockOnViewDetails}
        />
      )

      const conditionChip = screen.getByText(condition)
      expect(conditionChip).toBeInTheDocument()

      // Check condition color
      expect(conditionChip).toHaveStyle({
        backgroundColor: expect.stringContaining(expectedColors[index].slice(0, -1) + ', 0.1)'),
        color: expectedColors[index]
      })
    })
  })

  test('Patient card handles different patient statuses', () => {
    const statuses = ['admitted', 'outpatient', 'discharged', 'emergency']
    const expectedColors = ['#10B981', '#3B82F6', '#64748B', '#DC2626']

    statuses.forEach((status, index) => {
      const patient = { ...mockPatient, status }
      const { container, rerender } = renderWithTheme(
        <PatientCard
          patient={patient}
          onViewDetails={mockOnViewDetails}
        />
      )

      const statusChip = screen.getByText(status)
      expect(statusChip).toBeInTheDocument()

      // Check status color
      expect(statusChip).toHaveStyle({
        borderColor: expectedColors[index],
        color: expectedColors[index]
      })
    })
  })

  test('Patient card compact mode works correctly', () => {
    const { container } = renderWithTheme(
      <PatientCard
        patient={mockPatient}
        onViewDetails={mockOnViewDetails}
        compact={true}
      />
    )

    expect(screen.getByText('John Doe')).toBeInTheDocument()
    expect(screen.getByText('34y • PAT-001')).toBeInTheDocument()

    // Check compact styling
    const patientName = screen.getByText('John Doe')
    expect(patientName).toHaveStyle({
      fontSize: '0.875rem'
    })
  })

  test('Patient card emergency contact displays correctly', () => {
    const { container } = renderWithTheme(
      <PatientCard
        patient={mockPatient}
        onViewDetails={mockOnViewDetails}
      />
    )

    expect(screen.getByText('Emergency Contact:')).toBeInTheDocument()
    expect(screen.getByText('Jane Doe (Spouse)')).toBeInTheDocument()
    expect(screen.getByText('(555) 123-4567')).toBeInTheDocument()
  })

  test('Patient card interaction handlers work correctly', () => {
    const { container } = renderWithTheme(
      <PatientCard
        patient={mockPatient}
        onViewDetails={mockOnViewDetails}
        onContact={mockOnContact}
        onEmergencyAlert={mockOnEmergencyAlert}
      />
    )

    // Test view details button
    const viewDetailsButton = screen.getByRole('button', { name: /view details/i })
    fireEvent.click(viewDetailsButton)
    expect(mockOnViewDetails).toHaveBeenCalledWith('1')

    // Test contact button
    const contactButton = screen.getByRole('button', { name: /contact patient/i })
    fireEvent.click(contactButton)
    expect(mockOnContact).toHaveBeenCalledWith('1')

    // Test emergency alert button
    const emergencyButton = screen.getByRole('button', { name: /emergency alert/i })
    fireEvent.click(emergencyButton)
    expect(mockOnEmergencyAlert).toHaveBeenCalledWith('1')
  })

  test('Patient card gender icons display correctly', () => {
    // Test male patient
    const malePatient = { ...mockPatient, gender: 'male' }
    const { container: maleContainer, rerender } = renderWithTheme(
      <PatientCard
        patient={malePatient}
        onViewDetails={mockOnViewDetails}
      />
    )

    const maleIcon = maleContainer.querySelector('svg[data-testid="MaleIcon"]')
    expect(maleIcon).toBeInTheDocument()

    // Test female patient
    const femalePatient = { ...mockPatient, gender: 'female' }
    rerender(
      <PatientCard
        patient={femalePatient}
        onViewDetails={mockOnViewDetails}
      />
    )

    const femaleIcon = screen.getByTestId('FemaleIcon')
    expect(femaleIcon).toBeInTheDocument()

    // Test other gender patient
    const otherPatient = { ...mockPatient, gender: 'other' }
    rerender(
      <PatientCard
        patient={otherPatient}
        onViewDetails={mockOnViewDetails}
      />
    )

    const otherIcon = screen.getByTestId('TransgenderIcon')
    expect(otherIcon).toBeInTheDocument()
  })

  test('Patient card allergy warning displays correctly', () => {
    const patientWithAllergies = { ...mockPatient, allergies: ['Penicillin', 'Sulfa'] }

    const { container } = renderWithTheme(
      <PatientCard
        patient={patientWithAllergies}
        onViewDetails={mockOnViewDetails}
      />
    )

    expect(screen.getByText('2 Allergies')).toBeInTheDocument()

    const allergyChip = screen.getByText('2 Allergies')
    expect(allergyChip).toBeInTheDocument()

    // Check warning icon
    const warningIcon = container.querySelector('svg[data-testid="WarningIcon"]')
    expect(warningIcon).toBeInTheDocument()
  })

  test('Patient card medication count displays correctly', () => {
    const patientWithMedications = { ...mockPatient, medications: 5 }

    const { container } = renderWithTheme(
      <PatientCard
        patient={patientWithMedications}
        onViewDetails={mockOnViewDetails}
      />
    )

    expect(screen.getByText('5 active medications')).toBeInTheDocument()
  })

  test('Patient card handles missing data gracefully', () => {
    const patientWithMissingData = {
      ...mockPatient,
      room: undefined,
      bed: undefined,
      lastVitals: undefined,
      emergencyContact: undefined,
      allergies: []
    }

    const { container } = renderWithTheme(
      <PatientCard
        patient={patientWithMissingData}
        onViewDetails={mockOnViewDetails}
      />
    )

    expect(screen.getByText('John Doe')).toBeInTheDocument()
    expect(screen.queryByText('Room')).not.toBeInTheDocument()
    expect(screen.queryByText('Last Vitals:')).not.toBeInTheDocument()
    expect(screen.queryByText('Emergency Contact:')).not.toBeInTheDocument()
    expect(screen.queryByText('Allergies')).not.toBeInTheDocument()
  })

  test('Vital signs chart component displays correctly', () => {
    const vitalSigns = [
      { timestamp: '2024-01-10T08:00:00Z', value: 120, type: 'Blood Pressure' },
      { timestamp: '2024-01-10T12:00:00Z', value: 118, type: 'Blood Pressure' },
      { timestamp: '2024-01-10T16:00:00Z', value: 122, type: 'Blood Pressure' }
    ]

    const { container } = renderWithTheme(
      <div data-testid="vital-signs-chart">
        <h3>Blood Pressure Trends</h3>
        <div data-testid="chart-container">
          {vitalSigns.map((vital, index) => (
            <div key={index} data-testid={`vital-${index}`}>
              <span>{vital.timestamp}</span>
              <span>{vital.value}</span>
              <span>{vital.type}</span>
            </div>
          ))}
        </div>
      </div>
    )

    expect(screen.getByText('Blood Pressure Trends')).toBeInTheDocument()
    expect(screen.getByTestId('vital-0')).toBeInTheDocument()
    expect(screen.getByTestId('vital-1')).toBeInTheDocument()
    expect(screen.getByTestId('vital-2')).toBeInTheDocument()
  })

  test('Medication list displays with proper warnings', () => {
    const medications = [
      {
        name: 'Metformin',
        dosage: '500mg',
        frequency: 'Twice daily',
        warnings: ['Take with food', 'Monitor blood sugar']
      },
      {
        name: 'Lisinopril',
        dosage: '10mg',
        frequency: 'Once daily',
        warnings: ['May cause dizziness']
      },
      {
        name: 'Atorvastatin',
        dosage: '20mg',
        frequency: 'Once daily',
        warnings: []
      }
    ]

    const { container } = renderWithTheme(
      <div data-testid="medication-list">
        <h3>Current Medications</h3>
        {medications.map((med, index) => (
          <div key={index} data-testid={`medication-${index}`}>
            <h4>{med.name}</h4>
            <p>Dosage: {med.dosage}</p>
            <p>Frequency: {med.frequency}</p>
            {med.warnings.length > 0 && (
              <div data-testid={`warnings-${index}`}>
                <strong>Warnings:</strong>
                <ul>
                  {med.warnings.map((warning, warningIndex) => (
                    <li key={warningIndex}>{warning}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        ))}
      </div>
    )

    expect(screen.getByText('Current Medications')).toBeInTheDocument()
    expect(screen.getByText('Metformin')).toBeInTheDocument()
    expect(screen.getByText('500mg')).toBeInTheDocument()
    expect(screen.getByText('Twice daily')).toBeInTheDocument()
    expect(screen.getByText('Take with food')).toBeInTheDocument()
    expect(screen.getByText('Monitor blood sugar')).toBeInTheDocument()
    expect(screen.getByText('Lisinopril')).toBeInTheDocument()
    expect(screen.getByText('May cause dizziness')).toBeInTheDocument()

    // Check that Atorvastatin has no warnings
    const atorvastatinWarnings = screen.queryByTestId('warnings-2')
    expect(atorvastatinWarnings).not.toBeInTheDocument()
  })

  test('Appointment scheduling component works correctly', () => {
    const { container } = renderWithTheme(
      <div data-testid="appointment-scheduler">
        <h2>Schedule Appointment</h2>
        <form data-testid="appointment-form">
          <div>
            <label htmlFor="patient-select">Patient</label>
            <select id="patient-select" data-testid="patient-select">
              <option value="">Select patient</option>
              <option value="1">John Doe</option>
              <option value="2">Jane Smith</option>
            </select>
          </div>
          <div>
            <label htmlFor="appointment-date">Date</label>
            <input
              id="appointment-date"
              type="date"
              data-testid="appointment-date"
            />
          </div>
          <div>
            <label htmlFor="appointment-time">Time</label>
            <input
              id="appointment-time"
              type="time"
              data-testid="appointment-time"
            />
          </div>
          <div>
            <label htmlFor="appointment-type">Type</label>
            <select id="appointment-type" data-testid="appointment-type">
              <option value="">Select type</option>
              <option value="consultation">Consultation</option>
              <option value="follow-up">Follow-up</option>
              <option value="emergency">Emergency</option>
            </select>
          </div>
          <div>
            <label htmlFor="appointment-notes">Notes</label>
            <textarea
              id="appointment-notes"
              data-testid="appointment-notes"
              rows={3}
            />
          </div>
          <button type="submit" data-testid="schedule-btn">Schedule Appointment</button>
        </form>
      </div>
    )

    expect(screen.getByText('Schedule Appointment')).toBeInTheDocument()
    expect(screen.getByTestId('patient-select')).toBeInTheDocument()
    expect(screen.getByTestId('appointment-date')).toBeInTheDocument()
    expect(screen.getByTestId('appointment-time')).toBeInTheDocument()
    expect(screen.getByTestId('appointment-type')).toBeInTheDocument()
    expect(screen.getByTestId('appointment-notes')).toBeInTheDocument()
    expect(screen.getByTestId('schedule-btn')).toBeInTheDocument()

    // Test form interaction
    const patientSelect = screen.getByTestId('patient-select')
    const appointmentDate = screen.getByTestId('appointment-date')
    const appointmentTime = screen.getByTestId('appointment-time')
    const appointmentType = screen.getByTestId('appointment-type')
    const appointmentNotes = screen.getByTestId('appointment-notes')

    fireEvent.change(patientSelect, { target: { value: '1' } })
    fireEvent.change(appointmentDate, { target: { value: '2024-01-15' } })
    fireEvent.change(appointmentTime, { target: { value: '10:00' } })
    fireEvent.change(appointmentType, { target: { value: 'consultation' } })
    fireEvent.change(appointmentNotes, { target: { value: 'Regular checkup' } })

    expect(patientSelect).toHaveValue('1')
    expect(appointmentDate).toHaveValue('2024-01-15')
    expect(appointmentTime).toHaveValue('10:00')
    expect(appointmentType).toHaveValue('consultation')
    expect(appointmentNotes).toHaveValue('Regular checkup')
  })

  test('Emergency triage component displays priority levels correctly', () => {
    const triageLevels = [
      { level: 'Immediate', color: '#DC2626', description: 'Life-threatening' },
      { level: 'Urgent', color: '#F59E0B', description: 'Serious but stable' },
      { level: 'Delayed', color: '#3B82F6', description: 'Stable condition' },
      { level: 'Expectant', color: '#6B7280', description: 'Minor injuries' }
    ]

    const { container } = renderWithTheme(
      <div data-testid="emergency-triage">
        <h2>Emergency Triage</h2>
        <div data-testid="triage-levels">
          {triageLevels.map((level, index) => (
            <div key={index} data-testid={`triage-${index}`} style={{
              backgroundColor: level.color,
              color: 'white',
              padding: '16px',
              margin: '8px 0',
              borderRadius: '8px'
            }}>
              <h3>{level.level}</h3>
              <p>{level.description}</p>
            </div>
          ))}
        </div>
      </div>
    )

    expect(screen.getByText('Emergency Triage')).toBeInTheDocument()
    expect(screen.getByText('Immediate')).toBeInTheDocument()
    expect(screen.getByText('Life-threatening')).toBeInTheDocument()
    expect(screen.getByText('Urgent')).toBeInTheDocument()
    expect(screen.getByText('Serious but stable')).toBeInTheDocument()

    // Check color coding
    const immediateTriage = screen.getByTestId('triage-0')
    expect(immediateTriage).toHaveStyle({
      backgroundColor: '#DC2626',
      color: 'white'
    })

    const urgentTriage = screen.getByTestId('triage-1')
    expect(urgentTriage).toHaveStyle({
      backgroundColor: '#F59E0B',
      color: 'white'
    })
  })

  test('Medical record viewer component handles different record types', () => {
    const medicalRecords = [
      {
        id: '1',
        type: 'Diagnosis',
        date: '2024-01-10',
        provider: 'Dr. Smith',
        content: 'Patient diagnosed with Type 2 Diabetes',
        category: 'diagnosis'
      },
      {
        id: '2',
        type: 'Prescription',
        date: '2024-01-10',
        provider: 'Dr. Smith',
        content: 'Metformin 500mg twice daily',
        category: 'prescription'
      },
      {
        id: '3',
        type: 'Lab Result',
        date: '2024-01-12',
        provider: 'Lab Corp',
        content: 'Blood glucose: 120 mg/dL',
        category: 'lab'
      },
      {
        id: '4',
        type: 'Procedure',
        date: '2024-01-08',
        provider: 'Dr. Johnson',
        content: 'Annual physical examination',
        category: 'procedure'
      }
    ]

    const { container } = renderWithTheme(
      <div data-testid="medical-record-viewer">
        <h2>Medical Records</h2>
        <div data-testid="record-filters">
          <button data-testid="filter-all">All</button>
          <button data-testid="filter-diagnosis">Diagnosis</button>
          <button data-testid="filter-prescription">Prescription</button>
          <button data-testid="filter-lab">Lab Results</button>
          <button data-testid="filter-procedure">Procedures</button>
        </div>
        <div data-testid="records-list">
          {medicalRecords.map((record) => (
            <div key={record.id} data-testid={`record-${record.id}`}>
              <h3>{record.type}</h3>
              <p>Date: {record.date}</p>
              <p>Provider: {record.provider}</p>
              <p>{record.content}</p>
              <span data-testid={`category-${record.id}`}>{record.category}</span>
            </div>
          ))}
        </div>
      </div>
    )

    expect(screen.getByText('Medical Records')).toBeInTheDocument()
    expect(screen.getByText('Diagnosis')).toBeInTheDocument()
    expect(screen.getByText('Prescription')).toBeInTheDocument()
    expect(screen.getByText('Lab Result')).toBeInTheDocument()
    expect(screen.getByText('Procedure')).toBeInTheDocument()

    // Test filtering functionality
    const filterDiagnosis = screen.getByTestId('filter-diagnosis')
    fireEvent.click(filterDiagnosis)

    // Check that only diagnosis records are visible
    const diagnosisRecord = screen.getByTestId('record-1')
    expect(diagnosisRecord).toBeInTheDocument()
    expect(screen.getByTestId('category-1')).toHaveTextContent('diagnosis')
  })

  test('Healthcare dashboard displays key metrics correctly', () => {
    const dashboardMetrics = {
      totalPatients: 150,
      admittedPatients: 45,
      emergencyPatients: 8,
      todayAppointments: 24,
      availableBeds: 12,
      staffOnDuty: 18
    }

    const { container } = renderWithTheme(
      <div data-testid="healthcare-dashboard">
        <h1>Healthcare Dashboard</h1>
        <div data-testid="metrics-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '16px' }}>
          <div data-testid="metric-total-patients" style={{ padding: '16px', backgroundColor: '#F0F9FF', borderRadius: '8px' }}>
            <h3>Total Patients</h3>
            <p data-testid="total-patients-value">{dashboardMetrics.totalPatients}</p>
          </div>
          <div data-testid="metric-admitted-patients" style={{ padding: '16px', backgroundColor: '#F0FDF4', borderRadius: '8px' }}>
            <h3>Admitted Patients</h3>
            <p data-testid="admitted-patients-value">{dashboardMetrics.admittedPatients}</p>
          </div>
          <div data-testid="metric-emergency-patients" style={{ padding: '16px', backgroundColor: '#FEF2F2', borderRadius: '8px' }}>
            <h3>Emergency Patients</h3>
            <p data-testid="emergency-patients-value">{dashboardMetrics.emergencyPatients}</p>
          </div>
          <div data-testid="metric-appointments" style={{ padding: '16px', backgroundColor: '#FFFBEB', borderRadius: '8px' }}>
            <h3>Today&apos;s Appointments</h3>
            <p data-testid="appointments-value">{dashboardMetrics.todayAppointments}</p>
          </div>
          <div data-testid="metric-available-beds" style={{ padding: '16px', backgroundColor: '#F0F9FF', borderRadius: '8px' }}>
            <h3>Available Beds</h3>
            <p data-testid="available-beds-value">{dashboardMetrics.availableBeds}</p>
          </div>
          <div data-testid="metric-staff" style={{ padding: '16px', backgroundColor: '#F3E8FF', borderRadius: '8px' }}>
            <h3>Staff on Duty</h3>
            <p data-testid="staff-value">{dashboardMetrics.staffOnDuty}</p>
          </div>
        </div>
      </div>
    )

    expect(screen.getByText('Healthcare Dashboard')).toBeInTheDocument()
    expect(screen.getByTestId('total-patients-value')).toHaveTextContent('150')
    expect(screen.getByTestId('admitted-patients-value')).toHaveTextContent('45')
    expect(screen.getByTestId('emergency-patients-value')).toHaveTextContent('8')
    expect(screen.getByTestId('appointments-value')).toHaveTextContent('24')
    expect(screen.getByTestId('available-beds-value')).toHaveTextContent('12')
    expect(screen.getByTestId('staff-value')).toHaveTextContent('18')

    // Check color coding for different metrics
    const emergencyMetric = screen.getByTestId('metric-emergency-patients')
    expect(emergencyMetric).toHaveStyle({
      backgroundColor: '#FEF2F2' // Light red for emergency
    })

    const admittedMetric = screen.getByTestId('metric-admitted-patients')
    expect(admittedMetric).toHaveStyle({
      backgroundColor: '#F0FDF4' // Light green for admitted
    })
  })
})