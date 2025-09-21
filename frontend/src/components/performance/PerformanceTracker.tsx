import React, { useEffect, useState } from 'react'

interface PerformanceEvent {
  timestamp: number
  type: 'render' | 'navigation' | 'resource' | 'interaction'
  name: string
  duration: number
  details?: Record<string, any>
}

interface PerformanceTrackerProps {
  enableDebugMode?: boolean
  maxEvents?: number
  onEventsUpdate?: (events: PerformanceEvent[]) => void
}

const PerformanceTracker: React.FC<PerformanceTrackerProps> = ({
  enableDebugMode = false,
  maxEvents = 50,
  onEventsUpdate,
}) => {
  const [events, setEvents] = useState<PerformanceEvent[]>([])
  const [isVisible, setIsVisible] = useState(false)

  const addEvent = (event: Omit<PerformanceEvent, 'timestamp'>) => {
    const newEvent: PerformanceEvent = {
      ...event,
      timestamp: Date.now(),
    }

    setEvents(prev => {
      const updated = [newEvent, ...prev].slice(0, maxEvents)
      onEventsUpdate?.(updated)
      return updated
    })
  }

  useEffect(() => {
    if (typeof window === 'undefined' || !window.performance) {
      return
    }

    // Track page load performance
    const handleLoad = () => {
      const navigation = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming
      if (navigation) {
        addEvent({
          type: 'navigation',
          name: 'Page Load',
          duration: navigation.loadEventEnd - navigation.navigationStart,
          details: {
            domContentLoaded: navigation.domContentLoadedEventEnd - navigation.domContentLoadedEventStart,
            firstPaint: navigation.responseStart,
            ttfb: navigation.responseEnd - navigation.requestStart,
          },
        })
      }
    }

    // Track resource loading
    const observeResources = () => {
      const observer = new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
          if (entry.entryType === 'resource') {
            const resource = entry as PerformanceResourceTiming
            if (resource.initiatorType === 'script' || resource.initiatorType === 'link') {
              addEvent({
                type: 'resource',
                name: resource.name.split('/').pop() || 'unknown',
                duration: resource.responseEnd - resource.startTime,
                details: {
                  size: resource.encodedBodySize,
                  type: resource.initiatorType,
                },
              })
            }
          }
        }
      })

      observer.observe({ entryTypes: ['resource'] })
      return observer
    }

    // Track user interactions
    const trackInteractions = () => {
      let interactionStart = 0

      const handleInteractionStart = () => {
        interactionStart = performance.now()
      }

      const handleInteractionEnd = (type: string) => {
        if (interactionStart > 0) {
          const duration = performance.now() - interactionStart
          if (duration > 50) { // Only track interactions slower than 50ms
            addEvent({
              type: 'interaction',
              name: type,
              duration,
            })
          }
          interactionStart = 0
        }
      }

      // Track clicks
      document.addEventListener('mousedown', handleInteractionStart)
      document.addEventListener('mouseup', () => handleInteractionEnd('click'))

      // Track key presses
      document.addEventListener('keydown', handleInteractionStart)
      document.addEventListener('keyup', () => handleInteractionEnd('keypress'))

      return () => {
        document.removeEventListener('mousedown', handleInteractionStart)
        document.removeEventListener('mouseup', () => handleInteractionEnd('click'))
        document.removeEventListener('keydown', handleInteractionStart)
        document.removeEventListener('keyup', () => handleInteractionEnd('keypress'))
      }
    }

    // Initialize tracking
    window.addEventListener('load', handleLoad)
    const resourceObserver = observeResources()
    const interactionCleanup = trackInteractions()

    // Periodic performance snapshot
    const intervalId = setInterval(() => {
      if (performance.memory) {
        const memory = performance.memory as any
        addEvent({
          type: 'render',
          name: 'Memory Usage',
          duration: memory.usedJSHeapSize,
          details: {
            total: memory.totalJSHeapSize,
            limit: memory.jsHeapSizeLimit,
            used: memory.usedJSHeapSize,
          },
        })
      }
    }, 10000)

    return () => {
      window.removeEventListener('load', handleLoad)
      resourceObserver?.disconnect()
      interactionCleanup()
      clearInterval(intervalId)
    }
  }, [maxEvents, onEventsUpdate])

  useEffect(() => {
    // Keyboard shortcut to toggle visibility
    const handleKeyPress = (e: KeyboardEvent) => {
      if (e.ctrlKey && e.shiftKey && e.key === 'T') {
        setIsVisible(!isVisible)
      }
    }

    document.addEventListener('keydown', handleKeyPress)

    return () => {
      document.removeEventListener('keydown', handleKeyPress)
    }
  }, [isVisible])

  const formatDuration = (duration: number): string => {
    if (duration < 1) return `${(duration * 1000).toFixed(1)}μs`
    if (duration < 1000) return `${duration.toFixed(1)}ms`
    return `${(duration / 1000).toFixed(1)}s`
  }

  const formatTimestamp = (timestamp: number): string => {
    const date = new Date(timestamp)
    return date.toLocaleTimeString()
  }

  const getEventTypeColor = (type: PerformanceEvent['type']) => {
    switch (type) {
      case 'render':
        return '#4caf50'
      case 'navigation':
        return '#2196f3'
      case 'resource':
        return '#ff9800'
      case 'interaction':
        return '#f44336'
      default:
        return '#9e9e9e'
    }
  }

  if (!enableDebugMode && !isVisible) {
    return null
  }

  return (
    <div
      style={{
        position: 'fixed',
        bottom: enableDebugMode ? 380 : 10,
        right: enableDebugMode ? 20 : 10,
        backgroundColor: 'rgba(255, 255, 255, 0.95)',
        border: '1px solid #ddd',
        borderRadius: '8px',
        padding: '16px',
        boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
        fontSize: '12px',
        fontFamily: 'monospace',
        zIndex: 9997,
        minWidth: enableDebugMode ? '400px' : '300px',
        backdropFilter: 'blur(10px)',
      }}
    >
      {enableDebugMode && (
        <div style={{ marginBottom: '12px', textAlign: 'center' }}>
          <div style={{ fontSize: '14px', fontWeight: 'bold', color: '#9c27b0' }}>
            Performance Events
          </div>
          <div style={{ fontSize: '10px', color: '#666', marginTop: '4px' }}>
            Press Ctrl+Shift+T to toggle
          </div>
        </div>
      )}

      {events.length > 0 ? (
        <div style={{ maxHeight: '300px', overflowY: 'auto' }}>
          {events.map((event, index) => (
            <div
              key={index}
              style={{
                padding: '6px 0',
                borderBottom: index < events.length - 1 ? '1px solid #eee' : 'none',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <div
                    style={{
                      width: '8px',
                      height: '8px',
                      borderRadius: '50%',
                      backgroundColor: getEventTypeColor(event.type),
                    }}
                  />
                  <span style={{ fontWeight: 'bold', fontSize: '11px' }}>
                    {event.name}
                  </span>
                  <span style={{ color: '#666', fontSize: '10px' }}>
                    ({event.type})
                  </span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span style={{ fontWeight: 'bold', color: event.duration > 100 ? '#f44336' : '#4caf50' }}>
                    {formatDuration(event.duration)}
                  </span>
                  <span style={{ color: '#999', fontSize: '10px' }}>
                    {formatTimestamp(event.timestamp)}
                  </span>
                </div>
              </div>

              {event.details && enableDebugMode && (
                <div style={{ marginLeft: '14px', fontSize: '10px', color: '#666' }}>
                  {Object.entries(event.details).map(([key, value], idx) => (
                    <div key={idx}>
                      {key}: {typeof value === 'number' ? formatDuration(value) : String(value)}
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      ) : (
        <div style={{ textAlign: 'center', color: '#666', padding: '20px' }}>
          Waiting for performance events...
        </div>
      )}
    </div>
  )
}

export default PerformanceTracker