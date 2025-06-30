import React from 'react';
import {
  ListItem,
  ListItemText,
  IconButton,
  LinearProgress,
  Box,
  Typography,
} from '@mui/material';
import {
  Pause as PauseIcon,
  PlayArrow as PlayArrowIcon,
  Cancel as CancelIcon,
} from '@mui/icons-material';
import { Download } from '../types/api';

interface DownloadItemRowProps {
  download: Download;
  onPause: () => void;
  onResume: () => void;
  onCancel: () => void;
}

const DownloadItemRow: React.FC<DownloadItemRowProps> = ({
  download,
  onPause,
  onResume,
  onCancel,
}) => {
  const formatSize = (bytes: number) => {
    const sizes = ['B', 'KB', 'MB', 'GB'];
    if (bytes === 0) return '0 B';
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return `${(bytes / Math.pow(1024, i)).toFixed(2)} ${sizes[i]}`;
  };

  return (
    <ListItem
      secondaryAction={
        <Box>
          <IconButton
            edge="end"
            aria-label={download.status === 'downloading' ? 'pause' : 'resume'}
            onClick={download.status === 'downloading' ? onPause : onResume}
          >
            {download.status === 'downloading' ? <PauseIcon /> : <PlayArrowIcon />}
          </IconButton>
          <IconButton edge="end" aria-label="cancel" onClick={onCancel}>
            <CancelIcon />
          </IconButton>
        </Box>
      }
    >
      <ListItemText
        primary={download.name}
        secondary={
          <Box sx={{ width: '100%' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
              <Typography variant="body2" color="text.secondary">
                {formatSize(download.size)} • {Math.round(download.progress)}%
              </Typography>
            </Box>
            <LinearProgress
              variant="determinate"
              value={download.progress}
              sx={{ height: 8, borderRadius: 4 }}
            />
          </Box>
        }
      />
    </ListItem>
  );
};

export default DownloadItemRow;
