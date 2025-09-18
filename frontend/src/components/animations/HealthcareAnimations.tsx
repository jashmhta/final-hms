import React, { createContext, useContext, useCallback, useMemo } from 'react'
import { motion, AnimatePresence, MotionConfig } from 'framer-motion'
import {
  Box,
  useTheme,
  alpha,
  SxProps,
  Theme,
  Typography,
  Button,
} from '@mui/material'
import { styled } from '@mui/material/styles'

// Animation context
interface AnimationContextType {
  pulse: (key: string) => void
  slideIn: (direction: 'left' | 'right' | 'up' | 'down') => any
  fadeIn: (delay?: number) => any
  scaleIn: (delay?: number) => any
  stagger: (staggerChildren?: number, delayChildren?: number) => any
  healthcareSpecific: {
    vitalSignPulse: (isCritical?: boolean) => any
    medicationReminder: () => any
    emergencyAlert: () => any
    patientStatusChange: (from: string, to: string) => any
    appointmentScheduling: () => any
    labResultAnimation: () => any
    medicalRecordTransition: () => any
  }
}

const AnimationContext = createContext<AnimationContextType>({
  pulse: () => ({}),
  slideIn: () => ({}),
  fadeIn: () => ({}),
  scaleIn: () => ({}),
  stagger: () => ({}),
  healthcareSpecific: {
    vitalSignPulse: () => ({}),
    medicationReminder: () => ({}),
    emergencyAlert: () => ({}),
    patientStatusChange: () => ({}),
    appointmentScheduling: () => ({}),
    labResultAnimation: () => ({}),
    medicalRecordTransition: () => ({}),
  },
})

// Provider component
export const AnimationProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const pulse = useCallback((key: string) => ({
    initial: { scale: 1 },
    animate: { scale: [1, 1.05, 1] },
    transition: {
      duration: 0.6,
      repeat: Infinity,
      repeatType: 'reverse' as const,
      key,
    },
  }), [])

  const slideIn = useCallback((direction: 'left' | 'right' | 'up' | 'down') => {
    const directions = {
      left: { x: -100, opacity: 0 },
      right: { x: 100, opacity: 0 },
      up: { y: -100, opacity: 0 },
      down: { y: 100, opacity: 0 },
    }
    return {
      initial: directions[direction],
      animate: { x: 0, y: 0, opacity: 1 },
      transition: { duration: 0.5, ease: 'easeOut' },
    }
  }, [])

  const fadeIn = useCallback((delay = 0) => ({
    initial: { opacity: 0 },
    animate: { opacity: 1 },
    transition: { duration: 0.5, delay },
  }), [])

  const scaleIn = useCallback((delay = 0) => ({
    initial: { scale: 0.8, opacity: 0 },
    animate: { scale: 1, opacity: 1 },
    transition: { duration: 0.3, delay },
  }), [])

  const stagger = useCallback((staggerChildren = 0.1, delayChildren = 0) => ({
    animate: 'visible',
    initial: 'hidden',
    variants: {
      visible: {
        transition: {
          staggerChildren,
          delayChildren,
        },
      },
      hidden: {},
    },
  }), [])

  const healthcareSpecific = useMemo(() => ({
    vitalSignPulse: (isCritical = false) => ({
      initial: { scale: 1, opacity: 0.8 },
      animate: {
        scale: [1, isCritical ? 1.2 : 1.1, 1],
        opacity: [0.8, 1, 0.8],
        borderColor: isCritical ? '#ef4444' : '#3b82f6',
      },
      transition: {
        duration: isCritical ? 1 : 2,
        repeat: Infinity,
        repeatType: 'reverse' as const,
        ease: 'easeInOut',
      },
    }),

    medicationReminder: () => ({
      initial: { y: -50, opacity: 0, scale: 0.8 },
      animate: { y: 0, opacity: 1, scale: 1 },
      transition: { type: 'spring', damping: 25, stiffness: 300 },
    }),

    emergencyAlert: () => ({
      initial: { scale: 0, opacity: 0, rotate: -10 },
      animate: { scale: 1, opacity: 1, rotate: [0, -5, 5, 0] },
      transition: {
        duration: 0.6,
        type: 'spring',
        damping: 15,
        stiffness: 400,
      },
    }),

    patientStatusChange: (from: string, to: string) => ({
      initial: { scale: 1, backgroundColor: alpha('#6b7280', 0.1) },
      animate: {
        scale: [1, 1.1, 1],
        backgroundColor: [
          alpha('#6b7280', 0.1),
          alpha('#10b981', 0.3),
          alpha('#10b981', 0.1),
        ],
      },
      transition: { duration: 0.8, ease: 'easeInOut' },
    }),

    appointmentScheduling: () => ({
      initial: { scale: 0, opacity: 0, y: 20 },
      animate: { scale: 1, opacity: 1, y: 0 },
      transition: {
        type: 'spring',
        damping: 20,
        stiffness: 300,
        delay: 0.1,
      },
    }),

    labResultAnimation: () => ({
      initial: { opacity: 0, x: -20 },
      animate: { opacity: 1, x: 0 },
      transition: { duration: 0.4, ease: 'easeOut' },
    }),

    medicalRecordTransition: () => ({
      initial: { opacity: 0, transform: 'translateX(-100%)' },
      animate: { opacity: 1, transform: 'translateX(0%)' },
      exit: { opacity: 0, transform: 'translateX(100%)' },
      transition: { duration: 0.3, ease: 'easeInOut' },
    }),
  }), [])

  const contextValue: AnimationContextType = {
    pulse,
    slideIn,
    fadeIn,
    scaleIn,
    stagger,
    healthcareSpecific,
  }

  return (
    <AnimationContext.Provider value={contextValue}>
      <MotionConfig
        transition={{ type: 'spring', damping: 25, stiffness: 300 }}
      >
        {children}
      </MotionConfig>
    </AnimationContext.Provider>
  )
}

