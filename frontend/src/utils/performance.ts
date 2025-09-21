/**
 * Performance Optimization Utilities for React Frontend
 * Bundle optimization, lazy loading, and performance monitoring
 */

import { lazy, Suspense, ComponentType, LazyExoticComponent } from 'react';
import { useDispatch } from 'react-redux';
import axios from 'axios';
import { debounce, throttle } from 'lodash-es';

// Performance monitoring
interface PerformanceMetrics {
  componentName: string;
  renderTime: number;
  mountTime: number;
  updateCount: number;
  memoryUsage?: number;
}

// Cache for component metrics
const componentMetrics = new Map<string, PerformanceMetrics>();

// Intersection Observer for lazy loading
let intersectionObserver: IntersectionObserver | null = null;

/**
 * Create a performance-aware lazy component with preloading
 */
export function createLazyComponent<T extends ComponentType<any>>(
  importFn: () => Promise<{ default: T }>,
  componentName: string,
  options: {
    preload?: boolean;
    fallback?: React.ReactNode;
    preloadDelay?: number;
  } = {}
): LazyExoticComponent<T> {
  const { preload = false, fallback = <div>Loading...</div>, preloadDelay = 200 } = options;

  const LazyComponent = lazy(() => {
    const start = performance.now();
    return importFn().then(module => {
      const end = performance.now();
      logComponentMetric(componentName, {
        loadTime: end - start,
        loadedAt: Date.now()
      });
      return module;
    });
  });

  // Preload component after delay
  if (preload) {
    setTimeout(() => {
      importFn();
    }, preloadDelay);
  }

  const WrappedComponent = (props: any) => (
    <Suspense fallback={fallback}>
      <PerformanceMonitor name={componentName}>
        <LazyComponent {...props} />
      </PerformanceMonitor>
    </Suspense>
  );

  return WrappedComponent as LazyExoticComponent<T>;
}

/**
 * Performance Monitor HOC
 */
export const PerformanceMonitor: React.FC<{
  name: string;
  children: React.ReactNode;
}> = ({ name, children }) => {
  const dispatch = useDispatch();

  React.useEffect(() => {
    const mountStart = performance.now();
    let updateCount = 0;

    // Track renders
    const observer = new MutationObserver(() => {
      updateCount++;
    });

    const root = document.getElementById('root');
    if (root) {
      observer.observe(root, {
        subtree: true,
        childList: true,
        attributes: true,
        characterData: true
      });
    }

    return () => {
      const mountTime = performance.now() - mountStart;
      logComponentMetric(name, {
        mountTime,
        updateCount,
        renderedAt: Date.now()
      });
      observer.disconnect();
    };
  }, [name]);

  return <>{children}</>;
};

/**
 * Log component performance metrics
 */
function logComponentMetric(
  componentName: string,
  metrics: Partial<PerformanceMetrics>
) {
  const existing = componentMetrics.get(componentName) || {
    componentName,
    renderTime: 0,
    mountTime: 0,
    updateCount: 0
  };

  const updated = {
    ...existing,
    ...metrics,
    lastUpdated: Date.now()
  };

  componentMetrics.set(componentName, updated);

  // Log slow components
  if (metrics.mountTime && metrics.mountTime > 100) {
    console.warn(`Slow component detected: ${componentName} (${metrics.mountTime.toFixed(2)}ms)`);
  }

  // Send to analytics if available
  if (window.gtag) {
    window.gtag('event', 'component_performance', {
      component_name: componentName,
      mount_time: metrics.mountTime,
      update_count: metrics.updateCount
    });
  }
}

/**
 * Optimized API client with caching and retry
 */
