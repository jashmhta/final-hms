import React, { useEffect, useState } from 'react'

interface PerformanceMetrics {
  lcp: number | null
  fid: number | null
  cls: number | null
  fcp: number | null
  ttfb: number | null
  inp: number | null
}

interface WebVitalsProps {
  onMetricsUpdate?: (metrics: PerformanceMetrics) => void
  enableDebugMode?: boolean
  sampleRate?: number
}

const WebVitalsMonitor: React.FC<WebVitalsProps> = ({
  onMetricsUpdate,
  enableDebugMode = false,
  sampleRate = 1,
}) => {
  const [metrics, setMetrics] = useState<PerformanceMetrics>({
    lcp: null,
    fid: null,
    cls: null,
    fcp: null,
    ttfb: null,
    inp: null,
  })
  const [isVisible, setIsVisible] = useState(false)
  const [healthScore, setHealthScore] = useState<number | null>(null)

  // Calculate overall health score
  const calculateHealthScore = (metrics: PerformanceMetrics): number => {
    const weights = {
      lcp: 0.25,
      fid: 0.2,
      cls: 0.25,
      fcp: 0.15,
      ttfb: 0.1,
      inp: 0.05,
    }

    const scores = {
      lcp: metrics.lcp ? Math.max(0, 100 - (metrics.lcp - 2500) / 25) : 100,
      fid: metrics.fid ? Math.max(0, 100 - (metrics.fid - 100) / 1) : 100,
      cls: metrics.cls ? Math.max(0, 100 - (metrics.cls - 0.1) / 0.001) : 100,
      fcp: metrics.fcp ? Math.max(0, 100 - (metrics.fcp - 1800) / 18) : 100,
      ttfb: metrics.ttfb ? Math.max(0, 100 - (metrics.ttfb - 800) / 8) : 100,
      inp: metrics.inp ? Math.max(0, 100 - (metrics.inp - 200) / 2) : 100,
    }

    return Math.round(
      Object.entries(weights).reduce(
        (sum, [metric, weight]) => sum + (scores[metric as keyof typeof scores] || 0) * weight,
        0
      )
    )
  }

  // Get metric status
  const getMetricStatus = (value: number | null, thresholds: { good: number; poor: number }) => {
    if (value === null) return 'unknown'
    if (value <= thresholds.good) return 'good'
    if (value <= thresholds.poor) return 'needs-improvement'
    return 'poor'
  }

  // Get metric color
  const getMetricColor = (status: string) => {
    switch (status) {
      case 'good':
        return '#4caf50'
      case 'needs-improvement':
        return '#ff9800'
      case 'poor':
        return '#f44336'
      default:
        return '#9e9e9e'
    }
  }

  // Format metric value
  const formatMetric = (value: number | null, unit: string) => {
    if (value === null) return '—'
    return `${value.toFixed(1)}${unit}`
  }

  useEffect(() => {
    // Only monitor in production or when debug mode is enabled
    if (process.env.NODE_ENV !== 'production' && !enableDebugMode) {
      return
    }

    // Sample rate to reduce overhead
    if (Math.random() > sampleRate) {
      return
    }

    // Load web-vitals library dynamically
    const loadWebVitals = async () => {
      try {
        const { onCLS, onFID, onLCP, onFCP, onTTFB, onINP } = await import('web-vitals')

        const updateMetrics = (newMetrics: Partial<PerformanceMetrics>) => {
          const updated = { ...metrics, ...newMetrics }
          setMetrics(updated)
          setHealthScore(calculateHealthScore(updated))
          onMetricsUpdate?.(updated)

          if (enableDebugMode) {
            console.log('[Performance Metrics]', updated)
          }
        }

        // Register metric handlers
        onCLS((metric) => updateMetrics({ cls: metric.value }))
        onFID((metric) => updateMetrics({ fid: metric.value }))
        onLCP((metric) => updateMetrics({ lcp: metric.value }))
        onFCP((metric) => updateMetrics({ fcp: metric.value }))
        onTTFB((metric) => updateMetrics({ ttfb: metric.value }))
        onINP((metric) => updateMetrics({ inp: metric.value }))
      } catch (error) {
        console.error('Failed to load web-vitals:', error)
      }
    }

    loadWebVitals()

    // Keyboard shortcut to toggle visibility
    const handleKeyPress = (e: KeyboardEvent) => {
      if (e.ctrlKey && e.shiftKey && e.key === 'P') {
        setIsVisible(!isVisible)
      }
    }

    document.addEventListener('keydown', handleKeyPress)

    return () => {
      document.removeEventListener('keydown', handleKeyPress)
    }
  }, [metrics, onMetricsUpdate, enableDebugMode, sampleRate, isVisible])

  if (!enableDebugMode && !isVisible) {
    return null
  }

  const lcpStatus = getMetricStatus(metrics.lcp, { good: 2500, poor: 4000 })
  const fidStatus = getMetricStatus(metrics.fid, { good: 100, poor: 300 })
  const clsStatus = getMetricStatus(metrics.cls, { good: 0.1, poor: 0.25 })
  const fcpStatus = getMetricStatus(metrics.fcp, { good: 1800, poor: 3000 })
  const ttfbStatus = getMetricStatus(metrics.ttfb, { good: 800, poor: 1800 })
  const inpStatus = getMetricStatus(metrics.inp, { good: 200, poor: 500 })

  return (
    <div
      style={{
        position: 'fixed',
        bottom: enableDebugMode ? 20 : 10,
        right: enableDebugMode ? 20 : 10,
        backgroundColor: 'rgba(255, 255, 255, 0.95)',
        border: '1px solid #ddd',
        borderRadius: '8px',
        padding: '16px',
        boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
        fontSize: '12px',
        fontFamily: 'monospace',
        zIndex: 9999,
        minWidth: enableDebugMode ? '300px' : '200px',
        backdropFilter: 'blur(10px)',
      }}
    >
      {enableDebugMode && (
        <div style={{ marginBottom: '12px', textAlign: 'center' }}>
          <div
            style={{
              fontSize: '14px',
              fontWeight: 'bold',
              color: healthScore && healthScore >= 90 ? '#4caf50' : healthScore && healthScore >= 70 ? '#ff9800' : '#f44336',
            }}
          >
            Performance Score: {healthScore || '—'}%
          </div>
          <div style={{ fontSize: '10px', color: '#666', marginTop: '4px' }}>
            Press Ctrl+Shift+P to toggle
          </div>
        </div>
      )}

      <div style={{ display: 'grid', gap: '6px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span style={{ color: getMetricColor(lcpStatus) }}>LCP:</span>
          <span>{formatMetric(metrics.lcp, 'ms')}</span>
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span style={{ color: getMetricColor(fidStatus) }}>FID:</span>
          <span>{formatMetric(metrics.fid, 'ms')}</span>
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span style={{ color: getMetricColor(clsStatus) }}>CLS:</span>
          <span>{formatMetric(metrics.cls, '')}</span>
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span style={{ color: getMetricColor(fcpStatus) }}>FCP:</span>
          <span>{formatMetric(metrics.fcp, 'ms')}</span>
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span style={{ color: getMetricColor(ttfbStatus) }}>TTFB:</span>
          <span>{formatMetric(metrics.ttfb, 'ms')}</span>
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span style={{ color: getMetricColor(inpStatus) }}>INP:</span>
          <span>{formatMetric(metrics.inp, 'ms')}</span>
        </div>
      </div>

      {enableDebugMode && (
        <div style={{ marginTop: '12px', paddingTop: '12px', borderTop: '1px solid #eee', fontSize: '10px', color: '#666' }}>
          <div>LCP: Largest Contentful Paint</div>
          <div>FID: First Input Delay</div>
          <div>CLS: Cumulative Layout Shift</div>
          <div>FCP: First Contentful Paint</div>
          <div>TTFB: Time to First Byte</div>
          <div>INP: Interaction to Next Paint</div>
        </div>
      )}
    </div>
  )
}

export default WebVitalsMonitor