import React from 'react'
import { render, screen } from '@testing-library/react'
import '@testing-library/jest-dom'

test('Simple test to validate Jest setup', () => {
  render(<div data-testid="test-div">Hello World</div>)
  expect(screen.getByTestId('test-div')).toBeInTheDocument()
  expect(screen.getByText('Hello World')).toBeInTheDocument()
})