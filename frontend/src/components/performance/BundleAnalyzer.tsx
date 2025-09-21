import React, { useEffect, useState } from 'react'

interface BundleInfo {
  totalSize: number
  chunkCount: number
  largestChunk: number
  loadTime: number
  chunks: Array<{
    name: string
    size: number
    loadTime: number
  }>
}

interface BundleAnalyzerProps {
  enableDebugMode?: boolean
  onBundleUpdate?: (bundleInfo: BundleInfo) => void
}

const BundleAnalyzer: React.FC<BundleAnalyzerProps> = ({
  enableDebugMode = false,
  onBundleUpdate,
}) => {
  const [bundleInfo, setBundleInfo] = useState<BundleInfo | null>(null)
  const [isVisible, setIsVisible] = useState(false)

  useEffect(() => {
    if (typeof window === 'undefined' || !window.performance) {
      return
    }

    const analyzeBundle = () => {
      const resources = performance.getEntriesByType('resource')
      const jsResources = resources.filter((r: PerformanceResourceTiming) =>
        r.initiatorType === 'script' || r.name.endsWith('.js')
      ) as PerformanceResourceTiming[]

      const chunks = jsResources.map(resource => ({
        name: resource.name.split('/').pop() || 'unknown',
        size: resource.encodedBodySize || resource.transferSize || 0,
        loadTime: resource.responseEnd - resource.startTime,
      }))

      const totalSize = chunks.reduce((sum, chunk) => sum + chunk.size, 0)
      const largestChunk = Math.max(...chunks.map(chunk => chunk.size))
      const loadTime = Math.max(...chunks.map(chunk => chunk.loadTime))

      const info: BundleInfo = {
        totalSize,
        chunkCount: chunks.length,
        largestChunk,
        loadTime,
        chunks,
      }

      setBundleInfo(info)
      onBundleUpdate?.(info)

      if (enableDebugMode) {
        console.log('[Bundle Analysis]', info)
      }
    }

    // Initial analysis
    analyzeBundle()

    // Re-analyze on load event
    window.addEventListener('load', analyzeBundle)

    // Periodic analysis in development
    let intervalId: NodeJS.Timeout
    if (process.env.NODE_ENV === 'development' && enableDebugMode) {
      intervalId = setInterval(analyzeBundle, 5000)
    }

    return () => {
      window.removeEventListener('load', analyzeBundle)
      if (intervalId) {
        clearInterval(intervalId)
      }
    }
  }, [onBundleUpdate, enableDebugMode])

  useEffect(() => {
    // Keyboard shortcut to toggle visibility
    const handleKeyPress = (e: KeyboardEvent) => {
      if (e.ctrlKey && e.shiftKey && e.key === 'B') {
        setIsVisible(!isVisible)
      }
    }

    document.addEventListener('keydown', handleKeyPress)

    return () => {
      document.removeEventListener('keydown', handleKeyPress)
    }
  }, [isVisible])

  const formatBytes = (bytes: number): string => {
    if (bytes === 0) return '0 B'
    const k = 1024
    const sizes = ['B', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  const formatTime = (ms: number): string => {
    return `${ms.toFixed(0)}ms`
  }

  if (!enableDebugMode && !isVisible) {
    return null
  }

  return (
    <div
      style={{
        position: 'fixed',
        bottom: enableDebugMode ? 200 : 10,
        right: enableDebugMode ? 20 : 10,
        backgroundColor: 'rgba(255, 255, 255, 0.95)',
        border: '1px solid #ddd',
        borderRadius: '8px',
        padding: '16px',
        boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
        fontSize: '12px',
        fontFamily: 'monospace',
        zIndex: 9998,
        minWidth: enableDebugMode ? '350px' : '250px',
        backdropFilter: 'blur(10px)',
      }}
    >
      {enableDebugMode && (
        <div style={{ marginBottom: '12px', textAlign: 'center' }}>
          <div style={{ fontSize: '14px', fontWeight: 'bold', color: '#2196f3' }}>
            Bundle Analysis
          </div>
          <div style={{ fontSize: '10px', color: '#666', marginTop: '4px' }}>
            Press Ctrl+Shift+B to toggle
          </div>
        </div>
      )}

      {bundleInfo ? (
        <>
          <div style={{ display: 'grid', gap: '8px', marginBottom: '12px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span>Total Size:</span>
              <span style={{ fontWeight: 'bold' }}>{formatBytes(bundleInfo.totalSize)}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span>Chunks:</span>
              <span>{bundleInfo.chunkCount}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span>Largest Chunk:</span>
              <span>{formatBytes(bundleInfo.largestChunk)}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span>Load Time:</span>
              <span>{formatTime(bundleInfo.loadTime)}</span>
            </div>
          </div>

          {enableDebugMode && bundleInfo.chunks.length > 0 && (
            <div>
              <div style={{ fontSize: '10px', fontWeight: 'bold', marginBottom: '6px', color: '#666' }}>
                Individual Chunks:
              </div>
              <div style={{ maxHeight: '200px', overflowY: 'auto', fontSize: '10px' }}>
                {bundleInfo.chunks
                  .sort((a, b) => b.size - a.size)
                  .map((chunk, index) => (
                    <div
                      key={index}
                      style={{
                        display: 'flex',
                        justifyContent: 'space-between',
                        padding: '2px 0',
                        borderBottom: index < bundleInfo.chunks.length - 1 ? '1px solid #eee' : 'none',
                      }}
                    >
                      <span style={{ maxWidth: '150px', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                        {chunk.name}
                      </span>
                      <div style={{ display: 'flex', gap: '8px' }}>
                        <span>{formatBytes(chunk.size)}</span>
                        <span style={{ color: '#666' }}>{formatTime(chunk.loadTime)}</span>
                      </div>
                    </div>
                  ))}
              </div>
            </div>
          )}
        </>
      ) : (
        <div style={{ textAlign: 'center', color: '#666', padding: '20px' }}>
          Analyzing bundle...
        </div>
      )}
    </div>
  )
}

export default BundleAnalyzer