// Hook to use animations
export const useAnimations = () => useContext(AnimationContext)

// Styled components with animations
export const AnimatedCard = styled(motion.div)(({ theme }: { theme?: Theme }) => ({
  backgroundColor: theme?.palette.background.paper,
  borderRadius: theme?.shape.borderRadius,
  border: `1px solid ${alpha(theme?.palette.divider || '#000', 0.1)}`,
  boxShadow: theme?.shadows[1],
  cursor: 'pointer',
  transition: 'all 0.2s ease-in-out',
  '&:hover': {
    boxShadow: theme?.shadows[4],
    transform: 'translateY(-2px)',
  },
}))

export const AnimatedButton = styled(motion.button)(({ theme }: { theme?: Theme }) => ({
  padding: theme?.spacing(1.5, 3),
  borderRadius: theme?.shape.borderRadius,
  border: 'none',
  backgroundColor: theme?.palette.primary.main,
  color: theme?.palette.primary.contrastText,
  fontSize: '0.875rem',
  fontWeight: 500,
  cursor: 'pointer',
  outline: 'none',
  '&:hover': {
    backgroundColor: theme?.palette.primary.dark,
  },
  '&:focus': {
    outline: `2px solid ${alpha(theme?.palette.primary.main, 0.5)}`,
    outlineOffset: '2px',
  },
}))

export const AnimatedBadge = styled(motion.div)(({ theme }: { theme?: Theme }) => ({
  display: 'inline-flex',
  alignItems: 'center',
  justifyContent: 'center',
  padding: '0.25rem 0.5rem',
  borderRadius: '9999px',
  fontSize: '0.75rem',
  fontWeight: 500,
  minWidth: '1.5rem',
  height: '1.5rem',
}))

