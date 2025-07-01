import React from 'react';
import { useForm, UseFormReturn, FieldValues, Path, RegisterOptions, FieldErrors } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { cn } from '../../utils/styles';
import { ExclamationCircleIcon } from '@heroicons/react/24/outline';

interface FormProps<TFormValues extends FieldValues> {
  onSubmit: (data: TFormValues) => void;
  children: (methods: UseFormReturn<TFormValues>) => React.ReactNode;
  schema?: z.ZodType<TFormValues>;
  className?: string;
}

export const Form = <TFormValues extends Record<string, unknown>>(
  {
    onSubmit,
    children,
    schema,
    className,
  }: FormProps<TFormValues>) => {
  const methods = useForm<TFormValues>({
    resolver: schema ? zodResolver(schema) : undefined,
  });

  return (
    <form
      className={className}
      onSubmit={methods.handleSubmit(onSubmit)}
      noValidate
    >
      {children(methods)}
    </form>
  );
};

interface FieldProps<TFormValues extends FieldValues>
  extends Omit<React.ComponentPropsWithoutRef<'input'>, 'name'> {
  name: Path<TFormValues>;
  label?: string;
  rules?: RegisterOptions;
  error?: FieldErrors[Path<TFormValues>];
}

export const Field = <TFormValues extends FieldValues>({
  name,
  label,
  error,
  type = 'text',
  className,
  ...props
}: FieldProps<TFormValues>) => {
  return (
    <div>
      {label && (
        <label
          htmlFor={name}
          className="block text-sm font-medium text-secondary-700"
        >
          {label}
        </label>
      )}
      <div className="relative mt-1 rounded-md shadow-sm">
        <input
          type={type}
          name={name}
          id={name}
          className={cn(
            'block w-full rounded-md border-secondary-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm',
            error && 'border-error-300 pr-10 text-error-900 placeholder-error-300 focus:border-error-500 focus:ring-error-500',
            className
          )}
          aria-invalid={error ? 'true' : 'false'}
          aria-describedby={error ? `${name}-error` : undefined}
          {...props}
        />
        {error && (
          <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center pr-3">
            <ExclamationCircleIcon
              className="h-5 w-5 text-error-500"
              aria-hidden="true"
            />
          </div>
        )}
      </div>
      {error && (
        <p className="mt-2 text-sm text-error-600" id={`${name}-error`}>
          {error.message?.toString()}
        </p>
      )}
    </div>
  );
};

interface TextAreaProps<TFormValues extends FieldValues>
  extends Omit<React.ComponentPropsWithoutRef<'textarea'>, 'name'> {
  name: Path<TFormValues>;
  label?: string;
  error?: FieldErrors[Path<TFormValues>];
}

export const TextArea = <TFormValues extends FieldValues>({
  name,
  label,
  error,
  className,
  ...props
}: TextAreaProps<TFormValues>) => {
  return (
    <div>
      {label && (
        <label
          htmlFor={name}
          className="block text-sm font-medium text-secondary-700"
        >
          {label}
        </label>
      )}
      <div className="relative mt-1 rounded-md shadow-sm">
        <textarea
          name={name}
          id={name}
          className={cn(
            'block w-full rounded-md border-secondary-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm',
            error && 'border-error-300 text-error-900 placeholder-error-300 focus:border-error-500 focus:ring-error-500',
            className
          )}
          aria-invalid={error ? 'true' : 'false'}
          aria-describedby={error ? `${name}-error` : undefined}
          {...props}
        />
      </div>
      {error && (
        <p className="mt-2 text-sm text-error-600" id={`${name}-error`}>
          {error.message?.toString()}
        </p>
      )}
    </div>
  );
};

interface SelectProps<TFormValues extends FieldValues>
  extends Omit<React.ComponentPropsWithoutRef<'select'>, 'name'> {
  name: Path<TFormValues>;
  label?: string;
  error?: FieldErrors[Path<TFormValues>];
  options: Array<{ value: string; label: string }>;
}

