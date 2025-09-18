import { createTheme } from '@mui/material/styles'
import { alpha } from '@mui/material/styles'

// Healthcare Color Palette
const healthcareColors = {
  // Primary - Medical Blue
  primary: {
    main: '#0066CC',
    light: '#4D94FF',
    dark: '#004C99',
    contrastText: '#FFFFFF',
  },
  // Secondary - Healing Green
  secondary: {
    main: '#00A86B',
    light: '#4DD4A6',
    dark: '#007A4F',
    contrastText: '#FFFFFF',
  },
  // Emergency Red
  error: {
    main: '#DC2626',
    light: '#EF4444',
    dark: '#B91C1C',
    contrastText: '#FFFFFF',
  },
  // Warning Amber
  warning: {
    main: '#F59E0B',
    light: '#FCD34D',
    dark: '#D97706',
    contrastText: '#1F2937',
  },
  // Success Green
  success: {
    main: '#10B981',
    light: '#34D399',
    dark: '#059669',
    contrastText: '#FFFFFF',
  },
  // Info Blue
  info: {
    main: '#3B82F6',
    light: '#60A5FA',
    dark: '#2563EB',
    contrastText: '#FFFFFF',
  },
  // Clinical Colors
  clinical: {
    emergency: '#DC2626',      // Emergency - Red
    critical: '#F59E0B',       // Critical - Amber
    urgent: '#EF4444',         // Urgent - Red-500
    priority: '#8B5CF6',       // Priority - Purple
    normal: '#10B981',         // Normal - Green
    low: '#6B7280',           // Low - Gray
  },
  // Department Colors
  departments: {
    emergency: '#DC2626',     // Emergency Department
    icu: '#8B5CF6',          // Intensive Care Unit
    surgery: '#EC4899',       // Surgery
    pediatrics: '#06B6D4',    // Pediatrics
    cardiology: '#EF4444',    // Cardiology
    neurology: '#8B5CF6',    // Neurology
    orthopedics: '#F59E0B',   // Orthopedics
    oncology: '#DC2626',      // Oncology
    radiology: '#3B82F6',     // Radiology
    laboratory: '#10B981',   // Laboratory
    pharmacy: '#84CC16',     // Pharmacy
    general: '#6B7280',      // General Medicine
  },
  // Neutral Palette
  grey: {
    50: '#F8FAFC',
    100: '#F1F5F9',
    200: '#E2E8F0',
    300: '#CBD5E1',
    400: '#94A3B8',
    500: '#64748B',
    600: '#475569',
    700: '#334155',
    800: '#1E293B',
    900: '#0F172A',
  },
  // Status Colors
  status: {
    online: '#10B981',
    offline: '#6B7280',
    busy: '#F59E0B',
    away: '#8B5CF6',
    emergency: '#DC2626',
  },
  // Background Colors
  background: {
    default: '#F8FAFC',
    paper: '#FFFFFF',
    app: '#F1F5F9',
    clinical: '#F0F9FF',
    emergency: '#FEF2F2',
  },
  // Text Colors
  text: {
    primary: '#0F172A',
    secondary: '#475569',
    disabled: '#94A3B8',
    hint: '#64748B',
    clinical: '#1E293B',
    emergency: '#7F1D1D',
  },
}

// Healthcare Typography
const healthcareTypography = {
  fontFamily: [
    'Inter',
    '-apple-system',
    'BlinkMacSystemFont',
    '"Segoe UI"',
    'Roboto',
    '"Helvetica Neue"',
    'Arial',
    'sans-serif',
  ].join(','),
  fontFamilyMono: [
    'Roboto Mono',
    'ui-monospace',
    'SFMono-Regular',
    'Menlo',
    'Monaco',
    'Consolas',
    '"Liberation Mono"',
    '"Courier New"',
    'monospace',
  ].join(','),
  fontFamilyDisplay: [
    'Manrope',
    'Inter',
    '-apple-system',
    'BlinkMacSystemFont',
    '"Segoe UI"',
    'Roboto',
    'sans-serif',
  ].join(','),

  fontSize: 14,
  htmlFontSize: 16,

  // Responsive typography scale
  h1: {
    fontSize: '2.5rem',
    fontWeight: 700,
    lineHeight: 1.2,
    '@media (max-width: 768px)': {
      fontSize: '2rem',
    },
    '@media (max-width: 480px)': {
      fontSize: '1.75rem',
    },
  },
  h2: {
    fontSize: '2rem',
    fontWeight: 600,
    lineHeight: 1.3,
    '@media (max-width: 768px)': {
      fontSize: '1.75rem',
    },
    '@media (max-width: 480px)': {
      fontSize: '1.5rem',
    },
  },
  h3: {
    fontSize: '1.5rem',
    fontWeight: 600,
    lineHeight: 1.4,
    '@media (max-width: 768px)': {
      fontSize: '1.375rem',
    },
    '@media (max-width: 480px)': {
      fontSize: '1.25rem',
    },
  },
  h4: {
    fontSize: '1.25rem',
    fontWeight: 600,
    lineHeight: 1.4,
    '@media (max-width: 768px)': {
      fontSize: '1.125rem',
    },
  },
  h5: {
    fontSize: '1rem',
    fontWeight: 600,
    lineHeight: 1.5,
  },
  h6: {
    fontSize: '0.875rem',
    fontWeight: 600,
    lineHeight: 1.5,
  },
  subtitle1: {
    fontSize: '1rem',
    fontWeight: 500,
    lineHeight: 1.5,
  },
  subtitle2: {
    fontSize: '0.875rem',
    fontWeight: 500,
    lineHeight: 1.5,
  },
  body1: {
    fontSize: '1rem',
    fontWeight: 400,
    lineHeight: 1.6,
  },
  body2: {
    fontSize: '0.875rem',
    fontWeight: 400,
    lineHeight: 1.5,
  },
  button: {
    fontSize: '0.875rem',
    fontWeight: 500,
    lineHeight: 1.25,
    textTransform: 'none',
  },
  caption: {
    fontSize: '0.75rem',
    fontWeight: 400,
    lineHeight: 1.5,
  },
  overline: {
    fontSize: '0.75rem',
    fontWeight: 500,
    lineHeight: 1.5,
    textTransform: 'uppercase',
    letterSpacing: '0.1em',
  },
}

