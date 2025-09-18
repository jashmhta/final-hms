import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import healthcareTheme from './theme/healthcareTheme'
import HealthcareDemo from './components/demo/HealthcareDemo'

// Create a client for React Query
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
})

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <HealthcareDemo />
    </QueryClientProvider>
  )
}

export default App