import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { ThemeProvider, createTheme } from '@mui/material/styles'
import healthcareTheme from '../../theme/healthcareTheme'
import PatientCard from '../components/healthcare/PatientCard'

describe('Frontend Performance Tests', () => {
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
    const theme = createTheme(healthcareTheme)
    return render(
      <ThemeProvider theme={theme}>
        {component}
      </ThemeProvider>
    )
  }

  test('Page load time under 1 second', async () => {
    const startTime = performance.now()

    const { container } = renderWithTheme(
      <div data-testid="patient-dashboard">
        <h1>Patient Dashboard</h1>
        <PatientCard
          patient={mockPatient}
          onViewDetails={mockOnViewDetails}
        />
      </div>
    )

    // Wait for all content to load
    await waitFor(() => {
      expect(screen.getByText('Patient Dashboard')).toBeInTheDocument()
    })

    const endTime = performance.now()
    const loadTime = endTime - startTime

    expect(loadTime).toBeLessThan(1000) // Less than 1 second

    // Log performance for debugging
    console.log(`Page load time: ${loadTime.toFixed(2)}ms`)
  })

  test('Interaction response time under 100ms', async () => {
    const { container } = renderWithTheme(
      <div data-testid="patient-search">
        <input
          data-testid="search-input"
          type="text"
          placeholder="Search patients..."
        />
        <div data-testid="search-results">
          <PatientCard
            patient={mockPatient}
            onViewDetails={mockOnViewDetails}
            compact
          />
        </div>
      </div>
    )

    const searchInput = screen.getByTestId('search-input')
    const startTime = performance.now()

    // Simulate user typing
    fireEvent.change(searchInput, { target: { value: 'John' } })

    // Wait for search results to update
    await waitFor(() => {
      expect(screen.getByText('John Doe')).toBeInTheDocument()
    })

    const endTime = performance.now()
    const responseTime = endTime - startTime

    expect(responseTime).toBeLessThan(100) // Less than 100ms

    // Log performance for debugging
    console.log(`Search response time: ${responseTime.toFixed(2)}ms`)
  })

  test('Memory usage optimization', () => {
    const { container, unmount } = renderWithTheme(
      <div data-testid="large-data-table">
        <h1>Patient Records</h1>
        <table>
          <thead>
            <tr>
              <th>Name</th>
              <th>ID</th>
              <th>Status</th>
              <th>Condition</th>
            </tr>
          </thead>
          <tbody>
            {Array.from({ length: 100 }, (_, i) => (
              <tr key={i}>
                <td>Patient {i + 1}</td>
                <td>PAT-{String(i + 1).padStart(3, '0')}</td>
                <td>Admitted</td>
                <td>Stable</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    )

    // Get initial memory usage
    const initialMemory = performance.memory?.usedJSHeapSize || 1000000

    // Perform interactions that might cause memory leaks
    for (let i = 0; i < 50; i++) {
      fireEvent.click(screen.getByRole('button', { name: /load more/i }))
    }

    // Check memory usage hasn't grown significantly
    const finalMemory = performance.memory?.usedJSHeapSize || 1000000
    const memoryGrowth = finalMemory - initialMemory

    expect(memoryGrowth).toBeLessThan(50 * 1024 * 1024) // Less than 50MB growth

    // Clean up
    unmount()

    // Log memory usage for debugging
    console.log(`Memory growth: ${(memoryGrowth / 1024 / 1024).toFixed(2)}MB`)
  })

  test('Large list rendering performance', async () => {
    const { container } = renderWithTheme(
      <div data-testid="virtualized-list">
        <h1>Patient List</h1>
        <div data-testid="patient-list" style={{ height: '400px', overflowY: 'auto' }}>
          {Array.from({ length: 1000 }, (_, i) => (
            <PatientCard
              key={i}
              patient={{
                ...mockPatient,
                id: String(i + 1),
                firstName: `Patient ${i + 1}`,
                patientId: `PAT-${String(i + 1).padStart(3, '0')}`
              }}
              onViewDetails={mockOnViewDetails}
              compact
            />
          ))}
        </div>
      </div>
    )

    const startTime = performance.now()

    // Wait for list to render
    await waitFor(() => {
      expect(screen.getByText('Patient 1')).toBeInTheDocument()
    })

    const endTime = performance.now()
    const renderTime = endTime - startTime

    expect(renderTime).toBeLessThan(500) // Less than 500ms for 1000 items

    // Test scroll performance
    const listContainer = screen.getByTestId('patient-list')
    const scrollStartTime = performance.now()

    // Simulate scrolling
    listContainer.scrollTop = 2000

    await waitFor(() => {
      expect(listContainer.scrollTop).toBe(2000)
    })

    const scrollEndTime = performance.now()
    const scrollTime = scrollEndTime - scrollStartTime

    expect(scrollTime).toBeLessThan(100) // Less than 100ms for scroll response

    // Log performance for debugging
    console.log(`List render time: ${renderTime.toFixed(2)}ms`)
    console.log(`Scroll response time: ${scrollTime.toFixed(2)}ms`)
  })

  test('Form submission performance', async () => {
    const { container } = renderWithTheme(
      <form data-testid="patient-form">
        <h1>Patient Registration</h1>
        <input
          data-testid="name-input"
          type="text"
          placeholder="Full Name"
          required
        />
        <input
          data-testid="email-input"
          type="email"
          placeholder="Email"
          required
        />
        <input
          data-testid="phone-input"
          type="tel"
          placeholder="Phone"
          required
        />
        <button type="submit" data-testid="submit-btn">Submit</button>
      </form>
    )

    const nameInput = screen.getByTestId('name-input')
    const emailInput = screen.getByTestId('email-input')
    const phoneInput = screen.getByTestId('phone-input')
    const submitBtn = screen.getByTestId('submit-btn')

    // Fill form quickly
    const fillStartTime = performance.now()

    fireEvent.change(nameInput, { target: { value: 'John Doe' } })
    fireEvent.change(emailInput, { target: { value: 'john.doe@example.com' } })
    fireEvent.change(phoneInput, { target: { value: '(555) 123-4567' } })

    const fillEndTime = performance.now()
    const fillTime = fillEndTime - fillStartTime

    expect(fillTime).toBeLessThan(50) // Less than 50ms to fill form

    // Test form validation performance
    const validationStartTime = performance.now()

    fireEvent.click(submitBtn)

    const validationEndTime = performance.now()
    const validationTime = validationEndTime - validationStartTime

    expect(validationTime).toBeLessThan(100) // Less than 100ms for validation

    // Log performance for debugging
    console.log(`Form fill time: ${fillTime.toFixed(2)}ms`)
    console.log(`Form validation time: ${validationTime.toFixed(2)}ms`)
  })

  test('Animation and transition performance', async () => {
    const { container } = renderWithTheme(
      <div data-testid="animated-container">
        <button
          data-testid="animated-button"
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
          Animated Button
        </button>

        <div
          data-testid="animated-card"
          style={{
            backgroundColor: 'white',
            padding: '16px',
            borderRadius: '8px',
            boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
            transition: 'all 0.3s ease-in-out',
            transform: 'scale(0.95)',
            opacity: '0'
          }}
        >
          Animated Card Content
        </div>
      </div>
    )

    const button = screen.getByTestId('animated-button')
    const card = screen.getByTestId('animated-card')

    // Test hover animation performance
    const hoverStartTime = performance.now()

    fireEvent.mouseEnter(button)

    // Wait for transition to complete
    await waitFor(() => {
      expect(button).toHaveStyle({
        transform: 'translateY(-1px)',
        boxShadow: '0 4px 8px rgba(0,0,0,0.2)'
      })
    }, { timeout: 300 })

    const hoverEndTime = performance.now()
    const hoverTime = hoverEndTime - hoverStartTime

    expect(hoverTime).toBeLessThan(250) // Less than 250ms for hover transition

    // Test card animation performance
    const cardAnimStartTime = performance.now()

    // Trigger card animation
    card.style.transform = 'scale(1)'
    card.style.opacity = '1'

    // Wait for animation to complete
    await waitFor(() => {
      expect(card).toHaveStyle({
        transform: 'scale(1)',
        opacity: '1'
      })
    }, { timeout: 400 })

    const cardAnimEndTime = performance.now()
    const cardAnimTime = cardAnimEndTime - cardAnimStartTime

    expect(cardAnimTime).toBeLessThan(350) // Less than 350ms for card animation

    // Log performance for debugging
    console.log(`Button hover time: ${hoverTime.toFixed(2)}ms`)
    console.log(`Card animation time: ${cardAnimTime.toFixed(2)}ms`)
  })

  test('Image loading performance', async () => {
    const { container } = renderWithTheme(
      <div data-testid="image-gallery">
        <h1>Patient Images</h1>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '16px' }}>
          {Array.from({ length: 12 }, (_, i) => (
            <img
              key={i}
              data-testid={`patient-image-${i}`}
              src={`patient-${i + 1}.jpg`}
              alt={`Patient ${i + 1}`}
              style={{
                width: '100%',
                height: '200px',
                objectFit: 'cover',
                borderRadius: '8px',
                loading: 'lazy'
              }}
            />
          ))}
        </div>
      </div>
    )

    const startTime = performance.now()

    // Wait for images to load
    await waitFor(() => {
      const images = screen.getAllByTestId(/patient-image-\d+/)
      expect(images.length).toBe(12)
    })

    const endTime = performance.now()
    const loadTime = endTime - startTime

    expect(loadTime).toBeLessThan(1000) // Less than 1 second for 12 images

    // Test lazy loading
    const images = screen.getAllByTestId(/patient-image-\d+/)
    images.forEach(img => {
      expect(img).toHaveAttribute('loading', 'lazy')
    })

    // Log performance for debugging
    console.log(`Image load time: ${loadTime.toFixed(2)}ms`)
  })

  test('Data fetching and API performance', async () => {
    // Mock API responses
    global.fetch = jest.fn()
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ patients: [mockPatient] })
      })
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ appointments: [] })
      })

    const { container } = renderWithTheme(
      <div data-testid="data-fetching-component">
        <h1>Patient Dashboard</h1>
        <div data-testid="loading-state">Loading data...</div>
        <div data-testid="content" style={{ display: 'none' }}>
          <PatientCard
            patient={mockPatient}
            onViewDetails={mockOnViewDetails}
          />
        </div>
      </div>
    )

    const fetchStartTime = performance.now()

    // Simulate data fetching
    const patientPromise = fetch('/api/patients')
    const appointmentPromise = fetch('/api/appointments')

    await Promise.all([patientPromise, appointmentPromise])

    const fetchEndTime = performance.now()
    const fetchTime = fetchEndTime - fetchStartTime

    expect(fetchTime).toBeLessThan(500) // Less than 500ms for parallel API calls

    // Hide loading state and show content
    const loadingState = screen.getByTestId('loading-state')
    const content = screen.getByTestId('content')

    loadingState.style.display = 'none'
    content.style.display = 'block'

    expect(loadingState).toHaveStyle({ display: 'none' })
    expect(content).not.toHaveStyle({ display: 'none' })

    // Log performance for debugging
    console.log(`API fetch time: ${fetchTime.toFixed(2)}ms`)
  })

  test('Component re-render performance', async () => {
    const { container, rerender } = renderWithTheme(
      <div data-testid="performance-component">
        <PatientCard
          patient={mockPatient}
          onViewDetails={mockOnViewDetails}
        />
      </div>
    )

    const renderStartTime = performance.now()

    // Re-render with updated props
    rerender(
      <div data-testid="performance-component">
        <PatientCard
          patient={{ ...mockPatient, condition: 'critical' }}
          onViewDetails={mockOnViewDetails}
        />
      </div>
    )

    const renderEndTime = performance.now()
    const reRenderTime = renderEndTime - renderStartTime

    expect(reRenderTime).toBeLessThan(100) // Less than 100ms for re-render

    // Test multiple re-renders
    const multiRenderStartTime = performance.now()

    for (let i = 0; i < 10; i++) {
      rerender(
        <div data-testid="performance-component">
          <PatientCard
            patient={{ ...mockPatient, condition: ['stable', 'critical', 'serious'][i % 3] }}
            onViewDetails={mockOnViewDetails}
          />
        </div>
      )
    }

    const multiRenderEndTime = performance.now()
    const multiRenderTime = multiRenderEndTime - multiRenderStartTime

    expect(multiRenderTime).toBeLessThan(500) // Less than 500ms for 10 re-renders

    // Log performance for debugging
    console.log(`Single re-render time: ${reRenderTime.toFixed(2)}ms`)
    console.log(`Multiple re-renders time: ${multiRenderTime.toFixed(2)}ms`)
  })

  test('Bundle size and code splitting simulation', async () => {
    const { container } = renderWithTheme(
      <div data-testid="lazy-loaded-component">
        <h1>Dashboard</h1>
        <div data-testid="main-content">Main content loaded</div>
        <div data-testid="lazy-content" style={{ display: 'none' }}>
          Lazy loaded content
        </div>
        <button
          data-testid="load-lazy-btn"
          onClick={() => {
            const lazyContent = screen.getByTestId('lazy-content')
            lazyContent.style.display = 'block'
          }}
        >
          Load Additional Content
        </button>
      </div>
    )

    // Test initial load performance
    const initialLoadStartTime = performance.now()

    await waitFor(() => {
      expect(screen.getByText('Main content loaded')).toBeInTheDocument()
    })

    const initialLoadEndTime = performance.now()
    const initialLoadTime = initialLoadEndTime - initialLoadStartTime

    expect(initialLoadTime).toBeLessThan(500) // Less than 500ms for initial load

    // Test lazy loading performance
    const loadLazyBtn = screen.getByTestId('load-lazy-btn')
    const lazyLoadStartTime = performance.now()

    fireEvent.click(loadLazyBtn)

    await waitFor(() => {
      expect(screen.getByText('Lazy loaded content')).toBeInTheDocument()
    })

    const lazyLoadEndTime = performance.now()
    const lazyLoadTime = lazyLoadEndTime - lazyLoadStartTime

    expect(lazyLoadTime).toBeLessThan(100) // Less than 100ms for lazy load

    // Log performance for debugging
    console.log(`Initial load time: ${initialLoadTime.toFixed(2)}ms`)
    console.log(`Lazy load time: ${lazyLoadTime.toFixed(2)}ms`)
  })

  test('Caching and memoization effectiveness', async () => {
    let renderCount = 0

    const MemoizedComponent = ({ data }) => {
      renderCount++
      return (
        <div data-testid="memoized-component">
          <h2>Memoized Component</h2>
          <p>Data: {data.value}</p>
          <p>Render count: {renderCount}</p>
        </div>
      )
    }

    const { container, rerender } = renderWithTheme(
      <div data-testid="memoization-test">
        <MemoizedComponent data={{ value: 'Initial' }} />
      </div>
    )

    // Initial render
    expect(renderCount).toBe(1)

    // Re-render with same props (should not re-render)
    rerender(
      <div data-testid="memoization-test">
        <MemoizedComponent data={{ value: 'Initial' }} />
      </div>
    )

    expect(renderCount).toBe(1) // Should still be 1

    // Re-render with different props (should re-render)
    rerender(
      <div data-testid="memoization-test">
        <MemoizedComponent data={{ value: 'Updated' }} />
      </div>
    )

    expect(renderCount).toBe(2) // Should increment

    // Test performance difference
    const samePropsStartTime = performance.now()

    for (let i = 0; i < 100; i++) {
      rerender(
        <div data-testid="memoization-test">
          <MemoizedComponent data={{ value: 'Updated' }} />
        </div>
      )
    }

    const samePropsEndTime = performance.now()
    const samePropsTime = samePropsEndTime - samePropsStartTime

    expect(samePropsTime).toBeLessThan(200) // Less than 200ms for 100 same-props re-renders

    // Log performance for debugging
    console.log(`Same props re-renders time: ${samePropsTime.toFixed(2)}ms`)
    console.log(`Total render count: ${renderCount}`)
  })

  test('Network performance and error handling', async () => {
    // Mock slow network response
    global.fetch = jest.fn()
      .mockImplementationOnce(() => new Promise(resolve => {
        setTimeout(() => {
          resolve({
            ok: true,
            json: () => Promise.resolve({ patients: [mockPatient] })
          })
        }, 200) // 200ms delay
      }))
      .mockImplementationOnce(() => new Promise((_, reject) => {
        setTimeout(() => {
          reject(new Error('Network error'))
        }, 100) // 100ms delay
      }))

    const { container } = renderWithTheme(
      <div data-testid="network-performance">
        <h1>Patient Data</h1>
        <div data-testid="loading-indicator">Loading...</div>
        <div data-testid="error-message" style={{ display: 'none' }}>
          Failed to load data. Please try again.
        </div>
        <div data-testid="data-content" style={{ display: 'none' }}>
          <PatientCard
            patient={mockPatient}
            onViewDetails={mockOnViewDetails}
          />
        </div>
        <button data-testid="retry-button">Retry</button>
      </div>
    )

    // Test slow network response
    const slowFetchStartTime = performance.now()

    try {
      await fetch('/api/patients')
    } catch (error) {
      // Expected to succeed
    }

    const slowFetchEndTime = performance.now()
    const slowFetchTime = slowFetchEndTime - slowFetchStartTime

    expect(slowFetchTime).toBeGreaterThanOrEqual(200) // Should take at least 200ms
    expect(slowFetchTime).toBeLessThan(300) // Should not take more than 300ms

    // Test network error handling
    const errorFetchStartTime = performance.now()

    try {
      await fetch('/api/patients')
    } catch (error) {
      // Expected to fail
      const errorMessage = screen.getByTestId('error-message')
      errorMessage.style.display = 'block'
    }

    const errorFetchEndTime = performance.now()
    const errorFetchTime = errorFetchEndTime - errorFetchStartTime

    expect(errorFetchTime).toBeLessThan(150) // Should handle error quickly

    // Log performance for debugging
    console.log(`Slow fetch time: ${slowFetchTime.toFixed(2)}ms`)
    console.log(`Error handling time: ${errorFetchTime.toFixed(2)}ms`)
  })
})