import React, { useMemo, useCallback, memo } from 'react'
import { useInView } from 'react-intersection-observer'

// Performance monitoring utilities
export const usePerformanceMetrics = () => {
  const metrics = useMemo(() => ({
    // Navigation timing
    navigationTiming: {
      getLoadTime: () => {
        if (typeof window !== 'undefined' && window.performance) {
          const navigation = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming
          return navigation.loadEventEnd - navigation.loadEventStart
        }
        return 0
      },
      getDomReadyTime: () => {
        if (typeof window !== 'undefined' && window.performance) {
          const navigation = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming
          return navigation.domContentLoadedEventEnd - navigation.domContentLoadedEventStart
        }
        return 0
      },
      getFirstPaint: () => {
        if (typeof window !== 'undefined' && window.performance) {
          const paint = performance.getEntriesByType('paint')
          const firstPaint = paint.find(entry => entry.name === 'first-paint')
          return firstPaint ? firstPaint.startTime : 0
        }
        return 0
      },
      getFirstContentfulPaint: () => {
        if (typeof window !== 'undefined' && window.performance) {
          const paint = performance.getEntriesByType('paint')
          const fcp = paint.find(entry => entry.name === 'first-contentful-paint')
          return fcp ? fcp.startTime : 0
        }
        return 0
      }
    },

    // Resource timing
    resourceTiming: {
      getResourcesByType: (type: string) => {
        if (typeof window !== 'undefined' && window.performance) {
          return performance.getEntriesByType('resource').filter((entry: PerformanceResourceTiming) =>
            entry.initiatorType === type
          )
        }
        return []
      },
      getLargestContentfulPaint: () => {
        if (typeof window !== 'undefined' && 'PerformanceObserver' in window) {
          const lcpEntries = performance.getEntriesByType('largest-contentful-paint')
          return lcpEntries.length > 0 ? lcpEntries[lcpEntries.length - 1].startTime : 0
        }
        return 0
      }
    },

    // Layout shifts
    layoutShift: {
      getCumulativeLayoutShift: () => {
        if (typeof window !== 'undefined' && 'PerformanceObserver' in window) {
          const clsEntries = performance.getEntriesByType('layout-shift')
          return clsEntries.reduce((sum, entry: any) => sum + entry.value, 0)
        }
        return 0
      }
    }
  }), [])

  return metrics
}

// Virtual scrolling utilities
export const useVirtualList = <T,>(
  items: T[],
  itemHeight: number,
  containerHeight: number,
  overscan: number = 5
) => {
  const [scrollTop, setScrollTop] = React.useState(0)

  const visibleRange = useMemo(() => {
    const startIndex = Math.max(0, Math.floor(scrollTop / itemHeight) - overscan)
    const endIndex = Math.min(
      items.length - 1,
      Math.floor((scrollTop + containerHeight) / itemHeight) + overscan
    )
    return { startIndex, endIndex }
  }, [scrollTop, itemHeight, containerHeight, overscan, items.length])

  const visibleItems = useMemo(() => {
    return items.slice(visibleRange.startIndex, visibleRange.endIndex + 1)
  }, [items, visibleRange])

  const totalHeight = items.length * itemHeight
  const offsetY = visibleRange.startIndex * itemHeight

  const handleScroll = useCallback((e: React.UIEvent<HTMLDivElement>) => {
    setScrollTop(e.currentTarget.scrollTop)
  }, [])

  return {
    visibleItems,
    totalHeight,
    offsetY,
    handleScroll,
    startIndex: visibleRange.startIndex
  }
}

// Intersection observer for lazy loading
export const useLazyLoad = (
  threshold: number = 0.1,
  rootMargin: string = '50px'
) => {
  const { ref, inView, entry } = useInView({
    threshold,
    rootMargin,
    triggerOnce: true
  })

  return { ref, inView, entry }
}

// Memoized image component
export const LazyImage = memo(({
  src,
  alt,
  width,
  height,
  placeholder = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTAwIiBoZWlnaHQ9IjEwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTAwIiBoZWlnaHQ9IjEwMCIgZmlsbD0iI2Y0ZjRmNCIvPjx0ZXh0IHg9IjUwIiB5PSI1MCIgZm9udC1mYW1pbHk9IkFyaWFsIiBmb250LXNpemU9IjE0IiBmaWxsPSIjOTk5IiB0ZXh0LWFuY2hvcj0ibWlkZGxlIiBkeT0iLjNlbSI+TG9hZGluZy4uLjwvdGV4dD48L3N2Zz4=',
  className = '',
  onLoad,
  onError,
  ...props
}: {
  src: string
  alt: string
  width?: number | string
  height?: number | string
  placeholder?: string
  className?: string
  onLoad?: () => void
  onError?: () => void
} & React.ImgHTMLAttributes<HTMLImageElement>) => {
  const { ref, inView } = useLazyLoad()

  const [isLoaded, setIsLoaded] = React.useState(false)
  const [hasError, setHasError] = React.useState(false)

  const handleLoad = useCallback(() => {
    setIsLoaded(true)
    setHasError(false)
    onLoad?.()
  }, [onLoad])

  const handleError = useCallback(() => {
    setHasError(true)
    onError?.()
  }, [onError])

  return (
    <div ref={ref} className={className} style={{ position: 'relative', width, height }}>
      {inView && (
        <>
          {!isLoaded && !hasError && (
            <img
              src={placeholder}
              alt=""
              style={{
                position: 'absolute',
                top: 0,
                left: 0,
                width: '100%',
                height: '100%',
                objectFit: 'cover'
              }}
            />
          )}
          <img
            src={src}
            alt={alt}
            onLoad={handleLoad}
            onError={handleError}
            style={{
              position: 'absolute',
              top: 0,
              left: 0,
              width: '100%',
              height: '100%',
              objectFit: 'cover',
              opacity: isLoaded ? 1 : 0,
              transition: 'opacity 0.3s ease-in-out'
            }}
            loading="lazy"
            {...props}
          />
          {hasError && (
            <div
              style={{
                position: 'absolute',
                top: 0,
                left: 0,
                width: '100%',
                height: '100%',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                backgroundColor: '#f5f5f5',
                color: '#999'
              }}
            >
              <span>Image failed to load</span>
            </div>
          )}
        </>
      )}
    </div>
  )
})

