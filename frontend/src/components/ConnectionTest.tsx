import React, { useState, useEffect } from 'react';
import { Box, Typography, Button, Chip, Stack, CircularProgress } from '@mui/material';
import { Refresh as RefreshIcon, CheckCircle as CheckIcon, Error as ErrorIcon } from '@mui/icons-material';

const ConnectionTest: React.FC = () => {
  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading');
  const [message, setMessage] = useState('Checking connection...');

  const testConnection = async () => {
    setStatus('loading');
    setMessage('Testing connection...');
    
    try {
      const response = await fetch('/api/system/info');
      if (response.ok) {
        setStatus('success');
        setMessage('Backend connection successful');
      } else {
        setStatus('error');
        setMessage(`Connection failed: ${response.status}`);
      }
    } catch (error) {
      setStatus('error');
      setMessage('Connection failed: Unable to reach backend');
    }
  };

  useEffect(() => {
    testConnection();
  }, []);

  return (
    <Box>
      <Stack direction="row" spacing={2} alignItems="center" sx={{ mb: 2 }}>
        <Typography variant="h6">Connection Status</Typography>
        <Button
          size="small"
          startIcon={<RefreshIcon />}
          onClick={testConnection}
          disabled={status === 'loading'}
        >
          Test
        </Button>
      </Stack>
      
      <Stack direction="row" spacing={2} alignItems="center">
        {status === 'loading' && <CircularProgress size={20} />}
        {status === 'success' && <CheckIcon color="success" />}
        {status === 'error' && <ErrorIcon color="error" />}
        
        <Chip
          label={message}
          color={status === 'success' ? 'success' : status === 'error' ? 'error' : 'default'}
          variant={status === 'loading' ? 'outlined' : 'filled'}
        />
      </Stack>
    </Box>
  );
};

export default ConnectionTest;
