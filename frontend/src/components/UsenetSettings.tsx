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
  CircularProgress,
  Switch,
  FormControlLabel
} from '@mui/material';
import { 
  Save as SaveIcon, 
  Refresh as RefreshIcon,
  TestTube as TestIcon
} from '@mui/icons-material';

interface UsenetConfig {
  server: string;
  port: number;
  use_ssl: boolean;
  username: string;
  password: string;
  max_connections: number;
  retention_days: number;
  download_rate_limit: number | null;
  max_retries: number;
}

const UsenetSettings: React.FC = () => {
  const [config, setConfig] = useState<UsenetConfig>({
    server: '',
    port: 563,
    use_ssl: true,
    username: '',
    password: '',
    max_connections: 10,
    retention_days: 1500,
    download_rate_limit: null,
    max_retries: 3
  });
  
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState('');

  const loadConfig = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/config/usenet');
      if (response.ok) {
        const data = await response.json();
        setConfig(data);
        setMessage('Configuration loaded successfully');
      } else {
        setMessage('Failed to load configuration');
      }
    } catch (error) {
      setMessage(`Error: ${error}`);
    } finally {
      setLoading(false);
    }
  };

  const saveConfig = async () => {
    setSaving(true);
    try {
      const response = await fetch('/api/config/usenet', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config),
      });
      
      if (response.ok) {
        setMessage('Configuration saved successfully');
      } else {
        setMessage('Failed to save configuration');
      }
    } catch (error) {
      setMessage(`Error: ${error}`);
    } finally {
      setSaving(false);
    }
  };

  useEffect(() => {
    loadConfig();
  }, []);

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" p={4}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        🗞️ Usenet Configuration
      </Typography>
      
      {message && (
        <Alert 
          severity={message.includes('success') ? 'success' : 'error'} 
          sx={{ mb: 3 }}
        >
          {message}
        </Alert>
      )}

      <Card>
        <CardHeader title="Usenet Server Settings" />
        <CardContent>
          <Grid container spacing={3}>
            <Grid item xs={12} md={8}>
              <TextField
                fullWidth
                label="Server"
                value={config.server}
                onChange={(e) => setConfig({...config, server: e.target.value})}
              />
            </Grid>
            
            <Grid item xs={12} md={4}>
              <TextField
                fullWidth
                label="Port"
                type="number"
                value={config.port}
                onChange={(e) => setConfig({...config, port: Number(e.target.value)})}
              />
            </Grid>

            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Username"
                value={config.username}
                onChange={(e) => setConfig({...config, username: e.target.value})}
              />
            </Grid>

            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Password"
                type="password"
                value={config.password}
                onChange={(e) => setConfig({...config, password: e.target.value})}
              />
            </Grid>

            <Grid item xs={12}>
              <FormControlLabel
                control={
                  <Switch
                    checked={config.use_ssl}
                    onChange={(e) => setConfig({...config, use_ssl: e.target.checked})}
                  />
                }
                label="Use SSL"
              />
            </Grid>

            <Grid item xs={12}>
              <Stack direction="row" spacing={2}>
                <Button
                  variant="contained"
                  startIcon={saving ? <CircularProgress size={20} /> : <SaveIcon />}
                  onClick={saveConfig}
                  disabled={saving}
                >
                  {saving ? 'Saving...' : 'Save'}
                </Button>

                <Button
                  variant="outlined"
                  startIcon={<RefreshIcon />}
                  onClick={loadConfig}
                  disabled={saving}
                >
                  Reload
                </Button>
              </Stack>
            </Grid>
          </Grid>
        </CardContent>
      </Card>
    </Box>
  );
};

export default UsenetSettings;
