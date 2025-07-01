import { useEffect, useCallback } from 'react';
import { UseFormReturn, FieldValues } from 'react-hook-form';

interface UseFormKeyboardShortcutsOptions {
  submitOnEnter?: boolean;
  clearOnEscape?: boolean;
  focusFirstError?: boolean;
  navigateWithArrows?: boolean;
}

export function useFormKeyboardShortcuts<T extends FieldValues>(
  form: UseFormReturn<T>,
  options: UseFormKeyboardShortcutsOptions = {}
) {
  const {
    submitOnEnter = true,
    clearOnEscape = true,
    focusFirstError = true,
    navigateWithArrows = true,
  } = options;

  const focusField = useCallback((name: string) => {
    const element = document.querySelector(`[name="${name}"]`) as HTMLElement;
    if (element) {
      element.focus();
    }
  }, []);

  const focusFirstErrorField = useCallback(() => {
    const errors = form.formState.errors;
    const firstErrorField = Object.keys(errors)[0];
    if (firstErrorField) {
      focusField(firstErrorField);
    }
  }, [form.formState.errors, focusField]);

  const getFieldNames = useCallback(() => {
    return Object.keys(form.getValues());
  }, [form]);

  const navigateFields = useCallback(
    (direction: 'next' | 'previous') => {
      const fieldNames = getFieldNames();
      const activeElement = document.activeElement;
      const currentFieldName = activeElement?.getAttribute('name');
      const currentIndex = fieldNames.indexOf(currentFieldName || '');

      if (currentIndex === -1) return;

      let nextIndex;
      if (direction === 'next') {
        nextIndex = currentIndex + 1 >= fieldNames.length ? 0 : currentIndex + 1;
      } else {
        nextIndex = currentIndex - 1 < 0 ? fieldNames.length - 1 : currentIndex - 1;
      }

      focusField(fieldNames[nextIndex]);
    },
    [getFieldNames, focusField]
  );

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Ignore if within textarea or contenteditable
      if (
        e.target instanceof HTMLTextAreaElement ||
        (e.target instanceof HTMLElement && e.target.isContentEditable)
      ) {
        return;
      }

      // Submit on Enter
      if (
        submitOnEnter &&
        e.key === 'Enter' &&
        !e.shiftKey &&
        !e.isComposing
      ) {
        e.preventDefault();
        void form.handleSubmit(() => {
          // Submit handled by form's onSubmit handler
        })();
      }

      // Clear on Escape
      if (clearOnEscape && e.key === 'Escape') {
        e.preventDefault();
        form.reset();
      }

      // Focus first error
      if (focusFirstError && e.key === 'e' && (e.ctrlKey || e.metaKey)) {
        e.preventDefault();
        focusFirstErrorField();
      }

      // Navigate with arrows
      if (navigateWithArrows) {
        if (e.key === 'ArrowDown' || (e.key === 'Tab' && !e.shiftKey)) {
          e.preventDefault();
          navigateFields('next');
        }
        if (e.key === 'ArrowUp' || (e.key === 'Tab' && e.shiftKey)) {
          e.preventDefault();
          navigateFields('previous');
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [
    form,
    submitOnEnter,
    clearOnEscape,
    focusFirstError,
    navigateWithArrows,
    focusFirstErrorField,
    navigateFields,
  ]);

  // Focus first error on mount
  useEffect(() => {
    if (focusFirstError && Object.keys(form.formState.errors).length > 0) {
      focusFirstErrorField();
    }
  }, [focusFirstError, form.formState.errors, focusFirstErrorField]);

  return {
    focusField,
    focusFirstErrorField,
    navigateFields,
  };
}
