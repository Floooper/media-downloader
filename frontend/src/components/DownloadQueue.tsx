import React from 'react';
import { Paper, Typography, List } from '@mui/material';
import { Download } from '../types/api';
import DownloadItemRow from './DownloadItemRow';

interface DownloadQueueProps {
  downloads: Download[];
  onPause: (id: number) => void;
  onResume: (id: number) => void;
  onCancel: (id: number) => void;
}

const DownloadQueue: React.FC<DownloadQueueProps> = ({ downloads, onPause, onResume, onCancel }) => {
  return (
    <Paper sx={{ p: 2 }}>
      <Typography variant="h6" gutterBottom>
        Active Downloads
      </Typography>
      <List>
        {downloads.map((download) => (
          <DownloadItemRow
            key={download.id}
            download={download}
            onPause={() => onPause(download.id)}
            onResume={() => onResume(download.id)}
            onCancel={() => onCancel(download.id)}
          />
        ))}
        {downloads.length === 0 && (
          <Typography variant="body2" color="text.secondary" sx={{ p: 2 }}>
            No active downloads
          </Typography>
        )}
      </List>
    </Paper>
  );
};

export default DownloadQueue;
