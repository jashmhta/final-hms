import '@testing-library/jest-dom'
import 'jest-canvas-mock'
import '@emotion/jest'

// Global setup for testing
global.ResizeObserver = class ResizeObserver {
  constructor(callback) {}
  disconnect() {}
  observe(element, options) {}
  unobserve(element) {}
}

// Mock window.matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: jest.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: jest.fn(), // Deprecated
    removeListener: jest.fn(), // Deprecated
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    dispatchEvent: jest.fn(),
  })),
})

// Mock IntersectionObserver
global.IntersectionObserver = class IntersectionObserver {
  constructor(callback) {}
  disconnect() {}
  observe(element) {}
  unobserve(element) {}
}

// Mock window.scrollTo
Object.defineProperty(window, 'scrollTo', {
  value: jest.fn(),
})

// Mock window.scrollTo with smooth scrolling
Object.defineProperty(window, 'scrollTo', {
  value: jest.fn((options) => {
    if (typeof options === 'object' && options.behavior === 'smooth') {
      // Simulate smooth scrolling completion
      setTimeout(() => {
        if (typeof options.top === 'number') {
          window.scrollY = options.top
        }
      }, 100)
    }
  }),
})

// Mock performance API
Object.defineProperty(window, 'performance', {
  writable: true,
  value: {
    ...window.performance,
    now: jest.fn(() => Date.now()),
    getEntriesByType: jest.fn(() => []),
    mark: jest.fn(),
    measure: jest.fn(),
    clearMarks: jest.fn(),
    clearMeasures: jest.fn(),
  },
})

// Mock performance.memory for Chrome
if (typeof window.performance !== 'undefined') {
  Object.defineProperty(window.performance, 'memory', {
    value: {
      usedJSHeapSize: 1000000,
      totalJSHeapSize: 2000000,
      jsHeapSizeLimit: 5000000,
    },
  })
}

// Mock fetch API
global.fetch = jest.fn(() =>
  Promise.resolve({
    ok: true,
    json: () => Promise.resolve({}),
    text: () => Promise.resolve(''),
    blob: () => Promise.resolve(new Blob()),
  })
)

// Mock URL.createObjectURL
global.URL.createObjectURL = jest.fn(() => 'mocked-url')
global.URL.revokeObjectURL = jest.fn()

// Mock window.getComputedStyle for style testing
Object.defineProperty(window, 'getComputedStyle', {
  value: jest.fn(() => ({
    getPropertyValue: (prop) => {
      const styleMap = {
        'font-family': 'Inter, sans-serif',
        'font-size': '16px',
        'font-weight': '400',
        'line-height': '1.5',
        'color': '#000000',
        'background-color': '#ffffff',
        'padding': '12px 24px',
        'margin': '8px',
        'border': '1px solid #e0e0e0',
        'border-radius': '8px',
        'display': 'flex',
        'flex-direction': 'row',
        'justify-content': 'center',
        'align-items': 'center',
        'text-align': 'left',
        'width': '100%',
        'height': 'auto',
        'opacity': '1',
        'transform': 'none',
        'transition': 'all 0.2s ease-in-out',
        'box-shadow': '0 2px 4px rgba(0,0,0,0.1)',
      }
      return styleMap[prop] || ''
    },
  })),
})

// Mock window.scrollY and related properties
Object.defineProperty(window, 'scrollY', {
  value: 0,
  writable: true,
})

Object.defineProperty(window, 'innerWidth', {
  value: 1024,
  writable: true,
})

Object.defineProperty(window, 'innerHeight', {
  value: 768,
  writable: true,
})

// Mock window.resizeTo for responsive testing
Object.defineProperty(window, 'resizeTo', {
  value: jest.fn((width, height) => {
    Object.defineProperty(window, 'innerWidth', {
      value: width,
      writable: true,
    })
    Object.defineProperty(window, 'innerHeight', {
      value: height,
      writable: true,
    })
    // Trigger resize event
    window.dispatchEvent(new Event('resize'))
  }),
})

// Mock screen reader APIs
Object.defineProperty(document, 'activeElement', {
  value: document.body,
  writable: true,
})