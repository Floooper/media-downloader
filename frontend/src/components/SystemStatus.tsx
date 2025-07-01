import React, { useState, useEffect } from 'react';
import {
  Paper,
  Typography,
  Grid,
  Box,
  CircularProgress,
  Tooltip,
} from '@mui/material';
import {
  Speed as SpeedIcon,
  CloudQueue as CloudIcon,
  Memory as MemoryIcon,
  Storage as StorageIcon,
} from '@mui/icons-material';
import { getSystemStatus } from '../services/api';
import { SystemStatusData } from '../types/system-status';

const SystemStatus: React.FC = () => {
  const [status, setStatus] = useState<SystemStatusData | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const data = await getSystemStatus();
        setStatus(data);
        setError(null);
      } catch {
        setError('Failed to fetch system status');
      }
    };

    void fetchStatus();
    const interval = setInterval(fetchStatus, 5000);
    return () => clearInterval(interval);
  }, []);

  if (error) {
    return (
      <Paper sx={{ p: 2 }}>
        <Typography color="error">{error}</Typography>
      </Paper>
    );
  }

  if (!status) {
    return (
      <Paper sx={{ p: 2, display: 'flex', justifyContent: 'center' }}>
        <CircularProgress />
      </Paper>
    );
  }

  const formatSpeed = (bytesPerSecond: number): string => {
    if (bytesPerSecond < 1024) return `${bytesPerSecond} B/s`;
    if (bytesPerSecond < 1024 * 1024) return `${(bytesPerSecond / 1024).toFixed(1)} KB/s`;
    return `${(bytesPerSecond / (1024 * 1024)).toFixed(1)} MB/s`;
  };

  return (
    <Paper sx={{ p: 2 }}>
      <Grid container spacing={3}>
        <Grid item xs={3}>
          <Tooltip title="Usenet Connection Status">
            <Box sx={{ textAlign: 'center' }}>
              <CloudIcon
                color={status.usenet.connected ? 'success' : 'error'}
                sx={{ fontSize: 40 }}
              />
              <Typography variant="body2">
                {status.usenet.active_connections}/{status.usenet.max_connections} connections
              </Typography>
            </Box>
          </Tooltip>
        </Grid>
        <Grid item xs={3}>
          <Tooltip title="Download Speed">
            <Box sx={{ textAlign: 'center' }}>
              <SpeedIcon color="primary" sx={{ fontSize: 40 }} />
              <Typography variant="body2">
                {formatSpeed(status.usenet.download_rate)}
              </Typography>
            </Box>
          </Tooltip>
        </Grid>
        <Grid item xs={3}>
          <Tooltip title="Memory Usage">
            <Box sx={{ textAlign: 'center' }}>
              <MemoryIcon color="primary" sx={{ fontSize: 40 }} />
              <Typography variant="body2">
                {status.system.memory_usage.toFixed(1)}%
              </Typography>
            </Box>
          </Tooltip>
        </Grid>
        <Grid item xs={3}>
          <Tooltip title="Disk Usage">
            <Box sx={{ textAlign: 'center' }}>
              <StorageIcon color="primary" sx={{ fontSize: 40 }} />
              <Typography variant="body2">
                {status.system.disk_usage.toFixed(1)}%
              </Typography>
            </Box>
          </Tooltip>
        </Grid>
      </Grid>
    </Paper>
  );
};

export default SystemStatus;
