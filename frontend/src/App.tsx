import React from 'react';
import ErrorBoundary from './components/ErrorBoundary';
import LogViewer from './components/LogViewer';
import { ThemeProvider } from './contexts/theme';
import { Box, Container, CssBaseline } from '@mui/material';
import { logInfo } from './utils/logger';

function App() {
  // Log app initialization
  React.useEffect(() => {
    logInfo('Application initialized', {
      version: import.meta.env.VITE_APP_VERSION || '1.0.0',
      environment: import.meta.env.MODE,
      buildTime: new Date().toISOString(),
    });
  }, []);

  return (
    <ErrorBoundary>
      <ThemeProvider>
        <CssBaseline />
        <Container>
          <Box sx={{ my: 4 }}>
            {/* Your existing app content */}
          </Box>
        </Container>
        <LogViewer />
      </ThemeProvider>
    </ErrorBoundary>
  );
}

export default App;
