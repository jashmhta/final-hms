import React, { useEffect, useState, useCallback } from 'react'
import {
  Box,
  Button,
  IconButton,
  Tooltip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  FormControlLabel,
  Switch,
  Slider,
  Typography,
  Paper,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Alert,
  useTheme,
  Grid,
} from '@mui/material'
import {
  Accessibility,
  AccessibilityNew,
  TextFields,
  TextIncrease,
  TextDecrease,
  Contrast,
  ZoomIn,
  ZoomOut,
  VolumeUp,
  VolumeOff,
  Keyboard,
  Visibility,
  ColorLens,
  DarkMode,
  LightMode,
} from '@mui/icons-material'

interface AccessibilitySettings {
  fontSize: number
  lineHeight: number
  letterSpacing: number
  highContrast: boolean
  darkMode: boolean
  reduceMotion: boolean
  screenReader: boolean
  keyboardNavigation: boolean
  colorBlind: 'none' | 'protanopia' | 'deuteranopia' | 'tritanopia' | 'achromatopsia'
  focusVisible: boolean
  largeText: boolean
  dyslexiaFont: boolean
  audioCues: boolean
  simplifiedInterface: boolean
  skipLinks: boolean
  ariaLabels: boolean
}

interface AccessibilityWrapperProps {
  children: React.ReactNode
  onSettingsChange: (settings: AccessibilitySettings) => void
  className?: string
}

