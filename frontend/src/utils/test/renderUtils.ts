import { render as rtlRender } from '@testing-library/react';
import React from 'react';
import { TestProviders } from './providers/TestProviders';

export function render(ui: React.ReactElement, options = {}) {
  return rtlRender(ui, { wrapper: TestProviders, ...options });
}