// Healthcare-specific animated components
export const VitalSignsIndicator: React.FC<{
  value: number
  isCritical?: boolean
  label: string
  unit: string
}> = ({ value, isCritical, label, unit }) => {
  const { healthcareSpecific } = useAnimations()

  return (
    <AnimatedCard
      variants={healthcareSpecific.vitalSignPulse(isCritical)}
      initial="initial"
      animate="animate"
      sx={{
        p: 2,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        border: isCritical ? `2px solid #ef4444` : `1px solid #e5e7eb`,
      }}
    >
      <Typography variant="caption" color="textSecondary" sx={{ mb: 0.5 }}>
        {label}
      </Typography>
      <Typography
        variant="h4"
        fontWeight={600}
        color={isCritical ? 'error.main' : 'text.primary'}
      >
        {value} {unit}
      </Typography>
    </AnimatedCard>
  )
}

export const EmergencyAlert: React.FC<{
  message: string
  onDismiss?: () => void
}> = ({ message, onDismiss }) => {
  const { healthcareSpecific } = useAnimations()

  return (
    <motion.div
      variants={healthcareSpecific.emergencyAlert()}
      initial="initial"
      animate="animate"
      style={{
        position: 'fixed',
        top: 20,
        right: 20,
        zIndex: 9999,
      }}
    >
      <Box
        sx={{
          backgroundColor: '#fee2e2',
          border: '2px solid #ef4444',
          borderRadius: 2,
          p: 3,
          minWidth: 300,
          boxShadow: 8,
        }}
      >
        <Box display="flex" alignItems="center" gap={2}>
          <Box
            sx={{
              width: 40,
              height: 40,
              borderRadius: '50%',
              backgroundColor: '#ef4444',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              animation: 'pulse 2s infinite',
            }}
          >
            <span style={{ color: 'white', fontSize: '20px' }}>!</span>
          </Box>
          <Box sx={{ flexGrow: 1 }}>
            <Typography variant="h6" fontWeight={600} color="#991b1b">
              Emergency Alert
            </Typography>
            <Typography variant="body2" color="#7f1d1d">
              {message}
            </Typography>
          </Box>
          {onDismiss && (
            <Button
              size="small"
              onClick={onDismiss}
              sx={{ color: '#7f1d1d' }}
            >
              Dismiss
            </Button>
          )}
        </Box>
      </Box>
    </motion.div>
  )
}

export const MedicationReminder: React.FC<{
  medicationName: string
  dosage: string
  time: string
  onTake?: () => void
  onSnooze?: () => void
}> = ({ medicationName, dosage, time, onTake, onSnooze }) => {
  const { healthcareSpecific } = useAnimations()

  return (
    <motion.div
      variants={healthcareSpecific.medicationReminder()}
      initial="initial"
      animate="animate"
      style={{
        position: 'fixed',
        bottom: 20,
        right: 20,
        zIndex: 9998,
      }}
    >
      <Box
        sx={{
          backgroundColor: '#f0f9ff',
          border: '2px solid #0ea5e9',
          borderRadius: 2,
          p: 3,
          minWidth: 320,
          boxShadow: 8,
        }}
      >
        <Box sx={{ mb: 2 }}>
          <Typography variant="h6" fontWeight={600} color="#0369a1">
            Medication Reminder
          </Typography>
          <Typography variant="body2" color="#0c4a6e">
            {time}
          </Typography>
        </Box>
        <Box sx={{ mb: 2 }}>
          <Typography variant="subtitle1" fontWeight={600}>
            {medicationName}
          </Typography>
          <Typography variant="body2" color="#0c4a6e">
            {dosage}
          </Typography>
        </Box>
        <Box display="flex" gap={1}>
          {onTake && (
            <Button
              variant="contained"
              size="small"
              onClick={onTake}
              sx={{ backgroundColor: '#0ea5e9', color: 'white' }}
            >
              Take Now
            </Button>
          )}
          {onSnooze && (
            <Button
              variant="outlined"
              size="small"
              onClick={onSnooze}
              sx={{ borderColor: '#0ea5e9', color: '#0ea5e9' }}
            >
              Snooze
            </Button>
          )}
        </Box>
      </Box>
    </motion.div>
  )
}

