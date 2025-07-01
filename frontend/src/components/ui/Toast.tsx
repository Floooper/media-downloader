import React from 'react';
import { Transition } from '@headlessui/react';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '../../utils/styles';

const toastVariants = cva(
  'pointer-events-auto w-full max-w-sm overflow-hidden rounded-lg bg-white shadow-lg ring-1 ring-black ring-opacity-5',
  {
    variants: {
      variant: {
        default: 'ring-secondary-200',
        success: 'ring-success-500',
        warning: 'ring-warning-500',
        error: 'ring-error-500',
      },
    },
    defaultVariants: {
      variant: 'default',
    },
  }
);

const iconVariants = cva(
  'h-6 w-6',
  {
    variants: {
      variant: {
        default: 'text-secondary-400',
        success: 'text-success-500',
        warning: 'text-warning-500',
        error: 'text-error-500',
      },
    },
    defaultVariants: {
      variant: 'default',
    },
  }
);

export interface ToastProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof toastVariants> {
  show: boolean;
  onClose: () => void;
  title?: string;
  autoClose?: boolean;
  autoCloseDelay?: number;
}

export const Toast = React.forwardRef<HTMLDivElement, ToastProps>(
  ({
    className,
    variant,
    show,
    onClose,
    title,
    children,
    autoClose = true,
    autoCloseDelay = 5000,
    ...props
  }, ref) => {
    React.useEffect(() => {
      if (show && autoClose) {
        const timer = setTimeout(() => {
          onClose();
        }, autoCloseDelay);
        return () => clearTimeout(timer);
      }
    }, [show, autoClose, autoCloseDelay, onClose]);

    return (
      <Transition
        show={show}
        as={React.Fragment}
        enter="transform ease-out duration-300 transition"
        enterFrom="translate-y-2 opacity-0 sm:translate-y-0 sm:translate-x-2"
        enterTo="translate-y-0 opacity-100 sm:translate-x-0"
        leave="transition ease-in duration-100"
        leaveFrom="opacity-100"
        leaveTo="opacity-0"
      >
        <div
          ref={ref}
          className={cn(toastVariants({ variant, className }))}
          {...props}
        >
          <div className="p-4">
            <div className="flex items-start">
              <div className="flex-shrink-0">
                {variant === 'success' && (
                  <svg className={iconVariants({ variant })} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                )}
                {variant === 'warning' && (
                  <svg className={iconVariants({ variant })} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                  </svg>
                )}
                {variant === 'error' && (
                  <svg className={iconVariants({ variant })} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                )}
                {variant === 'default' && (
                  <svg className={iconVariants({ variant })} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                )}
              </div>
              <div className="ml-3 w-0 flex-1 pt-0.5">
                {title && (
                  <p className="text-sm font-medium text-secondary-900">{title}</p>
                )}
                <div className="mt-1 text-sm text-secondary-500">
                  {children}
                </div>
              </div>
              <div className="ml-4 flex flex-shrink-0">
                <button
                  type="button"
                  className="inline-flex rounded-md text-secondary-400 hover:text-secondary-500 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2"
                  onClick={onClose}
                >
                  <span className="sr-only">Close</span>
                  <svg className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                  </svg>
                </button>
              </div>
            </div>
          </div>
        </div>
      </Transition>
    );
  }
);

Toast.displayName = 'Toast';

export const ToastContainer: React.FC<React.HTMLAttributes<HTMLDivElement>> = ({
  className,
  ...props
}) => {
  return (
    <div
      className={cn(
        'fixed bottom-0 right-0 z-50 m-6 flex flex-col items-end space-y-4',
        className
      )}
      {...props}
    />
  );
};