const AccessibilityWrapper: React.FC<AccessibilityWrapperProps> = ({
  children,
  onSettingsChange,
  className,
}) => {
  const theme = useTheme()
  const [settings, setSettings] = useState<AccessibilitySettings>({
    fontSize: 16,
    lineHeight: 1.5,
    letterSpacing: 0,
    highContrast: false,
    darkMode: false,
    reduceMotion: false,
    screenReader: false,
    keyboardNavigation: true,
    colorBlind: 'none',
    focusVisible: true,
    largeText: false,
    dyslexiaFont: false,
    audioCues: false,
    simplifiedInterface: false,
    skipLinks: true,
    ariaLabels: true,
  })

  const [isOpen, setIsOpen] = useState(false)
  const [showHelp, setShowHelp] = useState(false)

  const updateSettings = useCallback((newSettings: Partial<AccessibilitySettings>) => {
    const updatedSettings = { ...settings, ...newSettings }
    setSettings(updatedSettings)
    onSettingsChange(updatedSettings)
    localStorage.setItem('accessibilitySettings', JSON.stringify(updatedSettings))
  }, [settings, onSettingsChange])

  const loadSettings = useCallback(() => {
    try {
      const saved = localStorage.getItem('accessibilitySettings')
      if (saved) {
        const parsed = JSON.parse(saved)
        setSettings(parsed)
        onSettingsChange(parsed)
      }
    } catch (error) {
      console.error('Error loading accessibility settings:', error)
    }
  }, [onSettingsChange])

  useEffect(() => {
    loadSettings()
  }, [loadSettings])

  useEffect(() => {
    // Apply CSS custom properties for global styling
    const root = document.documentElement

    root.style.setProperty('--accessibility-font-size', `${settings.fontSize}px`)
    root.style.setProperty('--accessibility-line-height', settings.lineHeight.toString())
    root.style.setProperty('--accessibility-letter-spacing', `${settings.letterSpacing}px`)

    // Apply high contrast mode
    if (settings.highContrast) {
      root.classList.add('high-contrast')
    } else {
      root.classList.remove('high-contrast')
    }

    // Apply reduced motion
    if (settings.reduceMotion) {
      root.style.setProperty('--transition-speed', '0s')
      root.classList.add('reduce-motion')
    } else {
      root.style.setProperty('--transition-speed', '0.2s')
      root.classList.remove('reduce-motion')
    }

    // Apply color blind filters
    if (settings.colorBlind !== 'none') {
      root.style.setProperty('--color-blind-filter', `url(#${settings.colorBlind}-filter)`)
    } else {
      root.style.setProperty('--color-blind-filter', 'none')
    }

    // Apply dyslexia font
    if (settings.dyslexiaFont) {
      root.style.setProperty('--font-family', 'OpenDyslexic, sans-serif')
    } else {
      root.style.setProperty('--font-family', 'Inter, sans-serif')
    }

    // Add keyboard navigation support
    if (settings.keyboardNavigation) {
      root.classList.add('keyboard-navigation')
    } else {
      root.classList.remove('keyboard-navigation')
    }

    // Focus visible
    if (settings.focusVisible) {
      root.classList.add('focus-visible')
    } else {
      root.classList.remove('focus-visible')
    }

  }, [settings])

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      // Alt + Shift + A - Open accessibility menu
      if (event.altKey && event.shiftKey && event.key === 'A') {
        event.preventDefault()
        setIsOpen(true)
      }

      // Alt + Shift + H - Show help
      if (event.altKey && event.shiftKey && event.key === 'H') {
        event.preventDefault()
        setShowHelp(true)
      }

      // Alt + Shift + C - Toggle high contrast
      if (event.altKey && event.shiftKey && event.key === 'C') {
        event.preventDefault()
        updateSettings({ highContrast: !settings.highContrast })
      }

      // Alt + Shift + D - Toggle dark mode
      if (event.altKey && event.shiftKey && event.key === 'D') {
        event.preventDefault()
        updateSettings({ darkMode: !settings.darkMode })
      }

      // Alt + Shift + R - Toggle reduced motion
      if (event.altKey && event.shiftKey && event.key === 'R') {
        event.preventDefault()
        updateSettings({ reduceMotion: !settings.reduceMotion })
      }
    }

    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [settings, updateSettings])

  const SkipLinks: React.FC = () => {
    if (!settings.skipLinks) return null

    return (
      <Box
        sx={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          zIndex: theme.zIndex.drawer + 1,
          backgroundColor: theme.palette.background.paper,
          boxShadow: theme.shadows[4],
          '&:not(:focus-within)': {
            transform: 'translateY(-100%)',
          },
          transition: 'transform 0.3s ease-in-out',
        }}
      >
        <Box sx={{ p: 1, display: 'flex', gap: 1 }}>
          <Button
            variant="text"
            onClick={() => document.querySelector('main')?.focus()}
            sx={{ textDecoration: 'underline' }}
          >
            Skip to main content
          </Button>
          <Button
            variant="text"
            onClick={() => document.querySelector('nav')?.focus()}
            sx={{ textDecoration: 'underline' }}
          >
            Skip to navigation
          </Button>
          <Button
            variant="text"
            onClick={() => document.querySelector('footer')?.focus()}
            sx={{ textDecoration: 'underline' }}
          >
            Skip to footer
          </Button>
        </Box>
      </Box>
    )
  }

  const AccessibilityButton: React.FC = () => (
    <Tooltip title="Accessibility Options (Alt+Shift+A)">
      <IconButton
        onClick={() => setIsOpen(true)}
        sx={{
          position: 'fixed',
          bottom: 20,
          right: 20,
          zIndex: theme.zIndex.drawer + 1,
          backgroundColor: theme.palette.primary.main,
          color: theme.palette.primary.contrastText,
          '&:hover': {
            backgroundColor: theme.palette.primary.dark,
          },
          boxShadow: theme.shadows[4],
        }}
        aria-label="Accessibility options"
      >
        <AccessibilityNew />
      </IconButton>
    </Tooltip>
  )

  const AuralAnnouncer: React.FC = () => {
    const [announcement, setAnnouncement] = useState<string>('')

    const announce = useCallback((message: string) => {
      if (settings.audioCues) {
        setAnnouncement(message)
        setTimeout(() => setAnnouncement(''), 1000)
      }
    }, [settings.audioCues])

    useEffect(() => {
      // Announce page changes
      announce('Accessibility options opened')
    }, [announce])

    return (
      <div
        aria-live="polite"
        aria-atomic="true"
        style={{
          position: 'absolute',
          left: '-10000px',
          width: '1px',
          height: '1px',
          overflow: 'hidden',
        }}
      >
        {announcement}
      </div>
    )
  }

  return (
    <Box className={className} sx={{ position: 'relative' }}>
      <SkipLinks />
      <AccessibilityButton />
      <AuralAnnouncer />

      {/* Global styles for accessibility */}
      <style>{`
        :root {
          --accessibility-font-size: 16px;
          --accessibility-line-height: 1.5;
          --accessibility-letter-spacing: 0px;
          --transition-speed: 0.2s;
          --color-blind-filter: none;
          --font-family: 'Inter', sans-serif;
        }

        body {
          font-size: var(--accessibility-font-size);
          line-height: var(--accessibility-line-height);
          letter-spacing: var(--accessibility-letter-spacing);
          font-family: var(--font-family);
        }

        .high-contrast {
          --primary-color: #000000;
          --secondary-color: #ffffff;
          --background-color: #ffffff;
          --text-color: #000000;
          --border-color: #000000;
        }

        .reduce-motion * {
          animation-duration: 0.01ms !important;
          animation-iteration-count: 1 !important;
          transition-duration: 0.01ms !important;
          scroll-behavior: auto !important;
        }

        .keyboard-navigation *:focus {
          outline: 3px solid ${theme.palette.primary.main};
          outline-offset: 2px;
        }

        .focus-visible *:focus-visible {
          outline: 3px solid ${theme.palette.primary.main};
          outline-offset: 2px;
        }

        .simplified-interface {
          --complex-ui-opacity: 0.3;
        }

        .simplified-interface .complex-ui {
          opacity: var(--complex-ui-opacity);
        }

        /* Color blind filters */
        .color-blind-filters {
          display: none;
        }
      `}</style>

      {/* SVG filters for color blindness */}
      <svg className="color-blind-filters">
        <defs>
          <filter id="protanopia-filter">
            <feColorMatrix
              type="matrix"
              values="0.567, 0.433, 0, 0, 0
                       0.558, 0.442, 0, 0, 0
                       0, 0.242, 0.758, 0, 0
                       0, 0, 0, 1, 0"
            />
          </filter>
          <filter id="deuteranopia-filter">
            <feColorMatrix
              type="matrix"
              values="0.625, 0.375, 0, 0, 0
                       0.7, 0.3, 0, 0, 0
                       0, 0.3, 0.7, 0, 0
                       0, 0, 0, 1, 0"
            />
          </filter>
          <filter id="tritanopia-filter">
            <feColorMatrix
              type="matrix"
              values="0.95, 0.05, 0, 0, 0
                       0, 0.433, 0.567, 0, 0
                       0, 0.475, 0.525, 0, 0
                       0, 0, 0, 1, 0"
            />
          </filter>
          <filter id="achromatopsia-filter">
            <feColorMatrix
              type="matrix"
              values="0.299, 0.587, 0.114, 0, 0
                       0.299, 0.587, 0.114, 0, 0
                       0.299, 0.587, 0.114, 0, 0
                       0, 0, 0, 1, 0"
            />
          </filter>
        </defs>
      </svg>

      {/* Main content */}
      <Box
        sx={{
          filter: 'var(--color-blind-filter)',
          transition: 'all var(--transition-speed) ease-in-out',
        }}
      >
        {children}
      </Box>

      {/* Settings Dialog */}
      <Dialog
        open={isOpen}
        onClose={() => setIsOpen(false)}
        maxWidth="md"
        fullWidth
        PaperProps={{
          sx: {
            maxHeight: '90vh',
          },
        }}
      >
        <DialogTitle>
          <Box display="flex" alignItems="center" gap={2}>
            <AccessibilityNew />
            <Typography variant="h6">
              Accessibility Settings
            </Typography>
          </Box>
        </DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
            {/* Text Settings */}
            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" fontWeight={600} mb={2}>
                <TextFields sx={{ mr: 1 }} />
                Text Settings
              </Typography>
              <Grid container spacing={3}>
                <Grid item xs={12}>
                  <Box display="flex" alignItems="center" gap={2}>
                    <Typography variant="body2">Font Size:</Typography>
                    <Slider
                      value={settings.fontSize}
                      onChange={(_, value) => updateSettings({ fontSize: value as number })}
                      min={12}
                      max={24}
                      marks={[
                        { value: 12, label: '12px' },
                        { value: 16, label: '16px' },
                        { value: 20, label: '20px' },
                        { value: 24, label: '24px' },
                      ]}
                      sx={{ flexGrow: 1 }}
                    />
                    <Typography variant="body2">{settings.fontSize}px</Typography>
                  </Box>
                </Grid>
                <Grid item xs={12}>
                  <Box display="flex" alignItems="center" gap={2}>
                    <Typography variant="body2">Line Height:</Typography>
                    <Slider
                      value={settings.lineHeight}
                      onChange={(_, value) => updateSettings({ lineHeight: value as number })}
                      min={1}
                      max={2}
                      step={0.1}
                      marks={[
                        { value: 1, label: '1.0' },
                        { value: 1.5, label: '1.5' },
                        { value: 2, label: '2.0' },
                      ]}
                      sx={{ flexGrow: 1 }}
                    />
                    <Typography variant="body2">{settings.lineHeight}</Typography>
                  </Box>
                </Grid>
                <Grid item xs={12}>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={settings.dyslexiaFont}
                        onChange={(e) => updateSettings({ dyslexiaFont: e.target.checked })}
                      />
                    }
                    label="Use Dyslexia-Friendly Font"
                  />
                </Grid>
                <Grid item xs={12}>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={settings.largeText}
                        onChange={(e) => updateSettings({ largeText: e.target.checked })}
                      />
                    }
                    label="Large Text Mode"
                  />
                </Grid>
              </Grid>
            </Paper>

            {/* Visual Settings */}
            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" fontWeight={600} mb={2}>
                <Contrast sx={{ mr: 1 }} />
                Visual Settings
              </Typography>
              <Grid container spacing={2}>
                <Grid item xs={12} sm={6}>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={settings.highContrast}
                        onChange={(e) => updateSettings({ highContrast: e.target.checked })}
                      />
                    }
                    label="High Contrast Mode"
                  />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={settings.darkMode}
                        onChange={(e) => updateSettings({ darkMode: e.target.checked })}
                      />
                    }
                    label="Dark Mode"
                  />
                </Grid>
                <Grid item xs={12}>
                  <FormControl fullWidth>
                    <InputLabel>Color Vision</InputLabel>
                    <Select
                      value={settings.colorBlind}
                      onChange={(e) => updateSettings({ colorBlind: e.target.value as any })}
                    >
                      <MenuItem value="none">Normal</MenuItem>
                      <MenuItem value="protanopia">Protanopia (Red-blind)</MenuItem>
                      <MenuItem value="deuteranopia">Deuteranopia (Green-blind)</MenuItem>
                      <MenuItem value="tritanopia">Tritanopia (Blue-blind)</MenuItem>
                      <MenuItem value="achromatopsia">Achromatopsia (Color-blind)</MenuItem>
                    </Select>
                  </FormControl>
                </Grid>
                <Grid item xs={12}>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={settings.reduceMotion}
                        onChange={(e) => updateSettings({ reduceMotion: e.target.checked })}
                      />
                    }
                    label="Reduce Motion"
                  />
                </Grid>
              </Grid>
            </Paper>

            {/* Navigation Settings */}
            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" fontWeight={600} mb={2}>
                <Keyboard sx={{ mr: 1 }} />
                Navigation Settings
              </Typography>
              <Grid container spacing={2}>
                <Grid item xs={12} sm={6}>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={settings.keyboardNavigation}
                        onChange={(e) => updateSettings({ keyboardNavigation: e.target.checked })}
                      />
                    }
                    label="Keyboard Navigation"
                  />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={settings.skipLinks}
                        onChange={(e) => updateSettings({ skipLinks: e.target.checked })}
                      />
                    }
                    label="Show Skip Links"
                  />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={settings.focusVisible}
                        onChange={(e) => updateSettings({ focusVisible: e.target.checked })}
                      />
                    }
                    label="Focus Indicators"
                  />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={settings.simplifiedInterface}
                        onChange={(e) => updateSettings({ simplifiedInterface: e.target.checked })}
                      />
                    }
                    label="Simplified Interface"
                  />
                </Grid>
              </Grid>
            </Paper>

            {/* Screen Reader Settings */}
            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" fontWeight={600} mb={2}>
                <VolumeUp sx={{ mr: 1 }} />
                Screen Reader Settings
              </Typography>
              <Grid container spacing={2}>
                <Grid item xs={12}>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={settings.screenReader}
                        onChange={(e) => updateSettings({ screenReader: e.target.checked })}
                      />
                    }
                    label="Screen Reader Optimized"
                  />
                </Grid>
                <Grid item xs={12}>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={settings.ariaLabels}
                        onChange={(e) => updateSettings({ ariaLabels: e.target.checked })}
                      />
                    }
                    label="Enhanced ARIA Labels"
                  />
                </Grid>
                <Grid item xs={12}>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={settings.audioCues}
                        onChange={(e) => updateSettings({ audioCues: e.target.checked })}
                      />
                    }
                    label="Audio Cues"
                  />
                </Grid>
              </Grid>
            </Paper>
          </Box>

          <Alert severity="info" sx={{ mt: 2 }}>
            <Typography variant="body2">
              <strong>Keyboard Shortcuts:</strong>
              <br />
              Alt+Shift+A: Open accessibility settings
              <br />
              Alt+Shift+C: Toggle high contrast
              <br />
              Alt+Shift+D: Toggle dark mode
              <br />
              Alt+Shift+R: Toggle reduced motion
              <br />
              Alt+Shift+H: Show help
            </Typography>
          </Alert>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setIsOpen(false)}>Close</Button>
          <Button
            onClick={() => {
              setSettings({
                fontSize: 16,
                lineHeight: 1.5,
                letterSpacing: 0,
                highContrast: false,
                darkMode: false,
                reduceMotion: false,
                screenReader: false,
                keyboardNavigation: true,
                colorBlind: 'none',
                focusVisible: true,
                largeText: false,
                dyslexiaFont: false,
                audioCues: false,
                simplifiedInterface: false,
                skipLinks: true,
                ariaLabels: true,
              })
              localStorage.removeItem('accessibilitySettings')
            }}
            variant="outlined"
          >
            Reset to Default
          </Button>
        </DialogActions>
      </Dialog>

      {/* Help Dialog */}
      <Dialog
        open={showHelp}
        onClose={() => setShowHelp(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Accessibility Help</DialogTitle>
        <DialogContent>
          <Typography variant="body2" paragraph>
            This healthcare management system is designed to be accessible to all users, including those with disabilities.
          </Typography>

          <Typography variant="h6" fontWeight={600} gutterBottom>
            Navigation
          </Typography>
          <Typography variant="body2" paragraph>
            • Use the Tab key to navigate between interactive elements
            <br />
            • Use Shift+Tab to navigate backwards
            <br />
            • Use Enter or Space to activate buttons and links
            <br />
            • Use arrow keys for navigation within menus and lists
          </Typography>

          <Typography variant="h6" fontWeight={600} gutterBottom>
            Screen Reader Support
          </Typography>
          <Typography variant="body2" paragraph>
            • All interactive elements have proper ARIA labels
            <br />
            • Form fields have associated labels
            <br />
            • Error messages are announced to screen readers
            <br />
            • Live regions provide dynamic content updates
          </Typography>

          <Typography variant="h6" fontWeight={600} gutterBottom>
            Keyboard Shortcuts
          </Typography>
          <Typography variant="body2" paragraph>
            • Alt+Shift+A: Open accessibility settings
            <br />
            • Alt+Shift+C: Toggle high contrast mode
            <br />
            • Alt+Shift+D: Toggle dark mode
            <br />
            • Alt+Shift+R: Toggle reduced motion
            <br />
            • Alt+Shift+H: Show this help
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowHelp(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}

export default AccessibilityWrapper