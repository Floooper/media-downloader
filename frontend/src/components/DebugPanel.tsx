import React, { useState } from 'react';
import { Paper, Typography, Button, Grid } from '@mui/material';
import { LogViewer } from './LogViewer';
import logger from '../services/logging';
import * as api from '../services/api';

const DebugPanel: React.FC = () => {
  const [loading, setLoading] = useState(false);

  const handleClearLogs = () => {
    logger.clearLogs();
  };

  const handleTestConnection = async () => {
    setLoading(true);
    try {
      const status = await api.getSystemStatus();
      logger.info('Connection test successful', status);
    } catch (error) {
      logger.error('Connection test failed', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Paper sx={{ p: 2 }}>
      <Typography variant="h6" gutterBottom>
        Debug Panel
      </Typography>
      
      <Grid container spacing={2} sx={{ mb: 2 }}>
        <Grid item>
          <Button 
            variant="contained" 
            onClick={handleTestConnection}
            disabled={loading}
          >
            Test Connection
          </Button>
        </Grid>
        <Grid item>
          <Button 
            variant="outlined" 
            onClick={handleClearLogs}
            disabled={loading}
          >
            Clear Logs
          </Button>
        </Grid>
      </Grid>

      <LogViewer />
    </Paper>
  );
};

export default DebugPanel;
