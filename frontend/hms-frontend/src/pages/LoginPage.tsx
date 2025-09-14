import { useState } from 'react'
import { Box, Button, Container, Paper, Stack, TextField, Typography, Alert } from '@mui/material'
import axios from 'axios'

export default function LoginPage() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      const res = await axios.post('/api/auth/token/', { username, password })
      const { access, refresh } = res.data
      localStorage.setItem('accessToken', access)
      localStorage.setItem('refreshToken', refresh)
      window.location.href = '/'
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Login failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <Container maxWidth="xs" sx={{ mt: 10 }}>
      <Paper elevation={3} sx={{ p: 3 }}>
        <Typography variant="h5" gutterBottom>HMS Login</Typography>
        {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
        <Box component="form" onSubmit={onSubmit}>
          <Stack spacing={2}>
            <TextField label="Username" value={username} onChange={e => setUsername(e.target.value)} fullWidth autoFocus />
            <TextField label="Password" type="password" value={password} onChange={e => setPassword(e.target.value)} fullWidth />
            <Button type="submit" variant="contained" disabled={loading}>{loading ? 'Logging in...' : 'Login'}</Button>
          </Stack>
        </Box>
      </Paper>
    </Container>
  )
}
