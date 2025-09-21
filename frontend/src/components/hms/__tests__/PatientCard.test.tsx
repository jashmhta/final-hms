import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { axe, toHaveNoViolations } from 'jest-axe'
import { ThemeProvider, createTheme } from '@mui/material'
import PatientCard from '../patients/PatientCard'

// Extend Jest expect with axe assertions
expect.extend(toHaveNoViolations)

// Mock translations
jest.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string) => key,
  }),
}))

// Mock theme
const theme = createTheme()

const mockPatient = {
  id: '1',
  medicalRecordNumber: 'MRN-001',
  firstName: 'John',
  lastName: 'Doe',
  dateOfBirth: '1990-01-01',
  gender: 'M',
  email: 'john.doe@example.com',
  phone: '+1-555-0123',
  address: '123 Main St, City, State 12345',
  emergencyContact: {
    name: 'Jane Doe',
    relationship: 'Spouse',
    phone: '+1-555-0456',
  },
  insuranceInformation: {
    provider: 'Blue Cross',
    policyNumber: 'POL-001',
    groupNumber: 'GRP-001',
    expirationDate: '2025-12-31',
  },
  allergies: ['Penicillin', 'Latex'],
  medications: ['Lisinopril'],
  medicalConditions: ['Hypertension'],
  bloodType: 'O+',
  createdAt: '2024-01-01T00:00:00Z',
  updatedAt: '2024-01-01T00:00:00Z',
}

