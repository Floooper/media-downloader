import React from 'react';
import { cn } from '../../utils/styles';

interface EmptyStateProps extends React.HTMLAttributes<HTMLDivElement> {
  icon?: React.ReactNode;
  title: string;
  description?: string;
  action?: React.ReactNode;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  className,
  icon,
  title,
  description,
  action,
  ...props
}) => {
  return (
    <div
      className={cn(
        'flex flex-col items-center justify-center p-8 text-center',
        className
      )}
      {...props}
    >
      {icon && (
        <div className="mx-auto h-12 w-12 text-secondary-400">{icon}</div>
      )}
      <h3 className="mt-2 text-sm font-semibold text-secondary-900">{title}</h3>
      {description && (
        <p className="mt-1 text-sm text-secondary-500">{description}</p>
      )}
      {action && <div className="mt-6">{action}</div>}
    </div>
  );
};

interface ErrorStateProps extends Omit<EmptyStateProps, 'icon'> {
  error?: Error | null;
  onRetry?: () => void;
}

export const ErrorState: React.FC<ErrorStateProps> = ({
  className,
  title = 'Something went wrong',
  description,
  error,
  onRetry,
  action,
  ...props
}) => {
  return (
    <EmptyState
      className={cn('text-error-600', className)}
      icon={
        <svg
          className="h-full w-full"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          aria-hidden="true"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
          />
        </svg>
      }
      title={title}
      description={description || error?.message}
      action={
        onRetry ? (
          <button
            type="button"
            onClick={onRetry}
            className="text-sm font-semibold text-error-600 hover:text-error-500"
          >
            Try again
          </button>
        ) : (
          action
        )
      }
      {...props}
    />
  );
};

interface LoadingStateProps extends Omit<EmptyStateProps, 'icon' | 'title'> {
  text?: string;
}

export const LoadingState: React.FC<LoadingStateProps> = ({
  className,
  text = 'Loading...',
  description,
  ...props
}) => {
  return (
    <EmptyState
      className={cn('text-secondary-400', className)}
      icon={
        <svg
          className="h-full w-full animate-spin"
          fill="none"
          viewBox="0 0 24 24"
          aria-hidden="true"
        >
          <circle
            className="opacity-25"
            cx="12"
            cy="12"
            r="10"
            stroke="currentColor"
            strokeWidth="4"
          />
          <path
            className="opacity-75"
            fill="currentColor"
            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
          />
        </svg>
      }
      title={text}
      description={description}
      {...props}
    />
  );
};
