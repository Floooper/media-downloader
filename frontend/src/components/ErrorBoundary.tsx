import React, { Component, ReactNode } from 'react';
import {
    Alert,
    Button,
    Stack,
    Text,
    Title,
    Code,
    Container,
    Paper,
} from '@mantine/core';
import { IconAlertTriangle, IconRefresh } from '@tabler/icons-react';

interface Props {
    children: ReactNode;
}

interface State {
    hasError: boolean;
    error?: Error;
    errorInfo?: string;
}

export class ErrorBoundary extends Component<Props, State> {
    constructor(props: Props) {
        super(props);
        this.state = { hasError: false };
    }

    static getDerivedStateFromError(error: Error): State {
        return {
            hasError: true,
            error,
        };
    }

    componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
        console.error('ErrorBoundary caught an error:', error, errorInfo);
        this.setState({
            error,
            errorInfo: errorInfo.componentStack,
        });
    }

    handleReset = () => {
        this.setState({ hasError: false, error: undefined, errorInfo: undefined });
        window.location.reload();
    };

    render() {
        if (this.state.hasError) {
            return (
                <Container size="md" py="xl">
                    <Paper p="xl" radius="md" withBorder>
                        <Stack spacing="md" align="center">
                            <IconAlertTriangle size={48} c="red" />
                            <Title order={2} c="red">
                                Something went wrong
                            </Title>
                            
                            <Text align="center" c="dimmed">
                                An unexpected error occurred. Please try refreshing the page or contact support if the problem persists.
                            </Text>

                            {this.state.error && (
                                <Alert c="red" icon={<IconAlertTriangle size={16} />}>
                                    <Text fw={500}>Error Details:</Text>
                                    <Code>{this.state.error.message}</Code>
                                </Alert>
                            )}

                            <Button
                                leftSection={<IconRefresh size={16} />}
                                onClick={this.handleReset}
                                c="blue"
                            >
                                Refresh Page
                            </Button>

                            {process.env.NODE_ENV === 'development' && this.state.errorInfo && (
                                <details style={{ width: '100%' }}>
                                    <summary>Stack Trace (Development Only)</summary>
                                    <Code block mt="sm">
                                        {this.state.errorInfo}
                                    </Code>
                                </details>
                            )}
                        </Stack>
                    </Paper>
                </Container>
            );
        }

        return this.props.children;
    }
}

