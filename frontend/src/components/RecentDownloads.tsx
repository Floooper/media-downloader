import React from 'react';
import {
  Paper,
  Typography,
  List,
  ListItem,
  ListItemText,
  IconButton,
  Chip,
} from '@mui/material';
import { Refresh as RefreshIcon } from '@mui/icons-material';
import { Download } from '../types/api';

interface RecentDownloadsProps {
  downloads: Download[];
  onRetry: (id: number) => void;
}

const RecentDownloads: React.FC<RecentDownloadsProps> = ({ downloads, onRetry }) => {
  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'success';
      case 'failed':
        return 'error';
      default:
        return 'default';
    }
  };

  return (
    <Paper sx={{ p: 2 }}>
      <Typography variant="h6" gutterBottom>
        Recent Downloads
      </Typography>
      <List>
        {downloads.map((download) => (
          <ListItem
            key={download.id}
            secondaryAction={
              download.status === 'failed' && (
                <IconButton
                  edge="end"
                  aria-label="retry"
                  onClick={() => onRetry(download.id)}
                >
                  <RefreshIcon />
                </IconButton>
              )
            }
          >
            <ListItemText
              primary={download.name}
              secondary={
                <>
                  {formatDate(download.updated_at)}
                  <Chip
                    label={download.status}
                    color={getStatusColor(download.status)}
                    size="small"
                    sx={{ ml: 1 }}
                  />
                </>
              }
            />
          </ListItem>
        ))}
        {downloads.length === 0 && (
          <Typography variant="body2" color="text.secondary" sx={{ p: 2 }}>
            No recent downloads
          </Typography>
        )}
      </List>
    </Paper>
  );
};

export default RecentDownloads;