// Healthcare Spacing System
const healthcareSpacing = {
  unit: 4,
  px: '1px',
  0: 0,
  0.5: 2,
  1: 4,
  1.5: 6,
  2: 8,
  2.5: 10,
  3: 12,
  3.5: 14,
  4: 16,
  5: 20,
  6: 24,
  7: 28,
  8: 32,
  9: 36,
  10: 40,
  11: 44,
  12: 48,
  14: 56,
  16: 64,
  20: 80,
  24: 96,
  28: 112,
  32: 128,
  36: 144,
  40: 160,
  44: 176,
  48: 192,
  52: 208,
  56: 224,
  60: 240,
  64: 256,
  72: 288,
  80: 320,
  96: 384,
}

// Healthcare Shape System
const healthcareShape = {
  borderRadius: 8,
  borderRadiusSmall: 4,
  borderRadiusMedium: 8,
  borderRadiusLarge: 12,
  borderRadiusExtraLarge: 16,
  borderRadiusFull: 9999,
}

// Healthcare Shadows
const healthcareShadows = [
  'none',
  '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
  '0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)',
  '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
  '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
  '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
  '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
  '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
]

// Healthcare Z-Index System
const healthcareZIndex = {
  mobileStepper: 1000,
  speedDial: 1050,
  appBar: 1100,
  drawer: 1200,
  modal: 1300,
  snackbar: 1400,
  tooltip: 1500,
  emergency: 9999,
  criticalAlert: 8888,
  priority: 7000,
}

