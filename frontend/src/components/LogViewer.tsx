import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
} from '@mui/material';
import {
  BugReport as BugIcon,
  Clear as ClearIcon,
  FilterList as FilterIcon,
} from '@mui/icons-material';
import logger from '../utils/logger';

type LogLevel = 'debug' | 'info' | 'warn' | 'error';

interface LogData {
  message?: string;
  stack?: string;
  source?: string;
  line?: number;
  column?: number;
  reason?: unknown;
  [key: string]: unknown;
}

interface LogEntry {
  timestamp: string;
  level: LogLevel;
  message: string;
  data?: LogData;
  stack?: string;
}

type LogLevelColor = 'error' | 'warning' | 'info' | 'default';

const LogViewer: React.FC = () => {
  const [open, setOpen] = useState(false);
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [filter, setFilter] = useState<LogLevel[]>(['error', 'warn']);
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);

  useEffect(() => {
    const updateLogs = () => {
      setLogs(logger.getLogs());
    };

    // Update logs every second
    const interval = setInterval(updateLogs, 1000);
    updateLogs();

    return () => clearInterval(interval);
  }, []);

  const filteredLogs = logs.filter((log) => filter.includes(log.level));
  const displayedLogs = filteredLogs
    .slice()
    .reverse()
    .slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage);

  const handleClearLogs = () => {
    logger.clearLogs();
    setLogs([]);
  };

  const handleFilterChange = (level: LogLevel) => {
    setFilter((prev) =>
      prev.includes(level)
        ? prev.filter((l) => l !== level)
        : [...prev, level]
    );
  };

  const getLevelColor = (level: LogLevel): LogLevelColor => {
    switch (level) {
      case 'error':
        return 'error';
      case 'warn':
        return 'warning';
      case 'info':
        return 'info';
      case 'debug':
        return 'default';
    }
  };

  const formatData = (data: LogData | undefined): string => {
    if (!data) return '';
    try {
      return typeof data === 'string'
        ? data
        : JSON.stringify(data, null, 2);
    } catch {
      return String(data);
    }
  };

  return (
    <>
      {process.env.NODE_ENV === 'development' && (
        <IconButton
          sx={{
            position: 'fixed',
            bottom: 16,
            right: 16,
            backgroundColor: 'background.paper',
          }}
          onClick={() => setOpen(true)}
        >
          <BugIcon />
        </IconButton>
      )}

      <Dialog
        open={open}
        onClose={() => setOpen(false)}
        maxWidth="lg"
        fullWidth
      >
        <DialogTitle>
          <Box display="flex" alignItems="center" justifyContent="space-between">
            <Typography variant="h6">Log Viewer</Typography>
            <Box>
              <IconButton onClick={() => setOpen(false)}>
                <ClearIcon />
              </IconButton>
            </Box>
          </Box>
        </DialogTitle>

        <DialogContent>
          <Box mb={2} display="flex" alignItems="center" gap={1}>
            <FilterIcon />
            {(['error', 'warn', 'info', 'debug'] as const).map((level) => (
              <Chip
                key={level}
                label={level}
                color={getLevelColor(level)}
                variant={filter.includes(level) ? 'filled' : 'outlined'}
                onClick={() => handleFilterChange(level)}
                size="small"
              />
            ))}
            <Box flex={1} />
            <IconButton onClick={handleClearLogs}>
              <ClearIcon />
            </IconButton>
          </Box>

          <TableContainer component={Paper} variant="outlined">
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>Time</TableCell>
                  <TableCell>Level</TableCell>
                  <TableCell>Message</TableCell>
                  <TableCell>Data</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {displayedLogs.map((log, index) => (
                  <TableRow key={`${log.timestamp}-${index}`}>
                    <TableCell>
                      {new Date(log.timestamp).toLocaleTimeString()}
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={log.level}
                        color={getLevelColor(log.level)}
                        size="small"
                      />
                    </TableCell>
                    <TableCell>{log.message}</TableCell>
                    <TableCell>
                      <Typography
                        variant="body2"
                        component="pre"
                        sx={{
                          whiteSpace: 'pre-wrap',
                          margin: 0,
                          fontFamily: 'monospace',
                        }}
                      >
                        {formatData(log.data)}
                        {log.stack && (
                          <>
                            {'\n\nStack Trace:\n'}
                            {log.stack}
                          </>
                        )}
                      </Typography>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>

          <TablePagination
            component="div"
            count={filteredLogs.length}
            page={page}
            onPageChange={(_, newPage) => setPage(newPage)}
            rowsPerPage={rowsPerPage}
            onRowsPerPageChange={(event) => {
              setRowsPerPage(parseInt(event.target.value, 10));
              setPage(0);
            }}
          />
        </DialogContent>
      </Dialog>
    </>
  );
};

export default LogViewer;
