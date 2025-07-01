import React from 'react';
import { ErrorState } from '../ui/EmptyState';

interface ErrorBoundaryProps {
  children: React.ReactNode;
  fallback?: React.ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends React.Component<
  ErrorBoundaryProps,
  ErrorBoundaryState
> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('Error caught by error boundary:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <ErrorState
          error={this.state.error}
          onRetry={() => this.setState({ hasError: false, error: null })}
        />
      );
    }

    return this.props.children;
  }
}

interface AsyncBoundaryProps {
  children: React.ReactNode;
  loading?: boolean;
  error?: Error | null;
  onRetry?: () => void;
  LoadingComponent?: React.ComponentType;
  ErrorComponent?: React.ComponentType<{ error: Error | null; onRetry?: () => void }>;
}

export const AsyncBoundary: React.FC<AsyncBoundaryProps> = ({
  children,
  loading,
  error,
  onRetry,
  LoadingComponent,
  ErrorComponent,
}) => {
  if (loading) {
    return LoadingComponent ? <LoadingComponent /> : <div>Loading...</div>;
  }

  if (error) {
    return ErrorComponent ? (
      <ErrorComponent error={error} onRetry={onRetry} />
    ) : (
      <ErrorState error={error} onRetry={onRetry} />
    );
  }

  return <ErrorBoundary>{children}</ErrorBoundary>;
};