// Create Healthcare Theme
const healthcareTheme = createTheme({
  palette: {
    ...healthcareColors,
    mode: 'light',
    contrastThreshold: 3,
    tonalOffset: 0.2,
    divider: alpha(healthcareColors.grey[300], 0.5),
    background: {
      default: healthcareColors.background.default,
      paper: healthcareColors.background.paper,
    },
    text: {
      primary: healthcareColors.text.primary,
      secondary: healthcareColors.text.secondary,
      disabled: healthcareColors.text.disabled,
    },
    action: {
      active: healthcareColors.primary.main,
      hover: alpha(healthcareColors.primary.main, 0.04),
      hoverOpacity: 0.04,
      selected: alpha(healthcareColors.primary.main, 0.08),
      selectedOpacity: 0.08,
      disabled: alpha(healthcareColors.text.disabled, 0.38),
      disabledBackground: alpha(healthcareColors.text.disabled, 0.12),
      disabledOpacity: 0.38,
      focus: alpha(healthcareColors.primary.main, 0.12),
      focusOpacity: 0.12,
      activatedOpacity: 0.12,
    },
  },
  typography: healthcareTypography,
  spacing: healthcareSpacing,
  shape: healthcareShape,
  shadows: healthcareShadows,
  zIndex: healthcareZIndex,

  // Component Overrides
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: healthcareShape.borderRadiusMedium,
          textTransform: 'none',
          fontWeight: 500,
          boxShadow: 'none',
          '&:hover': {
            boxShadow: 'none',
          },
        },
        contained: {
          boxShadow: healthcareShadows[2],
          '&:hover': {
            boxShadow: healthcareShadows[4],
          },
        },
        sizeLarge: {
          padding: `${healthcareSpacing[3]}px ${healthcareSpacing[6]}px`,
          fontSize: '1rem',
        },
        sizeSmall: {
          padding: `${healthcareSpacing[2]}px ${healthcareSpacing[4]}px`,
          fontSize: '0.875rem',
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: healthcareShape.borderRadiusLarge,
          boxShadow: healthcareShadows[1],
          border: `1px solid ${alpha(healthcareColors.grey[200], 0.5)}`,
          transition: 'all 0.2s ease-in-out',
          '&:hover': {
            boxShadow: healthcareShadows[3],
          },
        },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: {
          borderRadius: healthcareShape.borderRadiusFull,
          fontWeight: 500,
        },
      },
    },
    MuiAlert: {
      styleOverrides: {
        root: {
          borderRadius: healthcareShape.borderRadiusMedium,
          border: `1px solid ${alpha(healthcareColors.grey[200], 0.5)}`,
        },
        standardError: {
          backgroundColor: alpha(healthcareColors.error.main, 0.1),
          border: `1px solid ${alpha(healthcareColors.error.main, 0.3)}`,
          color: healthcareColors.error.dark,
        },
        standardWarning: {
          backgroundColor: alpha(healthcareColors.warning.main, 0.1),
          border: `1px solid ${alpha(healthcareColors.warning.main, 0.3)}`,
          color: healthcareColors.warning.dark,
        },
        standardSuccess: {
          backgroundColor: alpha(healthcareColors.success.main, 0.1),
          border: `1px solid ${alpha(healthcareColors.success.main, 0.3)}`,
          color: healthcareColors.success.dark,
        },
        standardInfo: {
          backgroundColor: alpha(healthcareColors.info.main, 0.1),
          border: `1px solid ${alpha(healthcareColors.info.main, 0.3)}`,
          color: healthcareColors.info.dark,
        },
      },
    },
    MuiDrawer: {
      styleOverrides: {
        paper: {
          borderRight: `1px solid ${alpha(healthcareColors.grey[200], 0.5)}`,
        },
      },
    },
    MuiAppBar: {
      styleOverrides: {
        root: {
          backgroundImage: 'none',
          boxShadow: healthcareShadows[2],
          borderBottom: `1px solid ${alpha(healthcareColors.grey[200], 0.5)}`,
        },
      },
    },
    MuiTableCell: {
      styleOverrides: {
        root: {
          borderBottom: `1px solid ${alpha(healthcareColors.grey[200], 0.5)}`,
        },
        head: {
          fontWeight: 600,
          color: healthcareColors.text.primary,
          backgroundColor: alpha(healthcareColors.grey[100], 0.5),
        },
      },
    },
    MuiInputBase: {
      styleOverrides: {
        root: {
          borderRadius: healthcareShape.borderRadiusMedium,
        },
      },
    },
    MuiOutlinedInput: {
      styleOverrides: {
        root: {
          '&:hover .MuiOutlinedInput-notchedOutline': {
            borderColor: healthcareColors.primary.light,
          },
          '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
            borderColor: healthcareColors.primary.main,
          },
        },
      },
    },
    MuiTab: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          fontWeight: 500,
          minWidth: 'auto',
          padding: `${healthcareSpacing[3]}px ${healthcareSpacing[4]}px`,
          '&.Mui-selected': {
            fontWeight: 600,
          },
        },
      },
    },
  },

  // Custom breakpoints for healthcare devices
  breakpoints: {
    values: {
      xs: 0,
      sm: 600,
      md: 900,
      lg: 1200,
      xl: 1536,
    },
  },
})

// Dark theme variant
const healthcareDarkTheme = createTheme({
  ...healthcareTheme,
  palette: {
    ...healthcareTheme.palette,
    mode: 'dark',
    background: {
      default: '#0F172A',
      paper: '#1E293B',
      app: '#0F172A',
      clinical: '#0C1E3D',
      emergency: '#1A0F0F',
    },
    text: {
      primary: '#F8FAFC',
      secondary: '#CBD5E1',
      disabled: '#64748B',
      hint: '#94A3B8',
      clinical: '#F1F5F9',
      emergency: '#FEE2E2',
    },
    divider: alpha(healthcareColors.grey[600], 0.3),
    action: {
      ...healthcareTheme.palette.action,
      hover: alpha(healthcareColors.primary.main, 0.08),
      selected: alpha(healthcareColors.primary.main, 0.16),
    },
  },
})

// High contrast theme for accessibility
const healthcareHighContrastTheme = createTheme({
  ...healthcareTheme,
  palette: {
    ...healthcareTheme.palette,
    primary: {
      main: '#0047AB',
      light: '#0066CC',
      dark: '#002266',
      contrastText: '#FFFFFF',
    },
    background: {
      default: '#000000',
      paper: '#FFFFFF',
    },
    text: {
      primary: '#000000',
      secondary: '#333333',
      disabled: '#666666',
    },
    contrastThreshold: 7,
  },
})

export {
  healthcareTheme,
  healthcareDarkTheme,
  healthcareHighContrastTheme,
  healthcareColors,
  healthcareTypography,
  healthcareSpacing,
  healthcareShape,
  healthcareShadows,
  healthcareZIndex,
}

export default healthcareTheme