import { useCallback, useState } from 'react';
import * as z from 'zod';

interface UseFormConfig<T> {
  initialValues: T;
  schema?: z.ZodType<T>;
  onSubmit: (values: T) => void | Promise<void>;
}

interface FormState<T> {
  values: T;
  errors: Partial<Record<keyof T, string>>;
  touched: Partial<Record<keyof T, boolean>>;
  isSubmitting: boolean;
  isValid: boolean;
}

type FieldValue = string | number | boolean | readonly string[] | undefined;

export function useForm<T extends Record<string, FieldValue>>({
  initialValues,
  schema,
  onSubmit,
}: UseFormConfig<T>) {
  const [state, setState] = useState<FormState<T>>({
    values: initialValues,
    errors: {},
    touched: {},
    isSubmitting: false,
    isValid: true,
  });

  const validateField = useCallback(
    (name: keyof T, value: FieldValue) => {
      if (!schema) return '';

      try {
        schema.shape[name as string].parse(value);
        return '';
      } catch (error) {
        if (error instanceof z.ZodError) {
          return error.errors[0]?.message || '';
        }
        return 'Invalid value';
      }
    },
    [schema]
  );

  const validateForm = useCallback(
    (values: T) => {
      if (!schema) return {};

      try {
        schema.parse(values);
        return {};
      } catch (error) {
        if (error instanceof z.ZodError) {
          return error.errors.reduce((acc, curr) => {
            const path = curr.path[0] as keyof T;
            acc[path] = curr.message;
            return acc;
          }, {} as Record<keyof T, string>);
        }
        return {};
      }
    },
    [schema]
  );

  const setFieldValue = useCallback(
    (name: keyof T, value: FieldValue) => {
      setState((prev) => {
        const newValues = { ...prev.values, [name]: value };
        const error = validateField(name, value);
        const newErrors = { ...prev.errors, [name]: error };
        const isValid = Object.values(newErrors).every((e) => !e);

        return {
          ...prev,
          values: newValues as T,
          errors: newErrors,
          touched: { ...prev.touched, [name]: true },
          isValid,
        };
      });
    },
    [validateField]
  );

  const setFieldTouched = useCallback((name: keyof T, touched = true) => {
    setState((prev) => ({
      ...prev,
      touched: { ...prev.touched, [name]: touched },
    }));
  }, []);

  const handleSubmit = useCallback(
    async (e?: React.FormEvent) => {
      if (e) {
        e.preventDefault();
      }

      setState((prev) => ({ ...prev, isSubmitting: true }));

      const errors = validateForm(state.values);
      const isValid = Object.keys(errors).length === 0;

      if (!isValid) {
        setState((prev) => ({
          ...prev,
          errors,
          isValid: false,
          isSubmitting: false,
          touched: Object.keys(prev.values).reduce(
            (acc, key) => ({ ...acc, [key]: true }),
            {} as Record<keyof T, boolean>
          ),
        }));
        return;
      }

      try {
        await onSubmit(state.values);
      } catch (error) {
        console.error('Form submission error:', error);
      } finally {
        setState((prev) => ({ ...prev, isSubmitting: false }));
      }
    },
    [state.values, validateForm, onSubmit]
  );

  const resetForm = useCallback(() => {
    setState({
      values: initialValues,
      errors: {},
      touched: {},
      isSubmitting: false,
      isValid: true,
    });
  }, [initialValues]);

  type InputElement = HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement;

  const getFieldProps = useCallback(
    (name: keyof T) => ({
      name,
      value: state.values[name],
      onChange: (e: React.ChangeEvent<InputElement>) => {
        const target = e.target;
        const value = target.type === 'checkbox' 
          ? (target as HTMLInputElement).checked 
          : target.value;
        setFieldValue(name, value as FieldValue);
      },
      onBlur: () => setFieldTouched(name),
    }),
    [state.values, setFieldValue, setFieldTouched]
  );

  return {
    values: state.values,
    errors: state.errors,
    touched: state.touched,
    isSubmitting: state.isSubmitting,
    isValid: state.isValid,
    setFieldValue,
    setFieldTouched,
    handleSubmit,
    resetForm,
    getFieldProps,
  };
}
