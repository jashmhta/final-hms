import { lazy, Suspense } from 'react'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ThemeProvider } from '@mui/material/styles'
import CssBaseline from '@mui/material/CssBaseline'
import { Toaster } from 'sonner'
import { CircularProgress, Box } from '@mui/material'

// Lazy load route components
const DashboardModule = lazy(() => import('./components/modules/DashboardModule'))
const PatientCard = lazy(() => import('./components/healthcare/PatientCard'))
const MedicalRecordViewer = lazy(() => import('./components/healthcare/MedicalRecordViewer'))
const MedicationManager = lazy(() => import('./components/healthcare/MedicationManager'))
const VitalSignsMonitor = lazy(() => import('./components/healthcare/VitalSignsMonitor'))
const EmergencyTriage = lazy(() => import('./components/healthcare/EmergencyTriage'))
const AppointmentCalendar = lazy(() => import('./components/healthcare/AppointmentCalendar'))
const HealthcareDemo = lazy(() => import('./components/demo/HealthcareDemo'))

// Create query client with optimized configuration
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      cacheTime: 10 * 60 * 1000, // 10 minutes
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
})

// Loading component
const LoadingFallback = () => (
  <Box
    display="flex"
    justifyContent="center"
    alignItems="center"
    minHeight="100vh"
    flexDirection="column"
    gap={2}
  >
    <CircularProgress size={48} />
    <div>Loading HMS Enterprise...</div>
  </Box>
)

// Error boundary component
class ErrorBoundary extends React.Component<
  { children: React.ReactNode },
  { hasError: boolean; error?: Error }
> {
  constructor(props: { children: React.ReactNode }) {
    super(props)
    this.state = { hasError: false }
  }

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('Error caught by boundary:', error, errorInfo)
  }

  render() {
    if (this.state.hasError) {
      return (
        <Box
          display="flex"
          justifyContent="center"
          alignItems="center"
          minHeight="100vh"
          flexDirection="column"
          gap={2}
          p={3}
        >
          <h2>Something went wrong</h2>
          <p>We're sorry for the inconvenience. Please try refreshing the page.</p>
          <button onClick={() => window.location.reload()}>
            Refresh Page
          </button>
        </Box>
      )
    }

    return this.props.children
  }
}

// Performance-optimized App component
const App = React.memo(() => {
  return (
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <ThemeProvider theme={ healthcareTheme }>
          <CssBaseline />
          <Router>
            <Suspense fallback={<LoadingFallback />}>
              <Routes>
                <Route path="/" element={<DashboardModule />} />
                <Route path="/patients" element={<PatientCard />} />
                <Route path="/medical-records" element={<MedicalRecordViewer />} />
                <Route path="/medications" element={<MedicationManager />} />
                <Route path="/vitals" element={<VitalSignsMonitor />} />
                <Route path="/emergency" element={<EmergencyTriage />} />
                <Route path="/appointments" element={<AppointmentCalendar />} />
                <Route path="/demo" element={<HealthcareDemo />} />
              </Routes>
            </Suspense>
          </Router>
          <Toaster position="top-right" />
        </ThemeProvider>
      </QueryClientProvider>
    </ErrorBoundary>
  )
})

export default App