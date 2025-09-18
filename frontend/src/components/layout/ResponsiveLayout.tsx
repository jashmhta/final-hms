import React, { useState, useEffect } from 'react'
import {
  Box,
  useTheme,
  useMediaQuery,
  Drawer,
  AppBar,
  Toolbar,
  Typography,
  IconButton,
  Button,
  Avatar,
  Badge,
  Menu,
  MenuItem,
  Divider,
  useScrollTrigger,
  Fab,
  Zoom,
  Tooltip,
  alpha,
} from '@mui/material'
import {
  Menu as MenuIcon,
  ChevronLeft,
  ChevronRight,
  Notifications,
  Search,
  Settings,
  Person,
  Logout,
  Home,
  People,
  CalendarToday,
  LocalHospital,
  Medication,
  Emergency,
  Description,
  Dashboard,
  Assessment,
  Phone,
  Mail,
  KeyboardArrowUp,
} from '@mui/icons-material'
import { Outlet, useLocation, useNavigate } from 'react-router-dom'

interface ResponsiveLayoutProps {
  children?: React.ReactNode
  onThemeToggle: () => void
  currentTheme: 'light' | 'dark' | 'high-contrast'
  user?: {
    name: string
    role: string
    avatar?: string
    notifications: number
  }
}

const drawerWidth = 280
const collapsedDrawerWidth = 72

const menuItems = [
  { title: 'Dashboard', icon: <Dashboard />, path: '/' },
  { title: 'Patients', icon: <People />, path: '/patients' },
  { title: 'Appointments', icon: <CalendarToday />, path: '/appointments' },
  { title: 'Medical Records', icon: <Description />, path: '/records' },
  { title: 'Medications', icon: <Medication />, path: '/medications' },
  { title: 'Vital Signs', icon: <Assessment />, path: '/vitals' },
  { title: 'Emergency', icon: <Emergency />, path: '/emergency' },
  { title: 'Laboratory', icon: <LocalHospital />, path: '/laboratory' },
  { title: 'Messages', icon: <Mail />, path: '/messages' },
  { title: 'Settings', icon: <Settings />, path: '/settings' },
]

