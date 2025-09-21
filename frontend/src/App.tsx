import { lazy, Suspense, useEffect } from 'react'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { Provider } from 'react-redux'
import { PersistGate } from 'redux-persist/integration/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ThemeProvider } from '@mui/material/styles'
import CssBaseline from '@mui/material/CssBaseline'
import { Toaster } from 'sonner'
import { CircularProgress, Box } from '@mui/material'
import healthcareTheme from './theme/healthcareTheme'
import { store, persistor } from './store/store'

// Performance monitoring components
import WebVitalsMonitor from './components/performance/WebVitalsMonitor'
import BundleAnalyzer from './components/performance/BundleAnalyzer'
import PerformanceTracker from './components/performance/PerformanceTracker'

// Lazy load route components
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

// Service Worker Registration
const registerServiceWorker = () => {
  if ('serviceWorker' in navigator && process.env.NODE_ENV === 'production') {
    window.addEventListener('load', () => {
      navigator.serviceWorker.register('/sw.js')
        .then((registration) => {
          console.log('SW registered: ', registration)
        })
        .catch((registrationError) => {
          console.log('SW registration failed: ', registrationError)
        })
    })
  }
}

// Performance-optimized App component
const App = React.memo(() => {
  // Register service worker on mount
  useEffect(() => {
    registerServiceWorker()
  }, [])

  return (
    <ErrorBoundary>
      <Provider store={store}>
        <PersistGate loading={<LoadingFallback />} persistor={persistor}>
          <QueryClientProvider client={queryClient}>
            <ThemeProvider theme={healthcareTheme}>
              <CssBaseline />
              <Router>
                <Suspense fallback={<LoadingFallback />}>
                  <Routes>
                    <Route path="/" element={<HealthcareDemo />} />
                  </Routes>
                </Suspense>
              </Router>
              <Toaster position="top-right" />

              {/* Performance monitoring components */}
              {process.env.NODE_ENV === 'development' && (
                <>
                  <WebVitalsMonitor enableDebugMode />
                  <BundleAnalyzer enableDebugMode />
                  <PerformanceTracker enableDebugMode />
                </>
              )}
              {process.env.NODE_ENV === 'production' && (
                <>
                  <WebVitalsMonitor sampleRate={0.1} />
                  <BundleAnalyzer />
                </>
              )}
            </ThemeProvider>
          </QueryClientProvider>
        </PersistGate>
      </Provider>
    </ErrorBoundary>
  )
})

export default App