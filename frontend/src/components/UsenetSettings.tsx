import React, { useState } from 'react';
import { 
  Typography, 
  TextField, 
  Button, 
  Box,
  Grid,
  Card,
  CardContent,
  CardHeader,
  Stack,
  FormGroup,
  FormControlLabel,
  Switch,
  IconButton,
  Tooltip,
  Alert,
} from '@mui/material';
import { Save as SaveIcon, AddCircle as AddIcon } from '@mui/icons-material';

interface ServerConfig {
  name: string;
  host: string;
  port: number;
  username: string;
  password: string;
  ssl: boolean;
  connections: number;
}

const UsenetSettings: React.FC = () => {
  const [config, setConfig] = useState<ServerConfig>({
    name: 'Primary Server',
    host: '',
    port: 119,
    username: '',
    password: '',
    ssl: false,
    connections: 5
  });
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState('');

  const handleSave = async () => {
    setSaving(true);
    try {
      const response = await fetch('/api/usenet/config', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(config),
      });
      
      if (response.ok) {
        setMessage('Settings saved successfully');
      } else {
        setMessage('Failed to save settings');
      }
    } catch (error) {
      console.error('Error saving settings:', error);
      setMessage('Error saving settings');
    } finally {
      setSaving(false);
    }
  };

  return (
    <Box sx={{ maxWidth: 800, mx: 'auto', mt: 2 }}>
      <Stack spacing={3}>
        <Stack direction="row" justifyContent="space-between" alignItems="center">
          <Typography variant="h5">Usenet Settings</Typography>
          <Button
            variant="contained"
            startIcon={<SaveIcon />}
            onClick={handleSave}
            disabled={saving}
          >
            {saving ? 'Saving...' : 'Save Settings'}
          </Button>
        </Stack>

        {message && (
          <Alert severity={message.includes('successfully') ? 'success' : 'error'}>
            {message}
          </Alert>
        )}

        <Card>
          <CardHeader 
            title="Server Settings"
            action={
              <Tooltip title="Add Additional Server">
                <IconButton>
                  <AddIcon />
                </IconButton>
              </Tooltip>
            }
          />
          <CardContent>
            <Grid container spacing={3}>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Server Name"
                  value={config.name}
                  onChange={(e) => setConfig({ ...config, name: e.target.value })}
                />
              </Grid>
              <Grid item xs={12} sm={8}>
                <TextField
                  fullWidth
                  label="Host"
                  value={config.host}
                  onChange={(e) => setConfig({ ...config, host: e.target.value })}
                />
              </Grid>
              <Grid item xs={12} sm={4}>
                <TextField
                  fullWidth
                  label="Port"
                  type="number"
                  value={config.port}
                  onChange={(e) => setConfig({ ...config, port: parseInt(e.target.value) || 119 })}
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="Username"
                  value={config.username}
                  onChange={(e) => setConfig({ ...config, username: e.target.value })}
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="Password"
                  type="password"
                  value={config.password}
                  onChange={(e) => setConfig({ ...config, password: e.target.value })}
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <FormGroup>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={config.ssl}
                        onChange={(e) => setConfig({ ...config, ssl: e.target.checked })}
                      />
                    }
                    label="Use SSL"
                  />
                </FormGroup>
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="Max Connections"
                  type="number"
                  value={config.connections}
                  onChange={(e) => setConfig({ ...config, connections: parseInt(e.target.value) || 5 })}
                />
              </Grid>
            </Grid>
          </CardContent>
        </Card>

        <Card>
          <CardHeader title="Connection Info" />
          <CardContent>
            <Grid container spacing={2}>
              <Grid item xs={12} sm={4}>
                <Typography variant="subtitle2" color="textSecondary">
                  Status
                </Typography>
                <Typography>Connected</Typography>
              </Grid>
              <Grid item xs={12} sm={4}>
                <Typography variant="subtitle2" color="textSecondary">
                  Active Connections
                </Typography>
                <Typography>3/5</Typography>
              </Grid>
              <Grid item xs={12} sm={4}>
                <Typography variant="subtitle2" color="textSecondary">
                  Speed
                </Typography>
                <Typography>2.5 MB/s</Typography>
              </Grid>
            </Grid>
          </CardContent>
        </Card>
      </Stack>
    </Box>
  );
};

export default UsenetSettings;