LazyImage.displayName = 'LazyImage'

// Debounce utility
export const useDebounce = <T>(value: T, delay: number): T => {
  const [debouncedValue, setDebouncedValue] = React.useState<T>(value)

  React.useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value)
    }, delay)

    return () => {
      clearTimeout(handler)
    }
  }, [value, delay])

  return debouncedValue
}

// Throttle utility
export const useThrottle = <T>(value: T, delay: number): T => {
  const [throttledValue, setThrottledValue] = React.useState<T>(value)
  const lastExecuted = React.useRef<number>(0)

  React.useEffect(() => {
    const now = Date.now()
    const timeElapsed = now - lastExecuted.current

    if (timeElapsed >= delay) {
      setThrottledValue(value)
      lastExecuted.current = now
    } else {
      const timer = setTimeout(() => {
        setThrottledValue(value)
        lastExecuted.current = Date.now()
      }, delay - timeElapsed)

      return () => clearTimeout(timer)
    }
  }, [value, delay])

  return throttledValue
}

// Performance-aware component wrapper
export const withPerformanceMonitoring = <P extends object>(
  Component: React.ComponentType<P>,
  componentName: string
) => {
  const WrappedComponent = memo((props: P) => {
    const renderStart = React.useRef<number>(0)
    const renderCount = React.useRef<number>(0)

    React.useEffect(() => {
      renderStart.current = performance.now()
      renderCount.current += 1
    })

    React.useEffect(() => {
      const renderTime = performance.now() - renderStart.current

      // Log performance metrics in development
      if (process.env.NODE_ENV === 'development') {
        console.log(`[Performance] ${componentName} rendered:`, {
          renderTime: `${renderTime.toFixed(2)}ms`,
          renderCount: renderCount.current
        })
      }
    })

    return <Component {...props} />
  })

  WrappedComponent.displayName = `WithPerformanceMonitoring(${componentName})`
  return WrappedComponent
}

// Resource preloading utility
export const preloadResources = (resources: Array<{ href: string; as: string; type?: string }>) => {
  if (typeof window === 'undefined') return

  resources.forEach(resource => {
    const link = document.createElement('link')
    link.rel = 'preload'
    link.href = resource.href
    link.as = resource.as

    if (resource.type) {
      link.type = resource.type
    }

    document.head.appendChild(link)
  })
}

// Critical CSS inlining utility
export const injectCriticalCSS = (css: string) => {
  if (typeof window === 'undefined') return

  const style = document.createElement('style')
  style.textContent = css
  style.setAttribute('data-critical', 'true')
  document.head.appendChild(style)
}

// Bundle size monitoring
export const useBundleSize = () => {
  const [bundleInfo, setBundleInfo] = React.useState<{
    totalSize: number
    chunkCount: number
    largestChunk: number
    loadTime: number
  } | null>(null)

  React.useEffect(() => {
    if (typeof window !== 'undefined' && window.performance) {
      const resources = performance.getEntriesByType('resource')
      const jsResources = resources.filter((r: PerformanceResourceTiming) =>
        r.initiatorType === 'script' || r.name.endsWith('.js')
      )

      const totalSize = jsResources.reduce((sum, r: PerformanceResourceTiming) =>
        sum + (r.encodedBodySize || 0), 0
      )

      const largestChunk = Math.max(...jsResources.map((r: PerformanceResourceTiming) =>
        r.encodedBodySize || 0
      ))

      const loadTime = Math.max(...jsResources.map((r: PerformanceResourceTiming) =>
        r.responseEnd - r.startTime
      ))

      setBundleInfo({
        totalSize,
        chunkCount: jsResources.length,
        largestChunk,
        loadTime
      })
    }
  }, [])

  return bundleInfo
}

// Memory usage monitoring (development only)
export const useMemoryMonitoring = () => {
  const [memoryInfo, setMemoryInfo] = React.useState<{
    usedJSHeapSize: number
    totalJSHeapSize: number
    jsHeapSizeLimit: number
  } | null>(null)

  React.useEffect(() => {
    if (process.env.NODE_ENV === 'development' && typeof window !== 'undefined') {
      const interval = setInterval(() => {
        const memory = (window as any).performance?.memory
        if (memory) {
          setMemoryInfo({
            usedJSHeapSize: memory.usedJSHeapSize,
            totalJSHeapSize: memory.totalJSHeapSize,
            jsHeapSizeLimit: memory.jsHeapSizeLimit
          })
        }
      }, 5000)

      return () => clearInterval(interval)
    }
  }, [])

  return memoryInfo
}