describe('PatientCard Component', () => {
  const renderWithTheme = (component: React.ReactElement) => {
    return render(
      <ThemeProvider theme={theme}>
        {component}
      </ThemeProvider>
    )
  }

  beforeEach(() => {
    // Clear all mocks before each test
    jest.clearAllMocks()
  })

  describe('Rendering', () => {
    it('renders patient information correctly', () => {
      renderWithTheme(<PatientCard patient={mockPatient} />)

      expect(screen.getByText('John Doe')).toBeInTheDocument()
      expect(screen.getByText('MRN-001')).toBeInTheDocument()
      expect(screen.getByText('+1-555-0123')).toBeInTheDocument()
      expect(screen.getByText('john.doe@example.com')).toBeInTheDocument()
      expect(screen.getByText('O+')).toBeInTheDocument()
    })

    it('renders patient avatar with correct initials', () => {
      renderWithTheme(<PatientCard patient={mockPatient} />)

      const avatar = screen.getByText('JD')
      expect(avatar).toBeInTheDocument()
    })

    it('renders gender and age information', () => {
      renderWithTheme(<PatientCard patient={mockPatient} />)

      expect(screen.getByText('patients.male')).toBeInTheDocument()
      expect(screen.getByText(/years/)).toBeInTheDocument()
    })

    it('renders allergies correctly', () => {
      renderWithTheme(<PatientCard patient={mockPatient} />)

      expect(screen.getByText('Penicillin')).toBeInTheDocument()
      expect(screen.getByText('Latex')).toBeInTheDocument()
    })

    it('renders emergency contact information', () => {
      renderWithTheme(<PatientCard patient={mockPatient} />)

      expect(screen.getByText('Jane Doe - +1-555-0456')).toBeInTheDocument()
    })
  })

  describe('Compact Mode', () => {
    it('renders compact version correctly', () => {
      renderWithTheme(<PatientCard patient={mockPatient} compact />)

      expect(screen.getByText('John Doe')).toBeInTheDocument()
      expect(screen.getByText('MRN-001')).toBeInTheDocument()
      // Check that less detailed information is shown in compact mode
      expect(screen.queryByText('123 Main St')).not.toBeInTheDocument()
    })
  })

  describe('Interactions', () => {
    it('calls onEdit when edit button is clicked', () => {
      const onEdit = jest.fn()
      renderWithTheme(
        <PatientCard patient={mockPatient} onEdit={onEdit} />
      )

      const editButton = screen.getByRole('button', { name: /edit/i })
      fireEvent.click(editButton)

      expect(onEdit).toHaveBeenCalledWith(mockPatient)
    })

    it('calls onView when view button is clicked', () => {
      const onView = jest.fn()
      renderWithTheme(
        <PatientCard patient={mockPatient} onView={onView} />
      )

      const viewButton = screen.getByRole('button', { name: /view/i })
      fireEvent.click(viewButton)

      expect(onView).toHaveBeenCalledWith(mockPatient)
    })

    it('handles missing action handlers gracefully', () => {
      renderWithTheme(<PatientCard patient={mockPatient} />)

      // Should not throw errors when action handlers are not provided
      const buttons = screen.getAllByRole('button')
      buttons.forEach(button => {
        expect(() => fireEvent.click(button)).not.toThrow()
      })
    })
  })

  describe('Accessibility', () => {
    it('should have no accessibility violations', async () => {
      const { container } = renderWithTheme(
        <PatientCard patient={mockPatient} />
      )

      const results = await axe(container)
      expect(results).toHaveNoViolations()
    })

    it('should be keyboard navigable', () => {
      const onEdit = jest.fn()
      const onView = jest.fn()

      renderWithTheme(
        <PatientCard patient={mockPatient} onEdit={onEdit} onView={onView} />
      )

      // Test keyboard navigation
      const editButton = screen.getByRole('button', { name: /edit/i })
      const viewButton = screen.getByRole('button', { name: /view/i })

      // Tab navigation should work
      editButton.focus()
      expect(document.activeElement).toBe(editButton)

      fireEvent.keyDown(editButton, { key: 'Tab' })
      expect(document.activeElement).toBe(viewButton)

      // Enter key should trigger action
      fireEvent.keyDown(editButton, { key: 'Enter' })
      expect(onEdit).toHaveBeenCalledWith(mockPatient)
    })

    it('should have proper ARIA labels', () => {
      renderWithTheme(<PatientCard patient={mockPatient} />)

      const avatar = screen.getByText('JD').closest('div')
      expect(avatar).toHaveAttribute('aria-label', 'John Doe avatar')

      const editButton = screen.getByRole('button', { name: /edit/i })
      expect(editButton).toHaveAttribute('aria-label', 'Edit patient')
    })
  })

  describe('Responsive Design', () => {
    it('should adapt to different screen sizes', () => {
      // Mock different screen sizes
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 320, // Mobile
      })

      renderWithTheme(<PatientCard patient={mockPatient} />)

      // Should render without errors on mobile
      expect(screen.getByText('John Doe')).toBeInTheDocument()

      // Test desktop size
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 1920, // Desktop
      })

      renderWithTheme(<PatientCard patient={mockPatient} />)

      expect(screen.getByText('John Doe')).toBeInTheDocument()
    })
  })

  describe('Performance', () => {
    it('should not re-render unnecessarily', () => {
      const { rerender } = renderWithTheme(
        <PatientCard patient={mockPatient} />
      )

      // Spy on console.log to detect unnecessary re-renders
      const consoleSpy = jest.spyOn(console, 'log')

      // Re-render with same props
      rerender(<PatientCard patient={mockPatient} />)

      // Should not log any warnings about unnecessary re-renders
      expect(consoleSpy).not.toHaveBeenCalled()

      consoleSpy.mockRestore()
    })

    it('should handle large patient data efficiently', () => {
      const largePatientData = {
        ...mockPatient,
        allergies: Array(50).fill('Test Allergy'),
        medications: Array(100).fill('Test Medication'),
      }

      const { container } = renderWithTheme(
        <PatientCard patient={largePatientData} />
      )

      // Should render without performance issues
      expect(container).toBeInTheDocument()

      // Should limit displayed items
      const allergyChips = screen.getAllByText('Test Allergy')
      expect(allergyChips.length).toBeLessThan(50) // Should show limited items
    })
  })

  describe('Edge Cases', () => {
    it('should handle missing patient data gracefully', () => {
      const incompletePatient = {
        ...mockPatient,
        allergies: undefined,
        emergencyContact: undefined,
      }

      renderWithTheme(<PatientCard patient={incompletePatient} />)

      // Should still render without errors
      expect(screen.getByText('John Doe')).toBeInTheDocument()
    })

    it('should handle empty arrays correctly', () => {
      const patientWithNoAllergies = {
        ...mockPatient,
        allergies: [],
      }

      renderWithTheme(<PatientCard patient={patientWithNoAllergies} />)

      // Should not render allergy section
      expect(screen.queryByText('patients.allergies')).not.toBeInTheDocument()
    })

    it('should handle special characters in names', () => {
      const patientWithSpecialChars = {
        ...mockPatient,
        firstName: 'José María',
        lastName: 'González',
      }

      renderWithTheme(<PatientCard patient={patientWithSpecialChars} />)

      expect(screen.getByText('José María González')).toBeInTheDocument()
    })
  })
})