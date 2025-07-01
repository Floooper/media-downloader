import React from 'react';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '../../utils/styles';

const progressVariants = cva(
  'relative w-full overflow-hidden rounded-full bg-secondary-200',
  {
    variants: {
      size: {
        sm: 'h-1',
        md: 'h-2',
        lg: 'h-3',
      },
      variant: {
        default: '',
        success: '',
        warning: '',
        error: '',
      },
    },
    defaultVariants: {
      size: 'md',
      variant: 'default',
    },
  }
);

const barVariants = cva(
  'h-full w-full flex-1 transition-all',
  {
    variants: {
      variant: {
        default: 'bg-primary-600',
        success: 'bg-success-500',
        warning: 'bg-warning-500',
        error: 'bg-error-500',
      },
      animated: {
        true: 'transition-all duration-500 ease-in-out',
      },
    },
    defaultVariants: {
      variant: 'default',
      animated: true,
    },
  }
);

export interface ProgressProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof progressVariants> {
  value: number;
  max?: number;
  animated?: boolean;
  showValue?: boolean;
  valuePrefix?: string;
  valueSuffix?: string;
}

export const Progress = React.forwardRef<HTMLDivElement, ProgressProps>(
  ({
    className,
    value,
    max = 100,
    size,
    variant,
    animated,
    showValue,
    valuePrefix,
    valueSuffix,
    ...props
  }, ref) => {
    const percentage = Math.min(Math.max((value / max) * 100, 0), 100);

    return (
      <div className="relative w-full">
        <div
          ref={ref}
          className={cn(progressVariants({ size, variant, className }))}
          {...props}
        >
          <div
            className={cn(barVariants({ variant, animated }))}
            style={{ width: `${percentage}%` }}
          />
        </div>
        {showValue && (
          <div className="absolute inset-0 flex items-center justify-center text-xs font-medium">
            {valuePrefix}
            {percentage.toFixed(1)}
            {valueSuffix || '%'}
          </div>
        )}
      </div>
    );
  }
);

Progress.displayName = 'Progress';