export const PatientStatusTransition: React.FC<{
  fromStatus: string
  toStatus: string
  patientName: string
}> = ({ fromStatus, toStatus, patientName }) => {
  const { healthcareSpecific } = useAnimations()

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'stable': return '#10b981'
      case 'critical': return '#ef4444'
      case 'serious': return '#f59e0b'
      case 'fair': return '#3b82f6'
      default: return '#6b7280'
    }
  }

  return (
    <motion.div
      variants={healthcareSpecific.patientStatusChange(fromStatus, toStatus)}
      initial="initial"
      animate="animate"
      style={{
        position: 'fixed',
        top: '50%',
        left: '50%',
        transform: 'translate(-50%, -50%)',
        zIndex: 9997,
      }}
    >
      <Box
        sx={{
          backgroundColor: 'white',
          borderRadius: 2,
          p: 4,
          textAlign: 'center',
          minWidth: 400,
          boxShadow: 16,
          border: `2px solid ${getStatusColor(toStatus)}`,
        }}
      >
        <Typography variant="h4" fontWeight={600} sx={{ mb: 2 }}>
          Patient Status Updated
        </Typography>
        <Typography variant="body1" sx={{ mb: 1 }}>
          <strong>{patientName}</strong>
        </Typography>
        <Box display="flex" alignItems="center" justifyContent="center" gap={2}>
          <Typography
            variant="h6"
            sx={{ color: getStatusColor(fromStatus), textDecoration: 'line-through' }}
          >
            {fromStatus}
          </Typography>
          <span>→</span>
          <Typography
            variant="h6"
            sx={{ color: getStatusColor(toStatus) }}
          >
            {toStatus}
          </Typography>
        </Box>
      </Box>
    </motion.div>
  )
}

export const LoadingSkeleton: React.FC<{
  lines?: number
  height?: number
}> = ({ lines = 3, height = 20 }) => {
  return (
    <Box sx={{ width: '100%' }}>
      {Array.from({ length: lines }).map((_, index) => (
        <motion.div
          key={index}
          initial={{ opacity: 0, width: 0 }}
          animate={{ opacity: 1, width: '100%' }}
          transition={{ duration: 0.5, delay: index * 0.1 }}
          style={{
            height,
            backgroundColor: '#e5e7eb',
            borderRadius: 4,
            marginBottom: 8,
          }}
        />
      ))}
    </Box>
  )
}

export const PageTransition: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { fadeIn } = useAnimations()

  return (
    <motion.div
      variants={fadeIn(0.1)}
      initial="initial"
      animate="animate"
      exit={{ opacity: 0 }}
      style={{ width: '100%', height: '100%' }}
    >
      {children}
    </motion.div>
  )
}

// Staggered list animation
export const StaggeredList: React.FC<{
  children: React.ReactNode[]
  delay?: number
}> = ({ children, delay = 0.1 }) => {
  const { stagger } = useAnimations()

  return (
    <motion.div
      variants={stagger(0.1, delay)}
      initial="hidden"
      animate="visible"
    >
      {children.map((child, index) => (
        <motion.div
          key={index}
          variants={{
            hidden: { opacity: 0, y: 20 },
            visible: { opacity: 1, y: 0 },
          }}
        >
          {child}
        </motion.div>
      ))}
    </motion.div>
  )
}