export const Select = <TFormValues extends FieldValues>({
  name,
  label,
  error,
  options,
  className,
  ...props
}: SelectProps<TFormValues>) => {
  return (
    <div>
      {label && (
        <label
          htmlFor={name}
          className="block text-sm font-medium text-secondary-700"
        >
          {label}
        </label>
      )}
      <div className="relative mt-1 rounded-md shadow-sm">
        <select
          name={name}
          id={name}
          className={cn(
            'block w-full rounded-md border-secondary-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm',
            error && 'border-error-300 text-error-900 focus:border-error-500 focus:ring-error-500',
            className
          )}
          aria-invalid={error ? 'true' : 'false'}
          aria-describedby={error ? `${name}-error` : undefined}
          {...props}
        >
          {options.map(({ value, label }) => (
            <option key={value} value={value}>
              {label}
            </option>
          ))}
        </select>
      </div>
      {error && (
        <p className="mt-2 text-sm text-error-600" id={`${name}-error`}>
          {error.message?.toString()}
        </p>
      )}
    </div>
  );
};

interface CheckboxProps<TFormValues extends FieldValues>
  extends Omit<React.ComponentPropsWithoutRef<'input'>, 'type' | 'name'> {
  name: Path<TFormValues>;
  label?: string;
  error?: FieldErrors[Path<TFormValues>];
}

export const Checkbox = <TFormValues extends FieldValues>({
  name,
  label,
  error,
  className,
  ...props
}: CheckboxProps<TFormValues>) => {
  return (
    <div className="relative flex items-start">
      <div className="flex h-5 items-center">
        <input
          type="checkbox"
          name={name}
          id={name}
          className={cn(
            'h-4 w-4 rounded border-secondary-300 text-primary-600 focus:ring-primary-500',
            error && 'border-error-300 text-error-600 focus:ring-error-500',
            className
          )}
          aria-invalid={error ? 'true' : 'false'}
          aria-describedby={error ? `${name}-error` : undefined}
          {...props}
        />
      </div>
      {label && (
        <div className="ml-3 text-sm">
          <label htmlFor={name} className="font-medium text-secondary-700">
            {label}
          </label>
        </div>
      )}
      {error && (
        <p className="mt-2 text-sm text-error-600" id={`${name}-error`}>
          {error.message?.toString()}
        </p>
      )}
    </div>
  );
};

interface RadioGroupProps<TFormValues extends FieldValues>
  extends Omit<React.ComponentPropsWithoutRef<'input'>, 'type' | 'name'> {
  name: Path<TFormValues>;
  label?: string;
  error?: FieldErrors[Path<TFormValues>];
  options: Array<{ value: string; label: string }>;
}

export const RadioGroup = <TFormValues extends FieldValues>({
  name,
  label,
  error,
  options,
  className,
  ...props
}: RadioGroupProps<TFormValues>) => {
  return (
    <div>
      {label && (
        <label className="block text-sm font-medium text-secondary-700">
          {label}
        </label>
      )}
      <div className="mt-4 space-y-4">
        {options.map(({ value, label }) => (
          <div key={value} className="flex items-center">
            <input
              type="radio"
              name={name}
              id={`${name}-${value}`}
              value={value}
              className={cn(
                'h-4 w-4 border-secondary-300 text-primary-600 focus:ring-primary-500',
                error && 'border-error-300 text-error-600 focus:ring-error-500',
                className
              )}
              aria-invalid={error ? 'true' : 'false'}
              {...props}
            />
            <label
              htmlFor={`${name}-${value}`}
              className="ml-3 block text-sm font-medium text-secondary-700"
            >
              {label}
            </label>
          </div>
        ))}
      </div>
      {error && (
        <p className="mt-2 text-sm text-error-600" id={`${name}-error`}>
          {error.message?.toString()}
        </p>
      )}
    </div>
  );
};
