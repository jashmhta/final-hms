import '@testing-library/jest-dom'
global.ResizeObserver = class ResizeObserver {
  constructor(callback) {}
  disconnect() {}
  observe(element, options) {}
  unobserve(element) {}
}