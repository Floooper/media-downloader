import React from 'react';
import { MantineProvider } from '@mantine/core';

export default function App() {
  return (
    <MantineProvider>
      <div style={{ padding: '20px' }}>
        <h1>Test App - White Screen Debug</h1>
        <p>If you can see this, the basic React app is working.</p>
        <p>Current time: {new Date().toLocaleString()}</p>
      </div>
    </MantineProvider>
  );
}
