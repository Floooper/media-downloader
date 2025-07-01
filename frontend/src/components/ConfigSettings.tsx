import React, { useState, useEffect } from 'react';
import { 
  Box, 
  Typography, 
  TextField, 
  Button, 
  Grid, 
  Card, 
  CardContent, 
  CardHeader,
  Alert,
  Stack,
  CircularProgress
} from '@mui/material';
import { Save as SaveIcon, Refresh as RefreshIcon } from '@mui/icons-material';

interface ConfigData {
  api_host: string;
  api_port: number;
  default_download_path: string;
  max_concurrent_downloads: number;
  readarr_url?: string;
  sonarr_url?: string;
  radarr_url?: string;
}

const ConfigSettings: React.FC = () => {
  const [config, setConfig] = useState<ConfigData>({
    api_host: 'localhost',
    api_port: 8000,
    default_download_path: '/downloads',
    max_concurrent_downloads: 5,
  });
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState('');

  const loadConfig = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/config/');
      if (response.ok) {
        const data = await response.json();
        setConfig(data);
        setMessage('Configuration loaded successfully');
      } else {
        setMessage('Failed to load configuration');
      }
    } catch (error) {
      console.error('Error loading config:', error);
      setMessage('Error loading configuration');
    } finally {
      setLoading(false);
    }
  };

  const saveConfig = async () => {
    setSaving(true);
    try {
      const response = await fetch('/api/config/', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(config),
      });
      
      if (response.ok) {
        setMessage('Configuration saved successfully');
      } else {
        setMessage('Failed to save configuration');
      }
    } catch (error) {
      console.error('Error saving config:', error);
      setMessage('Error saving configuration');
    } finally {
      setSaving(false);
    }
  };

  useEffect(() => {
    void loadConfig();
  }, []);

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" p={3}>
        <CircularProgress />
        <Typography sx={{ ml: 2 }}>Loading configuration...</Typography>
      </Box>
    );
  }

  return (
    <Box>
      <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 3 }}>
        <Typography variant="h5">Configuration Settings</Typography>
        <Stack direction="row" spacing={2}>
          <Button
            startIcon={<RefreshIcon />}
            onClick={() => void loadConfig()}
            disabled={loading}
          >
            Reload
          </Button>
          <Button
            variant="contained"
            startIcon={<SaveIcon />}
            onClick={() => void saveConfig()}
            disabled={saving}
          >
            {saving ? 'Saving...' : 'Save'}
          </Button>
        </Stack>
      </Stack>

      {message && (
        <Alert severity={message.includes('successfully') ? 'success' : 'error'} sx={{ mb: 3 }}>
          {message}
        </Alert>
      )}

      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardHeader title="Server Settings" />
            <CardContent>
              <Stack spacing={3}>
                <TextField
                  fullWidth
                  label="API Host"
                  value={config.api_host}
                  onChange={(e) => setConfig({ ...config, api_host: e.target.value })}
                />
                <TextField
                  fullWidth
                  label="API Port"
                  type="number"
                  value={config.api_port}
                  onChange={(e) => setConfig({ ...config, api_port: parseInt(e.target.value) || 8000 })}
                />
                <TextField
                  fullWidth
                  label="Default Download Path"
                  value={config.default_download_path}
                  onChange={(e) => setConfig({ ...config, default_download_path: e.target.value })}
                />
                <TextField
                  fullWidth
                  label="Max Concurrent Downloads"
                  type="number"
                  value={config.max_concurrent_downloads}
                  onChange={(e) => setConfig({ ...config, max_concurrent_downloads: parseInt(e.target.value) || 5 })}
                />
              </Stack>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card>
            <CardHeader title="Media Manager Integration" />
            <CardContent>
              <Stack spacing={3}>
                <TextField
                  fullWidth
                  label="Readarr URL"
                  placeholder="http://localhost:8787"
                  value={config.readarr_url || ''}
                  onChange={(e) => setConfig({ ...config, readarr_url: e.target.value })}
                />
                <TextField
                  fullWidth
                  label="Sonarr URL"
                  placeholder="http://localhost:8989"
                  value={config.sonarr_url || ''}
                  onChange={(e) => setConfig({ ...config, sonarr_url: e.target.value })}
                />
                <TextField
                  fullWidth
                  label="Radarr URL"
                  placeholder="http://localhost:7878"
                  value={config.radarr_url || ''}
                  onChange={(e) => setConfig({ ...config, radarr_url: e.target.value })}
                />
              </Stack>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12}>
          <Card>
            <CardHeader title="System Information" />
            <CardContent>
              <Typography variant="body2" color="textSecondary">
                Media Downloader - MUI Version
              </Typography>
              <Typography variant="body2" color="textSecondary">
                Backend API: http://{config.api_host}:{config.api_port}
              </Typography>
              <Typography variant="body2" color="textSecondary">
                Download Path: {config.default_download_path}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default ConfigSettings;
