import React, { useCallback } from 'react';
import { Paper, Typography, Box } from '@mui/material';
import { useDropzone } from 'react-dropzone';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';

interface UploadNZBProps {
  onUpload: (file: File) => void;
}

const UploadNZB: React.FC<UploadNZBProps> = ({ onUpload }) => {
  const onDrop = useCallback(
    (acceptedFiles: File[]) => {
      if (acceptedFiles.length > 0) {
        onUpload(acceptedFiles[0]);
      }
    },
    [onUpload]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/x-nzb': ['.nzb'],
    },
    multiple: false,
  });

  return (
    <Paper sx={{ p: 2 }}>
      <Box
        {...getRootProps()}
        sx={{
          border: '2px dashed',
          borderColor: isDragActive ? 'primary.main' : 'grey.500',
          borderRadius: 1,
          p: 3,
          textAlign: 'center',
          cursor: 'pointer',
          '&:hover': {
            borderColor: 'primary.main',
            bgcolor: 'action.hover',
          },
        }}
      >
        <input {...getInputProps()} />
        <CloudUploadIcon sx={{ fontSize: 48, color: 'primary.main', mb: 2 }} />
        <Typography variant="h6" gutterBottom>
          Drop NZB file here
        </Typography>
        <Typography variant="body2" color="text.secondary">
          or click to select file
        </Typography>
      </Box>
    </Paper>
  );
};

export default UploadNZB;