export const optimizedAxios = axios.create({
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Response interceptor for caching
optimizedAxios.interceptors.response.use(
  (response) => {
    // Cache GET requests
    if (response.config.method?.toLowerCase() === 'get') {
      const cacheKey = `axios_cache_${response.config.url}_${JSON.stringify(response.config.params)}`;
      const cacheData = {
        data: response.data,
        timestamp: Date.now(),
        headers: response.headers
      };
      sessionStorage.setItem(cacheKey, JSON.stringify(cacheData));
    }
    return response;
  },
  async (error) => {
    const originalRequest = error.config;

    // Retry on network errors
    if (!error.response && !originalRequest._retry) {
      originalRequest._retry = true;
      await new Promise(resolve => setTimeout(resolve, 1000));
      return optimizedAxios(originalRequest);
    }

    return Promise.reject(error);
  }
);

// Request interceptor for cache check
optimizedAxios.interceptors.request.use((config) => {
  if (config.method?.toLowerCase() === 'get') {
    const cacheKey = `axios_cache_${config.url}_${JSON.stringify(config.params)}`;
    const cached = sessionStorage.getItem(cacheKey);

    if (cached) {
      const { data, timestamp } = JSON.parse(cached);
      // Cache for 5 minutes
      if (Date.now() - timestamp < 300000) {
        config.adapter = () => Promise.resolve({
          data,
          status: 200,
          statusText: 'OK',
          headers: {},
          config
        });
      }
    }
  }

  return config;
});

/**
 * Optimized image component with lazy loading and WebP support
 */
export const OptimizedImage: React.FC<{
  src: string;
  alt: string;
  width?: number;
  height?: number;
  className?: string;
  onLoad?: () => void;
}> = ({ src, alt, width, height, className, onLoad }) => {
  const [imgSrc, setImgSrc] = React.useState<string>('');
  const [loading, setLoading] = React.useState(true);
  const imgRef = React.useRef<HTMLImageElement>(null);

  React.useEffect(() => {
    if (!intersectionObserver) {
      intersectionObserver = new IntersectionObserver(
        (entries) => {
          entries.forEach(entry => {
            if (entry.isIntersecting) {
              const img = entry.target as HTMLImageElement;
              const webpSrc = img.dataset.src?.replace(/\.(jpg|jpeg|png)$/i, '.webp');
              const srcset = img.dataset.srcset;

              // Try WebP first, fallback to original
              if (webpSrc) {
                const testImg = new Image();
                testImg.onload = () => {
                  img.src = webpSrc;
                  if (srcset) img.srcset = srcset;
                };
                testImg.onerror = () => {
                  img.src = img.dataset.src!;
                  if (srcset) img.srcset = srcset;
                };
                testImg.src = webpSrc;
              } else {
                img.src = img.dataset.src!;
                if (srcset) img.srcset = srcset;
              }

              intersectionObserver?.unobserve(img);
            }
          });
        },
        { rootMargin: '50px' }
      );
    }

    if (imgRef.current) {
      intersectionObserver.observe(imgRef.current);
    }

    return () => {
      if (imgRef.current) {
        intersectionObserver?.unobserve(imgRef.current);
      }
    };
  }, []);

  return (
    <div className={`optimized-image-container ${className || ''}`} style={{ width, height }}>
      {loading && (
        <div className="image-placeholder">
          <div className="skeleton-loader" />
        </div>
      )}
      <img
        ref={imgRef}
        data-src={src}
        data-srcset={`
          ${src} 1x,
          ${src.replace(/(\.[^.]+)$/, '@2x$1')} 2x,
          ${src.replace(/(\.[^.]+)$/, '@3x$1')} 3x
        `}
        alt={alt}
        className={`optimized-image ${imgSrc ? 'loaded' : ''}`}
        onLoad={() => {
          setLoading(false);
          onLoad?.();
        }}
        style={{ opacity: loading ? 0 : 1 }}
      />
    </div>
  );
};

/**
 * Virtualized list component for large datasets
 */
export const VirtualizedList: React.FC<{
  items: any[];
  itemHeight: number;
  renderItem: (item: any, index: number) => React.ReactNode;
  className?: string;
}> = ({ items, itemHeight, renderItem, className }) => {
  const [scrollTop, setScrollTop] = React.useState(0);
  const containerRef = React.useRef<HTMLDivElement>(null);

  const handleScroll = throttle((e: React.UIEvent<HTMLDivElement>) => {
    setScrollTop(e.currentTarget.scrollTop);
  }, 16); // 60fps

  const visibleStart = Math.floor(scrollTop / itemHeight);
  const visibleEnd = Math.min(
    visibleStart + Math.ceil(containerRef.current?.clientHeight! / itemHeight) + 2,
    items.length
  );

  const visibleItems = items.slice(visibleStart, visibleEnd);
  const offsetY = visibleStart * itemHeight;
  const totalHeight = items.length * itemHeight;

  return (
    <div
      ref={containerRef}
      className={`virtualized-list ${className || ''}`}
      onScroll={handleScroll}
      style={{ height: '100%', overflow: 'auto' }}
    >
      <div style={{ height: totalHeight, position: 'relative' }}>
        <div
          style={{
            position: 'absolute',
            top: offsetY,
            width: '100%'
          }}
        >
          {visibleItems.map((item, index) => (
            <div key={visibleStart + index} style={{ height: itemHeight }}>
              {renderItem(item, visibleStart + index)}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

/**
 * Performance utilities
 */
export const performanceUtils = {
  /**
   * Debounce function for search inputs
   */
  debounceSearch: debounce((searchFn: Function) => {
    searchFn();
  }, 300),

  /**
   * Throttle scroll events
   */
  throttleScroll: throttle((scrollFn: Function) => {
    scrollFn();
  }, 16),

  /**
   * Measure component render time
   */
  measureRender: (componentName: string, fn: Function) => {
    const start = performance.now();
    const result = fn();
    const end = performance.now();
    console.log(`${componentName} rendered in ${(end - start).toFixed(2)}ms`);
    return result;
  },

  /**
   * Get memory usage (if supported)
   */
  getMemoryUsage: () => {
    if ('memory' in performance) {
      return (performance as any).memory;
    }
    return null;
  },

  /**
   * Clear unused caches
   */
  clearCaches: () => {
    // Clear API cache older than 1 hour
    Object.keys(sessionStorage)
      .filter(key => key.startsWith('axios_cache_'))
      .forEach(key => {
        const cached = JSON.parse(sessionStorage.getItem(key)!);
        if (Date.now() - cached.timestamp > 3600000) {
          sessionStorage.removeItem(key);
        }
      });
  },

  /**
   * Preload critical resources
   */
  preloadCriticalResources: () => {
    // Preload fonts
    const fonts = [
      '/fonts/inter-var.woff2',
      '/fonts/inter-bold.woff2'
    ];

    fonts.forEach(font => {
      const link = document.createElement('link');
      link.rel = 'preload';
      link.as = 'font';
      link.href = font;
      link.crossOrigin = 'anonymous';
      document.head.appendChild(link);
    });
  }
};

// Initialize performance monitoring
if (typeof window !== 'undefined') {
  // Track page load metrics
  window.addEventListener('load', () => {
    setTimeout(() => {
      const navigation = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
      const paint = performance.getEntriesByType('paint');

      console.log('Page Load Metrics:', {
        domContentLoaded: navigation.domContentLoadedEventEnd - navigation.domContentLoadedEventStart,
        loadComplete: navigation.loadEventEnd - navigation.loadEventStart,
        firstPaint: paint.find(p => p.name === 'first-paint')?.startTime,
        firstContentfulPaint: paint.find(p => p.name === 'first-contentful-paint')?.startTime
      });
    }, 0);
  });

  // Clear caches periodically
  setInterval(performanceUtils.clearCaches, 300000); // Every 5 minutes
}