const ResponsiveLayout: React.FC<ResponsiveLayoutProps> = ({
  children,
  onThemeToggle,
  currentTheme,
  user = {
    name: 'Dr. Sarah Johnson',
    role: 'Physician',
    notifications: 3,
  },
}) => {
  const theme = useTheme()
  const navigate = useNavigate()
  const location = useLocation()

  // Responsive breakpoints
  const isXs = useMediaQuery(theme.breakpoints.down('xs'))
  const isSm = useMediaQuery(theme.breakpoints.down('sm'))
  const isMd = useMediaQuery(theme.breakpoints.down('md'))
  const isLg = useMediaQuery(theme.breakpoints.down('lg'))

  const [mobileOpen, setMobileOpen] = useState(false)
  const [desktopCollapsed, setDesktopCollapsed] = useState(false)
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null)
  const [notificationAnchor, setNotificationAnchor] = useState<null | HTMLElement>(null)
  const [scrolled, setScrolled] = useState(false)

  // Handle scroll effect for app bar
  const trigger = useScrollTrigger({
    disableHysteresis: true,
    threshold: 100,
  })

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 50)
    }
    window.addEventListener('scroll', handleScroll)
    return () => window.removeEventListener('scroll', handleScroll)
  }, [])

  const handleDrawerToggle = () => {
    setMobileOpen(!mobileOpen)
  }

  const handleDrawerCollapse = () => {
    setDesktopCollapsed(!desktopCollapsed)
  }

  const handleProfileMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget)
  }

  const handleNotificationMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setNotificationAnchor(event.currentTarget)
  }

  const handleMenuClose = () => {
    setAnchorEl(null)
    setNotificationAnchor(null)
  }

  const handleNavigation = (path: string) => {
    navigate(path)
    if (isSm) {
      setMobileOpen(false)
    }
  }

  const scrollToTop = () => {
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  const drawer = (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Logo and Header */}
      <Box sx={{ p: 3, borderBottom: `1px solid ${alpha(theme.palette.divider, 0.5)}` }}>
        <Box display="flex" alignItems="center" justifyContent="space-between">
          <Box display="flex" alignItems="center" gap={2}>
            <Avatar
              sx={{
                width: 40,
                height: 40,
                backgroundColor: theme.palette.primary.main,
              }}
            >
              <LocalHospital />
            </Avatar>
            <Box>
              <Typography variant="h6" fontWeight={600} noWrap>
                HMS
              </Typography>
              <Typography variant="caption" color="textSecondary">
                Healthcare Management
              </Typography>
            </Box>
          </Box>
          {isSm && (
            <IconButton onClick={handleDrawerToggle}>
              <ChevronLeft />
            </IconButton>
          )}
        </Box>
      </Box>

      {/* Navigation Menu */}
      <Box sx={{ flexGrow: 1, overflowY: 'auto', py: 2 }}>
        {menuItems.map((item) => (
          <Button
            key={item.path}
            onClick={() => handleNavigation(item.path)}
            sx={{
              justifyContent: desktopCollapsed ? 'center' : 'flex-start',
              px: desktopCollapsed ? 2 : 3,
              py: 1.5,
              mx: 1,
              mb: 0.5,
              borderRadius: 2,
              backgroundColor: location.pathname === item.path
                ? alpha(theme.palette.primary.main, 0.1)
                : 'transparent',
              color: location.pathname === item.path
                ? theme.palette.primary.main
                : 'text.primary',
              '&:hover': {
                backgroundColor: alpha(theme.palette.primary.main, 0.05),
              },
              transition: 'all 0.2s ease-in-out',
              textTransform: 'none',
              minHeight: 48,
            }}
            startIcon={
              <Box
                sx={{
                  color: location.pathname === item.path
                    ? theme.palette.primary.main
                    : 'text.secondary',
                }}
              >
                {item.icon}
              </Box>
            }
          >
            {!desktopCollapsed && (
              <Typography variant="body2" fontWeight={500}>
                {item.title}
              </Typography>
            )}
          </Button>
        ))}
      </Box>

      {/* User Section */}
      <Box sx={{ p: 2, borderTop: `1px solid ${alpha(theme.palette.divider, 0.5)}` }}>
        <Button
          onClick={handleProfileMenuOpen}
          sx={{
            justifyContent: desktopCollapsed ? 'center' : 'flex-start',
            width: '100%',
            px: 2,
            py: 1.5,
            borderRadius: 2,
            '&:hover': {
              backgroundColor: alpha(theme.palette.primary.main, 0.05),
            },
            textTransform: 'none',
            minHeight: 56,
          }}
          startIcon={
            <Avatar
              src={user.avatar}
              sx={{ width: 32, height: 32 }}
            >
              {user.name.charAt(0)}
            </Avatar>
          }
        >
          {!desktopCollapsed && (
            <Box sx={{ textAlign: 'left', ml: 1 }}>
              <Typography variant="body2" fontWeight={600} noWrap>
                {user.name}
              </Typography>
              <Typography variant="caption" color="textSecondary" noWrap>
                {user.role}
              </Typography>
            </Box>
          )}
        </Button>
      </Box>
    </Box>
  )

  // Mobile AppBar
  const MobileAppBar = () => (
    <AppBar
      position="fixed"
      sx={{
        width: '100%',
        backgroundColor: scrolled
          ? alpha(theme.palette.background.paper, 0.95)
          : theme.palette.background.paper,
        backdropFilter: 'blur(8px)',
        borderBottom: `1px solid ${alpha(theme.palette.divider, 0.2)}`,
        boxShadow: scrolled ? theme.shadows[2] : 'none',
        transition: 'all 0.3s ease-in-out',
        zIndex: theme.zIndex.drawer + 1,
      }}
    >
      <Toolbar>
        <IconButton
          color="inherit"
          aria-label="open drawer"
          edge="start"
          onClick={handleDrawerToggle}
          sx={{ mr: 2 }}
        >
          <MenuIcon />
        </IconButton>

        <Typography variant="h6" noWrap component="div" sx={{ flexGrow: 1 }}>
          HMS Healthcare
        </Typography>

        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Tooltip title="Search">
            <IconButton color="inherit" size="small">
              <Search />
            </IconButton>
          </Tooltip>

          <Tooltip title="Notifications">
            <IconButton
              color="inherit"
              size="small"
              onClick={handleNotificationMenuOpen}
            >
              <Badge badgeContent={user.notifications} color="error">
                <Notifications />
              </Badge>
            </IconButton>
          </Tooltip>

          <Tooltip title="User Menu">
            <IconButton
              color="inherit"
              size="small"
              onClick={handleProfileMenuOpen}
            >
              <Avatar
                src={user.avatar}
                sx={{ width: 32, height: 32 }}
              >
                {user.name.charAt(0)}
              </Avatar>
            </IconButton>
          </Tooltip>
        </Box>
      </Toolbar>
    </AppBar>
  )

  // Desktop Sidebar
  const DesktopSidebar = () => (
    <Box
      component="nav"
      sx={{
        width: desktopCollapsed ? collapsedDrawerWidth : drawerWidth,
        flexShrink: 0,
        position: 'fixed',
        top: 0,
        left: 0,
        height: '100vh',
        backgroundColor: theme.palette.background.paper,
        borderRight: `1px solid ${alpha(theme.palette.divider, 0.2)}`,
        transition: 'width 0.3s ease-in-out',
        zIndex: theme.zIndex.drawer,
      }}
    >
      <Toolbar sx={{ minHeight: 64, borderBottom: `1px solid ${alpha(theme.palette.divider, 0.2)}` }}>
        {!desktopCollapsed && (
          <Box display="flex" alignItems="center" gap={2}>
            <Avatar
              sx={{
                width: 40,
                height: 40,
                backgroundColor: theme.palette.primary.main,
              }}
            >
              <LocalHospital />
            </Avatar>
            <Box>
              <Typography variant="h6" fontWeight={600} noWrap>
                HMS Enterprise
              </Typography>
              <Typography variant="caption" color="textSecondary">
                Healthcare Management
              </Typography>
            </Box>
          </Box>
        )}
        <IconButton onClick={handleDrawerCollapse} sx={{ ml: 'auto' }}>
          {desktopCollapsed ? <ChevronRight /> : <ChevronLeft />}
        </IconButton>
      </Toolbar>

      {drawer}
    </Box>
  )

  // Main Content Area
  const MainContent = () => (
    <Box
      component="main"
      sx={{
        flexGrow: 1,
        minHeight: '100vh',
        backgroundColor: theme.palette.background.default,
        pt: isSm ? 8 : 0, // Account for mobile app bar
        ml: isSm ? 0 : desktopCollapsed ? collapsedDrawerWidth : drawerWidth,
        transition: 'margin-left 0.3s ease-in-out',
      }}
    >
      {/* Top Bar for Desktop */}
      {!isSm && (
        <Box
          sx={{
            position: 'sticky',
            top: 0,
            zIndex: theme.zIndex.appBar,
            backgroundColor: scrolled
              ? alpha(theme.palette.background.paper, 0.95)
              : 'transparent',
            backdropFilter: 'blur(8px)',
            borderBottom: scrolled ? `1px solid ${alpha(theme.palette.divider, 0.2)}` : 'none',
            transition: 'all 0.3s ease-in-out',
          }}
        >
          <Toolbar>
            <Box sx={{ flexGrow: 1 }}>
              <Typography variant="h5" fontWeight={600}>
                {menuItems.find(item => item.path === location.pathname)?.title || 'Dashboard'}
              </Typography>
            </Box>

            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <Tooltip title="Search">
                <IconButton size="small">
                  <Search />
                </IconButton>
              </Tooltip>

              <Tooltip title="Notifications">
                <IconButton
                  size="small"
                  onClick={handleNotificationMenuOpen}
                >
                  <Badge badgeContent={user.notifications} color="error">
                    <Notifications />
                  </Badge>
                </IconButton>
              </Tooltip>

              <Tooltip title="User Menu">
                <IconButton
                  size="small"
                  onClick={handleProfileMenuOpen}
                >
                  <Avatar
                    src={user.avatar}
                    sx={{ width: 36, height: 36 }}
                  >
                    {user.name.charAt(0)}
                  </Avatar>
                </IconButton>
              </Tooltip>
            </Box>
          </Toolbar>
        </Box>
      )}

      {/* Page Content */}
      <Box sx={{ p: { xs: 2, sm: 3, md: 4 } }}>
        {children || <Outlet />}
      </Box>

      {/* Scroll to Top Button */}
      <Zoom in={trigger}>
        <Box
          sx={{
            position: 'fixed',
            bottom: 80,
            right: 20,
            zIndex: theme.zIndex.speedDial,
          }}
        >
          <Tooltip title="Scroll to top">
            <Fab
              size="small"
              onClick={scrollToTop}
              sx={{
                backgroundColor: theme.palette.primary.main,
                color: theme.palette.primary.contrastText,
                '&:hover': {
                  backgroundColor: theme.palette.primary.dark,
                },
              }}
            >
              <KeyboardArrowUp />
            </Fab>
          </Tooltip>
        </Box>
      </Zoom>
    </Box>
  )

  return (
    <Box sx={{ display: 'flex', backgroundColor: theme.palette.background.default }}>
      {/* Mobile App Bar */}
      {isSm && <MobileAppBar />}

      {/* Mobile Drawer */}
      <Drawer
        variant="temporary"
        open={mobileOpen}
        onClose={handleDrawerToggle}
        ModalProps={{
          keepMounted: true, // Better open performance on mobile.
        }}
        sx={{
          display: { xs: 'block', sm: 'none' },
          '& .MuiDrawer-paper': {
            boxSizing: 'border-box',
            width: drawerWidth,
            backgroundColor: theme.palette.background.paper,
          },
        }}
      >
        {drawer}
      </Drawer>

      {/* Desktop Sidebar */}
      {!isSm && <DesktopSidebar />}

      {/* Main Content */}
      <MainContent />

      {/* User Menu */}
      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleMenuClose}
        onClick={handleMenuClose}
        PaperProps={{
          elevation: 0,
          sx: {
            overflow: 'visible',
            filter: 'drop-shadow(0px 2px 8px rgba(0,0,0,0.32))',
            mt: 1.5,
            '& .MuiAvatar-root': {
              width: 32,
              height: 32,
              ml: -0.5,
              mr: 1,
            },
          },
        }}
        transformOrigin={{ horizontal: 'right', vertical: 'top' }}
        anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}
      >
        <MenuItem>
          <Avatar src={user.avatar} />
          <Box>
            <Typography variant="body2" fontWeight={600}>
              {user.name}
            </Typography>
            <Typography variant="caption" color="textSecondary">
              {user.role}
            </Typography>
          </Box>
        </MenuItem>
        <Divider />
        <MenuItem onClick={() => navigate('/profile')}>
          <Person sx={{ mr: 2 }} />
          Profile
        </MenuItem>
        <MenuItem onClick={() => navigate('/settings')}>
          <Settings sx={{ mr: 2 }} />
          Settings
        </MenuItem>
        <MenuItem onClick={onThemeToggle}>
          {currentTheme === 'dark' ? <ChevronRight sx={{ mr: 2 }} /> : <ChevronLeft sx={{ mr: 2 }} />}
          {currentTheme === 'dark' ? 'Light Mode' : 'Dark Mode'}
        </MenuItem>
        <Divider />
        <MenuItem>
          <Logout sx={{ mr: 2 }} />
          Logout
        </MenuItem>
      </Menu>

      {/* Notifications Menu */}
      <Menu
        anchorEl={notificationAnchor}
        open={Boolean(notificationAnchor)}
        onClose={handleMenuClose}
        PaperProps={{
          elevation: 0,
          sx: {
            overflow: 'visible',
            filter: 'drop-shadow(0px 2px 8px rgba(0,0,0,0.32))',
            mt: 1.5,
            width: 360,
            maxHeight: 480,
          },
        }}
        transformOrigin={{ horizontal: 'right', vertical: 'top' }}
        anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}
      >
        <Box sx={{ p: 2 }}>
          <Typography variant="h6" fontWeight={600}>
            Notifications
          </Typography>
        </Box>
        <Divider />
        <MenuItem>
          <Box sx={{ width: '100%' }}>
            <Typography variant="body2" fontWeight={600}>
              New Patient Assigned
            </Typography>
            <Typography variant="caption" color="textSecondary">
              2 minutes ago
            </Typography>
          </Box>
        </MenuItem>
        <MenuItem>
          <Box sx={{ width: '100%' }}>
            <Typography variant="body2" fontWeight={600}>
              Lab Results Available
            </Typography>
            <Typography variant="caption" color="textSecondary">
              15 minutes ago
            </Typography>
          </Box>
        </MenuItem>
        <MenuItem>
          <Box sx={{ width: '100%' }}>
            <Typography variant="body2" fontWeight={600}>
              Appointment Reminder
            </Typography>
            <Typography variant="caption" color="textSecondary">
              1 hour ago
            </Typography>
          </Box>
        </MenuItem>
        <Divider />
        <MenuItem sx={{ justifyContent: 'center' }}>
          <Typography variant="body2" color="primary">
            View All Notifications
          </Typography>
        </MenuItem>
      </Menu>
    </Box>
  )
}

export default ResponsiveLayout