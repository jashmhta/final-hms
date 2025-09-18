import React from 'react'
import { render, screen } from '@testing-library/react'
import { ThemeProvider, createTheme } from '@mui/material/styles'
import { CssBaseline } from '@mui/material'
import App from '../App'
const theme = createTheme({
  palette: {
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
  },
})
const renderWithTheme = (component: React.ReactElement) => {
  return render(
    <ThemeProvider theme={theme}>
      <CssBaseline />
      {component}
    </ThemeProvider>
  )
}
describe('App', () => {
  test('renders App component', () => {
    renderWithTheme(<App />)
    expect(screen.getByRole('main')).toBeInTheDocument()
  })
  test('renders DashboardModule on root route', () => {
    renderWithTheme(<App />)
    expect(screen.getByText('Healthcare Management System')).toBeInTheDocument()
  })
})