import React, { useState, useEffect } from 'react';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import Container from '@mui/material/Container';
import Box from '@mui/material/Box';
import Grid from '@mui/material/Grid';
import Paper from '@mui/material/Paper';
import Typography from '@mui/material/Typography';

// Import components
import DownloadQueue from './components/DownloadQueue';
import RecentDownloads from './components/RecentDownloads';
import UploadNZB from './components/UploadNZB';
import SystemStatus from './components/SystemStatus';

// Import types and services
import { Download } from './types/api';
import * as api from './services/api';

// Create MUI theme
const theme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: '#90caf9',
    },
    secondary: {
      main: '#f48fb1',
    },
    background: {
      default: '#121212',
      paper: '#1e1e1e',
    },
  },
});

function App() {
  const [downloads, setDownloads] = useState<Download[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchDownloads = async () => {
    try {
      const data = await api.getDownloads();
      setDownloads(data);
      setError(null);
    } catch (err) {
      setError('Failed to fetch downloads');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDownloads();
    // Set up polling interval
    const interval = setInterval(fetchDownloads, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleUpload = async (file: File) => {
    try {
      await api.downloadNZB(file);
      fetchDownloads(); // Refresh the downloads list
    } catch (err) {
      setError('Failed to upload NZB file');
    }
  };

  const handlePause = async (id: number) => {
    try {
      await api.pauseDownload(id);
      fetchDownloads();
    } catch (err) {
      setError('Failed to pause download');
    }
  };

  const handleResume = async (id: number) => {
    try {
      await api.resumeDownload(id);
      fetchDownloads();
    } catch (err) {
      setError('Failed to resume download');
    }
  };

  const handleCancel = async (id: number) => {
    try {
      await api.cancelDownload(id);
      fetchDownloads();
    } catch (err) {
      setError('Failed to cancel download');
    }
  };

  const handleRetry = async (id: number) => {
    try {
      await api.retryDownload(id);
      fetchDownloads();
    } catch (err) {
      setError('Failed to retry download');
    }
  };

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Box sx={{ flexGrow: 1, height: '100vh', overflow: 'hidden' }}>
        <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
          <Grid container spacing={3}>
            {/* Header */}
            <Grid item xs={12}>
              <Paper sx={{ p: 2, display: 'flex', alignItems: 'center' }}>
                <Typography component="h1" variant="h4" color="primary">
                  Media Downloader
                </Typography>
              </Paper>
            </Grid>

            {/* System Status */}
            <Grid item xs={12}>
              <SystemStatus />
            </Grid>

            {/* Upload NZB */}
            <Grid item xs={12}>
              <UploadNZB onUpload={handleUpload} />
            </Grid>

            {/* Active Downloads */}
            <Grid item xs={12}>
              <DownloadQueue
                downloads={downloads.filter(d => d.status === 'downloading' || d.status === 'queued')}
                onPause={handlePause}
                onResume={handleResume}
                onCancel={handleCancel}
              />
            </Grid>

            {/* Recent Downloads */}
            <Grid item xs={12}>
              <RecentDownloads
                downloads={downloads.filter(d => d.status === 'completed' || d.status === 'failed')}
                onRetry={handleRetry}
              />
            </Grid>
          </Grid>
        </Container>
      </Box>
    </ThemeProvider>
  );
}

export default App;
