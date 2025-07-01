import React from 'react';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '../../utils/styles';

const badgeVariants = cva(
  'inline-flex items-center rounded-full font-medium ring-1 ring-inset',
  {
    variants: {
      variant: {
        default: 'bg-secondary-50 text-secondary-700 ring-secondary-600/20',
        primary: 'bg-primary-50 text-primary-700 ring-primary-600/20',
        success: 'bg-success-50 text-success-700 ring-success-600/20',
        warning: 'bg-warning-50 text-warning-700 ring-warning-600/20',
        error: 'bg-error-50 text-error-700 ring-error-600/20',
      },
      size: {
        sm: 'px-2 py-0.5 text-xs',
        md: 'px-2.5 py-0.5 text-sm',
        lg: 'px-3 py-1 text-base',
      },
      removable: {
        true: 'pr-1',
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'md',
    },
  }
);

const closeButtonVariants = cva(
  'ml-1 rounded-full p-0.5 hover:bg-black/5 focus:outline-none focus:ring-2 focus:ring-offset-2',
  {
    variants: {
      variant: {
        default: 'focus:ring-secondary-500',
        primary: 'focus:ring-primary-500',
        success: 'focus:ring-success-500',
        warning: 'focus:ring-warning-500',
        error: 'focus:ring-error-500',
      },
      size: {
        sm: 'h-3.5 w-3.5',
        md: 'h-4 w-4',
        lg: 'h-5 w-5',
      },
    },
  }
);

export interface BadgeProps
  extends React.HTMLAttributes<HTMLSpanElement>,
    VariantProps<typeof badgeVariants> {
  onRemove?: () => void;
}

export const Badge = React.forwardRef<HTMLSpanElement, BadgeProps>(
  ({ className, variant, size, onRemove, children, ...props }, ref) => {
    return (
      <span
        ref={ref}
        className={cn(
          badgeVariants({ variant, size, removable: !!onRemove, className })
        )}
        {...props}
      >
        {children}
        {onRemove && (
          <button
            type="button"
            onClick={onRemove}
            className={cn(closeButtonVariants({ variant, size }))}
          >
            <span className="sr-only">Remove</span>
            <svg
              className="h-full w-full"
              viewBox="0 0 14 14"
              fill="none"
              xmlns="http://www.w3.org/2000/svg"
            >
              <path
                d="M4 4L10 10M10 4L4 10"
                stroke="currentColor"
                strokeWidth="1.5"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
          </button>
        )}
      </span>
    );
  }
);

Badge.displayName = 'Badge';
