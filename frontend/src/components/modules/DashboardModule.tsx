import React, { useState } from 'react'
import {
  Box,
  Container,
  Card,
  CardContent,
  Typography,
  Button,
  IconButton,
  AppBar,
  Toolbar,
  Drawer,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Chip,
  Alert,
  Tab,
  Tabs,
} from '@mui/material'
import {
  Dashboard,
  People,
  Event,
  MedicalServices,
  LocalPharmacy,
  Science,
  Settings,
  Notifications,
  TrendingUp,
  Assignment,
  Payment,
  Message,
} from '@mui/icons-material'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, BarChart, Bar, PieChart, Pie, Cell } from 'recharts'
const drawerWidth = 240
const DashboardModule: React.FC = () => {
  const [mobileOpen, setMobileOpen] = useState(false)
  const [currentTab, setCurrentTab] = useState(0)
  const handleDrawerToggle = () => {
    setMobileOpen(!mobileOpen)
  }
  const menuItems = [
    { text: 'Dashboard', icon: <Dashboard /> },
    { text: 'Patients', icon: <People /> },
    { text: 'Appointments', icon: <Event /> },
    { text: 'Medical Records', icon: <MedicalServices /> },
    { text: 'Pharmacy', icon: <LocalPharmacy /> },
    { text: 'Laboratory', icon: <Science /> },
    { text: 'Billing', icon: <Payment /> },
    { text: 'Messages', icon: <Message /> },
    { text: 'Reports', icon: <Assignment /> },
    { text: 'Analytics', icon: <TrendingUp /> },
    { text: 'Settings', icon: <Settings /> },
  ]
  const patientData = [
    { name: 'Jan', patients: 65, admitted: 28 },
    { name: 'Feb', patients: 59, admitted: 48 },
    { name: 'Mar', patients: 80, admitted: 40 },
    { name: 'Apr', patients: 81, admitted: 19 },
    { name: 'May', patients: 56, admitted: 86 },
    { name: 'Jun', patients: 55, admitted: 27 },
  ]
  const departmentData = [
    { name: 'Emergency', value: 400, color: '#ff6b6b' },
    { name: 'ICU', value: 300, color: '#4ecdc4' },
    { name: 'General', value: 300, color: '#45b7d1' },
    { name: 'Surgery', value: 200, color: '#96ceb4' },
  ]
  const drawer = (
    <div>
      <Toolbar>
        <Typography variant="h6" noWrap component="div">
          HMS Enterprise
        </Typography>
      </Toolbar>
      <List>
        {menuItems.map((item) => (
          <ListItem key={item.text}>
            <ListItemIcon>{item.icon}</ListItemIcon>
            <ListItemText primary={item.text} />
          </ListItem>
        ))}
      </List>
    </div>
  )
  return (
    <Box sx={{ display: 'flex' }}>
      <AppBar
        position="fixed"
        sx={{
          width: { sm: `calc(100% - ${drawerWidth}px)` },
          ml: { sm: `${drawerWidth}px` },
        }}
      >
        <Toolbar>
          <IconButton
            color="inherit"
            aria-label="open drawer"
            onClick={handleDrawerToggle}
            sx={{ mr: 2, display: { sm: 'none' } }}
          >
            <Dashboard />
          </IconButton>
          <Typography variant="h6" noWrap component="div" sx={{ flexGrow: 1 }}>
            Healthcare Management System
          </Typography>
          <Chip label="Online" color="success" variant="outlined" />
          <Button color="inherit">
            <Notifications />
          </Button>
        </Toolbar>
      </AppBar>
      <Box
        component="nav"
        sx={{ width: { sm: drawerWidth }, flexShrink: { sm: 0 } }}
      >
        <Drawer
          variant="temporary"
          open={mobileOpen}
          onClose={handleDrawerToggle}
          ModalProps={{
            keepMounted: true,
          }}
          sx={{
            display: { xs: 'block', sm: 'none' },
            '& .MuiDrawer-paper': { boxSizing: 'border-box', width: drawerWidth },
          }}
        >
          {drawer}
        </Drawer>
        <Drawer
          variant="permanent"
          sx={{
            display: { xs: 'none', sm: 'block' },
            '& .MuiDrawer-paper': { boxSizing: 'border-box', width: drawerWidth },
          }}
          open
        >
          {drawer}
        </Drawer>
      </Box>
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          p: 3,
          width: { sm: `calc(100% - ${drawerWidth}px)` },
        }}
      >
        <Toolbar />
        <Alert severity="info" sx={{ mb: 2 }}>
          System Status: All services operational | Last updated: {new Date().toLocaleString()}
        </Alert>
        <Tabs value={currentTab} onChange={(_, newValue) => setCurrentTab(newValue)} sx={{ mb: 3 }}>
          <Tab label="Overview" />
          <Tab label="Analytics" />
          <Tab label="Patients" />
          <Tab label="Operations" />
        </Tabs>
        {currentTab === 0 && (
          <Container maxWidth="lg">
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 3 }}>
              <Box sx={{ width: { xs: '100%', sm: 'calc(50% - 12px)', md: 'calc(25% - 9px)' } }}>
                <Card>
                  <CardContent>
                    <Typography color="textSecondary" gutterBottom>
                      Total Patients
                    </Typography>
                    <Typography variant="h4" component="h2">
                      1,247
                    </Typography>
                    <Typography color="textSecondary">
                      +12% from last month
                    </Typography>
                  </CardContent>
                </Card>
              </Box>
              <Box sx={{ width: { xs: '100%', sm: 'calc(50% - 12px)', md: 'calc(25% - 9px)' } }}>
                <Card>
                  <CardContent>
                    <Typography color="textSecondary" gutterBottom>
                      Appointments Today
                    </Typography>
                    <Typography variant="h4" component="h2">
                      84
                    </Typography>
                    <Typography color="textSecondary">
                      3 urgent cases
                    </Typography>
                  </CardContent>
                </Card>
              </Box>
              <Box sx={{ width: { xs: '100%', sm: 'calc(50% - 12px)', md: 'calc(25% - 9px)' } }}>
                <Card>
                  <CardContent>
                    <Typography color="textSecondary" gutterBottom>
                      Available Beds
                    </Typography>
                    <Typography variant="h4" component="h2">
                      23/150
                    </Typography>
                    <Typography color="textSecondary">
                      84% occupancy
                    </Typography>
                  </CardContent>
                </Card>
              </Box>
              <Box sx={{ width: { xs: '100%', sm: 'calc(50% - 12px)', md: 'calc(25% - 9px)' } }}>
                <Card>
                  <CardContent>
                    <Typography color="textSecondary" gutterBottom>
                      Staff On Duty
                    </Typography>
                    <Typography variant="h4" component="h2">
                      67
                    </Typography>
                    <Typography color="textSecondary">
                      All departments covered
                    </Typography>
                  </CardContent>
                </Card>
              </Box>
              <Box sx={{ width: { xs: '100%', md: 'calc(66.666% - 6px)' } }}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      Patient Admissions Trend
                    </Typography>
                    <ResponsiveContainer width="100%" height={300}>
                      <LineChart data={patientData}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="name" />
                        <YAxis />
                        <Tooltip />
                        <Legend />
                        <Line type="monotone" dataKey="patients" stroke="#8884d8" />
                        <Line type="monotone" dataKey="admitted" stroke="#82ca9d" />
                      </LineChart>
                    </ResponsiveContainer>
                  </CardContent>
                </Card>
              </Box>
              <Box sx={{ width: { xs: '100%', md: 'calc(33.333% - 6px)' } }}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      Department Distribution
                    </Typography>
                    <ResponsiveContainer width="100%" height={300}>
                      <PieChart>
                        <Pie
                          data={departmentData}
                          cx="50%"
                          cy="50%"
                          labelLine={false}
                          label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                          outerRadius={80}
                          fill="#8884d8"
                          dataKey="value"
                        >
                          {departmentData.map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={entry.color} />
                          ))}
                        </Pie>
                        <Tooltip />
                      </PieChart>
                    </ResponsiveContainer>
                  </CardContent>
                </Card>
              </Box>
            </Box>
          </Container>
        )}
        {currentTab === 1 && (
          <Container maxWidth="lg">
            <Box sx={{ width: '100%' }}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Department Performance Metrics
                  </Typography>
                  <ResponsiveContainer width="100%" height={400}>
                    <BarChart data={departmentData}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="name" />
                      <YAxis />
                      <Tooltip />
                      <Legend />
                      <Bar dataKey="value" fill="#8884d8" />
                    </BarChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>
            </Box>
          </Container>
        )}
      </Box>
    </Box>
  )
}
export default DashboardModule