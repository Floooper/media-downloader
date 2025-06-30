import React, { Component, ReactNode } from 'react';
import { Alert, Box, Button, Typography } from '@mui/material';
import { Refresh as RefreshIcon } from '@mui/icons-material';

interface Props {
    children: ReactNode;
}

interface State {
    hasError: boolean;
    error?: Error;
}

export class SimpleErrorBoundary extends Component<Props, State> {
    constructor(props: Props) {
        super(props);
        this.state = { hasError: false };
    }

    static getDerivedStateFromError(error: Error): State {
        return { hasError: true, error };
    }

    componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
        console.error('🚨 Error Boundary caught an error:', error, errorInfo);
    }

    render() {
        if (this.state.hasError) {
            return (
                <Box sx={{ p: 3 }}>
                    <Alert severity="error">
                        <Typography variant="h6" sx={{ mb: 1 }}>
                            Something went wrong!
                        </Typography>
                        <Typography variant="body2" sx={{ mb: 2 }}>
                            {this.state.error?.message || 'An unexpected error occurred'}
                        </Typography>
                        <Button
                            variant="outlined"
                            startIcon={<RefreshIcon />}
                            onClick={() => window.location.reload()}
                        >
                            Reload Page
                        </Button>
                    </Alert>
                </Box>
            );
        }

        return this.props.children;
    }
}
