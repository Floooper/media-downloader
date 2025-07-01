import React from 'react';
import { MagnifyingGlassIcon, XMarkIcon } from '@heroicons/react/24/outline';
import { cn } from '../../utils/styles';

interface SearchInputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  onSearch?: (value: string) => void;
  onClear?: () => void;
  loading?: boolean;
}

export const SearchInput = React.forwardRef<HTMLInputElement, SearchInputProps>(
  ({ className, onSearch, onClear, loading, ...props }, ref) => {
    const [internalValue, setInternalValue] = React.useState(props.value || '');
    const searchTimeout = React.useRef<NodeJS.Timeout>();
    const isControlled = props.value !== undefined;
    const value = isControlled ? props.value : internalValue;

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
      const newValue = e.target.value;
      if (!isControlled) {
        setInternalValue(newValue);
      }
      props.onChange?.(e);

      if (onSearch) {
        if (searchTimeout.current) {
          clearTimeout(searchTimeout.current);
        }
        searchTimeout.current = setTimeout(() => {
          onSearch(newValue);
        }, 300);
      }
    };

    const handleClear = () => {
      if (!isControlled) {
        setInternalValue('');
      }
      if (onClear) {
        onClear();
      } else if (onSearch) {
        onSearch('');
      }
      props.onChange?.({
        target: { value: '' },
      } as React.ChangeEvent<HTMLInputElement>);
    };

    React.useEffect(() => {
      if (isControlled && props.value !== internalValue) {
        setInternalValue(props.value as string);
      }
    }, [isControlled, props.value, internalValue]);

    React.useEffect(() => {
      return () => {
        if (searchTimeout.current) {
          clearTimeout(searchTimeout.current);
        }
      };
    }, []);

    return (
      <div className={cn('relative rounded-md shadow-sm', className)}>
        <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3">
          {loading ? (
            <svg
              className="h-5 w-5 animate-spin text-secondary-400"
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
            >
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
              ></circle>
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
              ></path>
            </svg>
          ) : (
            <MagnifyingGlassIcon
              className="h-5 w-5 text-secondary-400"
              aria-hidden="true"
            />
          )}
        </div>
        <input
          ref={ref}
          type="text"
          className={cn(
            'block w-full rounded-md border-0 py-1.5 pl-10 pr-10 text-secondary-900 ring-1 ring-inset ring-secondary-300 placeholder:text-secondary-400 focus:ring-2 focus:ring-inset focus:ring-primary-600 sm:text-sm sm:leading-6',
            {
              'pr-10': value,
              'pr-3': !value,
            }
          )}
          value={value}
          onChange={handleChange}
          {...props}
        />
        {value && (
          <button
            type="button"
            className="absolute inset-y-0 right-0 flex items-center pr-3"
            onClick={handleClear}
          >
            <XMarkIcon
              className="h-5 w-5 text-secondary-400 hover:text-secondary-500"
              aria-hidden="true"
            />
          </button>
        )}
      </div>
    );
  }
);

SearchInput.displayName = 'SearchInput';