// Floating action button with healthcare theme
export const HealthcareFab: React.FC<{
  icon: React.ReactNode
  label: string
  onClick: () => void
  color?: 'primary' | 'secondary' | 'error' | 'warning' | 'success'
}> = ({ icon, label, onClick, color = 'primary' }) => {
  const { scaleIn } = useAnimations()

  const getColor = () => {
    switch (color) {
      case 'primary': return '#3b82f6'
      case 'secondary': return '#10b981'
      case 'error': return '#ef4444'
      case 'warning': return '#f59e0b'
      case 'success': return '#10b981'
      default: return '#3b82f6'
    }
  }

  return (
    <motion.div
      variants={scaleIn(0.3)}
      initial="initial"
      animate="animate"
      whileHover={{ scale: 1.05 }}
      whileTap={{ scale: 0.95 }}
      style={{
        position: 'fixed',
        bottom: 20,
        right: 20,
        zIndex: 1000,
      }}
    >
      <Box
        onClick={onClick}
        sx={{
          backgroundColor: getColor(),
          color: 'white',
          width: 56,
          height: 56,
          borderRadius: '50%',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          cursor: 'pointer',
          boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
          transition: 'all 0.2s ease-in-out',
          '&:hover': {
            transform: 'scale(1.05)',
            boxShadow: '0 6px 20px rgba(0, 0, 0, 0.25)',
          },
        }}
      >
        {icon}
      </Box>
      {label && (
        <Box
          sx={{
            position: 'absolute',
            right: 70,
            backgroundColor: 'rgba(0, 0, 0, 0.8)',
            color: 'white',
            padding: '8px 12px',
            borderRadius: '6px',
            fontSize: '14px',
            whiteSpace: 'nowrap',
          }}
        >
          {label}
        </Box>
      )}
    </motion.div>
  )
}

// Pulse animation for notifications
export const PulseNotification: React.FC<{
  count: number
  children: React.ReactNode
}> = ({ count, children }) => {
  return (
    <Box sx={{ position: 'relative', display: 'inline-block' }}>
      {children}
      {count > 0 && (
        <motion.div
          style={{
            position: 'absolute',
            top: -8,
            right: -8,
            width: 20,
            height: 20,
            borderRadius: '50%',
            backgroundColor: '#ef4444',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'white',
            fontSize: '12px',
            fontWeight: 'bold',
          }}
          animate={{
            scale: [1, 1.2, 1],
          }}
          transition={{
            duration: 2,
            repeat: Infinity,
            repeatType: 'reverse' as const,
          }}
        >
          {count > 99 ? '99+' : count}
        </motion.div>
      )}
    </Box>
  )
}

// CSS for keyframe animations
export const GlobalAnimationStyles = () => (
  <style jsx global>{`
    @keyframes pulse {
      0% {
        transform: scale(1);
        opacity: 1;
      }
      50% {
        transform: scale(1.1);
        opacity: 0.8;
      }
      100% {
        transform: scale(1);
        opacity: 1;
      }
    }

    @keyframes slideInUp {
      from {
        transform: translateY(100%);
        opacity: 0;
      }
      to {
        transform: translateY(0);
        opacity: 1;
      }
    }

    @keyframes fadeIn {
      from {
        opacity: 0;
      }
      to {
        opacity: 1;
      }
    }

    @keyframes heartbeat {
      0% {
        transform: scale(1);
      }
      14% {
        transform: scale(1.1);
      }
      28% {
        transform: scale(1);
      }
      42% {
        transform: scale(1.1);
      }
      70% {
        transform: scale(1);
      }
    }

    .animate-pulse {
      animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
    }

    .animate-slide-in-up {
      animation: slideInUp 0.3s ease-out;
    }

    .animate-fade-in {
      animation: fadeIn 0.3s ease-out;
    }

    .animate-heartbeat {
      animation: heartbeat 1.5s ease-in-out infinite;
    }

    .transition-all {
      transition: all 0.3s ease-in-out;
    }

    .transition-transform {
      transition: transform 0.3s ease-in-out;
    }

    .transition-opacity {
      transition: opacity 0.3s ease-in-out;
    }
  `}</style>
)

export default HealthcareAnimations