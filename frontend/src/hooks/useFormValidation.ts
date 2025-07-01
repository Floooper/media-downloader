import { useState, useCallback, useEffect, useRef } from 'react';
import * as z from 'zod';

type ValidationRule<T> = {
  validate: (value: T) => boolean | Promise<boolean>;
  message: string;
};

type AsyncValidationState = {
  isValidating: boolean;
  validationError: string | null;
};

interface FieldDependency {
  field: string;
  value: unknown;
}

type ValidationOptions<T> = {
  validateOnChange?: boolean;
  validateOnBlur?: boolean;
  debounceMs?: number;
  transform?: (value: T) => T;
  dependencies?: FieldDependency[];
  asyncValidation?: ValidationRule<T>;
};

export function useFieldValidation<T>(
  initialValue: T,
  validationRules: ValidationRule<T>[],
  options: ValidationOptions<T> = {}
) {
  const {
    validateOnChange = true,
    validateOnBlur = true,
    debounceMs = 500,
    transform,
    dependencies = [],
    asyncValidation,
  } = options;

  const [value, setValue] = useState<T>(initialValue);
  const [isDirty, setIsDirty] = useState(false);
  const [isTouched, setIsTouched] = useState(false);
  const [errors, setErrors] = useState<string[]>([]);
  const [asyncState, setAsyncState] = useState<AsyncValidationState>({
    isValidating: false,
    validationError: null,
  });

  // Store dependencies in a ref to avoid recreation on every render
  const dependenciesRef = useRef(dependencies);
  dependenciesRef.current = dependencies;

  const validate = useCallback(
    async (valueToValidate: T = value) => {
      const transformedValue = transform ? transform(valueToValidate) : valueToValidate;
      const validationErrors: string[] = [];

      // Synchronous validation
      for (const rule of validationRules) {
        const isValid = rule.validate(transformedValue);
        if (!isValid) {
          validationErrors.push(rule.message);
        }
      }

      setErrors(validationErrors);

      // Async validation
      if (asyncValidation && validationErrors.length === 0) {
        setAsyncState((prev) => ({ ...prev, isValidating: true }));
        try {
          const isValid = await asyncValidation.validate(transformedValue);
          if (!isValid) {
            setAsyncState({
              isValidating: false,
              validationError: asyncValidation.message,
            });
          } else {
            setAsyncState({
              isValidating: false,
              validationError: null,
            });
          }
        } catch {
          setAsyncState({
            isValidating: false,
            validationError: 'Validation failed',
          });
        }
      }

      return validationErrors.length === 0 && !asyncState.validationError;
    },
    [value, validationRules, transform, asyncValidation, asyncState.validationError]
  );

  useEffect(() => {
    if (validateOnChange && isDirty) {
      const timeoutId = setTimeout(() => void validate(), debounceMs);
      return () => clearTimeout(timeoutId);
    }
  }, [validate, validateOnChange, isDirty, debounceMs, dependencies]);

  const handleChange = useCallback(
    (newValue: T) => {
      setValue(newValue);
      setIsDirty(true);
    },
    []
  );

  const handleBlur = useCallback(() => {
    setIsTouched(true);
    if (validateOnBlur) {
      void validate();
    }
  }, [validate, validateOnBlur]);

  const reset = useCallback(() => {
    setValue(initialValue);
    setIsDirty(false);
    setIsTouched(false);
    setErrors([]);
    setAsyncState({
      isValidating: false,
      validationError: null,
    });
  }, [initialValue]);

  return {
    value,
    setValue: handleChange,
    onBlur: handleBlur,
    isDirty,
    isTouched,
    errors,
    isValidating: asyncState.isValidating,
    asyncError: asyncState.validationError,
    validate,
    reset,
  };
}

export type FormValues = Record<string, unknown>;

export function useFormValidation<T extends FormValues>(
  initialValues: T,
  schema: z.ZodType<T>
) {
  const [values, setValues] = useState<T>(initialValues);
  const [errors, setErrors] = useState<Record<keyof T, string[]>>({} as Record<keyof T, string[]>);
  const [touched, setTouched] = useState<Record<keyof T, boolean>>({} as Record<keyof T, boolean>);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isValid, setIsValid] = useState(false);

  const validateField = useCallback(
    async (name: keyof T, value: unknown) => {
      try {
        await schema.pick({ [name]: true }).parseAsync({ [name]: value });
        setErrors((prev) => ({ ...prev, [name]: [] }));
        return true;
      } catch (error) {
        if (error instanceof z.ZodError) {
          const fieldErrors = error.errors.map((e) => e.message);
          setErrors((prev) => ({ ...prev, [name]: fieldErrors }));
        }
        return false;
      }
    },
    [schema]
  );

  const validateForm = useCallback(async () => {
    try {
      await schema.parseAsync(values);
      setErrors({} as Record<keyof T, string[]>);
      setIsValid(true);
      return true;
    } catch (error) {
      if (error instanceof z.ZodError) {
        const formErrors = error.errors.reduce((acc, err) => {
          const field = err.path[0] as keyof T;
          acc[field] = acc[field] || [];
          acc[field].push(err.message);
          return acc;
        }, {} as Record<keyof T, string[]>);
        setErrors(formErrors);
      }
      setIsValid(false);
      return false;
    }
  }, [values, schema]);

  const handleChange = useCallback(
    async (name: keyof T, value: unknown) => {
      setValues((prev) => ({ ...prev, [name]: value }));
      await validateField(name, value);
    },
    [validateField]
  );

  const handleBlur = useCallback((name: keyof T) => {
    setTouched((prev) => ({ ...prev, [name]: true }));
  }, []);

  const handleSubmit = useCallback(
    async (onSubmit: (values: T) => Promise<void>) => {
      setIsSubmitting(true);
      const isValid = await validateForm();

      if (isValid) {
        try {
          await onSubmit(values);
        } catch (error) {
          console.error('Form submission error:', error);
        }
      }

      setIsSubmitting(false);
    },
    [values, validateForm]
  );

  const reset = useCallback(() => {
    setValues(initialValues);
    setErrors({} as Record<keyof T, string[]>);
    setTouched({} as Record<keyof T, boolean>);
    setIsSubmitting(false);
    setIsValid(false);
  }, [initialValues]);

  return {
    values,
    errors,
    touched,
    isSubmitting,
    isValid,
    handleChange,
    handleBlur,
    handleSubmit,
    reset,
    validateField,
    validateForm,
  };
}
