import { useEffect, useRef, useState } from 'react';

interface KeyBinding {
  key: string;
  ctrl?: boolean;
  alt?: boolean;
  shift?: boolean;
  meta?: boolean;
}

export function parseKeyBinding(binding: string): KeyBinding {
  const parts = binding.toLowerCase().split('+');
  const key = parts.pop() || '';

  return {
    key,
    ctrl: parts.includes('ctrl'),
    alt: parts.includes('alt'),
    shift: parts.includes('shift'),
    meta: parts.includes('meta'),
  };
}

export function matchesKeyBinding(event: KeyboardEvent, binding: KeyBinding): boolean {
  return (
    event.key.toLowerCase() === binding.key &&
    event.ctrlKey === !!binding.ctrl &&
    event.altKey === !!binding.alt &&
    event.shiftKey === !!binding.shift &&
    event.metaKey === !!binding.meta
  );
}

interface FocusGroupItem {
  element: HTMLElement;
  disabled?: boolean;
}

export function focusNextItem(
  items: FocusGroupItem[],
  currentIndex: number,
  direction: 'next' | 'previous' = 'next',
  loop: boolean = true
): number {
  const itemCount = items.length;
  if (itemCount === 0) return -1;

  const increment = direction === 'next' ? 1 : -1;
  let nextIndex = currentIndex;

  do {
    nextIndex += increment;
    if (loop) {
      nextIndex = (nextIndex + itemCount) % itemCount;
    } else if (nextIndex < 0 || nextIndex >= itemCount) {
      return currentIndex;
    }

    if (!items[nextIndex].disabled) {
      items[nextIndex].element.focus();
      return nextIndex;
    }
  } while (nextIndex !== currentIndex);

  return currentIndex;
}

interface UseFocusGroupOptions {
  onFocusChange?: (index: number) => void;
  orientation?: 'horizontal' | 'vertical' | 'both';
  loop?: boolean;
  defaultIndex?: number;
}

export function useFocusGroup(
  items: FocusGroupItem[],
  options: UseFocusGroupOptions = {}
) {
  const {
    onFocusChange,
    orientation = 'both',
    loop = true,
    defaultIndex = -1,
  } = options;

  const [focusedIndex, setFocusedIndex] = useState(defaultIndex);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const handleKeyDown = (event: KeyboardEvent) => {
      if (['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight'].includes(event.key)) {
        event.preventDefault();

        let direction: 'next' | 'previous' | null = null;

        if (orientation === 'horizontal' || orientation === 'both') {
          if (event.key === 'ArrowRight') direction = 'next';
          if (event.key === 'ArrowLeft') direction = 'previous';
        }

        if (orientation === 'vertical' || orientation === 'both') {
          if (event.key === 'ArrowDown') direction = 'next';
          if (event.key === 'ArrowUp') direction = 'previous';
        }

        if (direction) {
          const nextIndex = focusNextItem(items, focusedIndex, direction, loop);
          setFocusedIndex(nextIndex);
          onFocusChange?.(nextIndex);
        }
      }

      // Handle Home/End keys
      if (event.key === 'Home') {
        event.preventDefault();
        const firstIndex = items.findIndex((item) => !item.disabled);
        if (firstIndex !== -1) {
          items[firstIndex].element.focus();
          setFocusedIndex(firstIndex);
          onFocusChange?.(firstIndex);
        }
      }

      if (event.key === 'End') {
        event.preventDefault();
        const lastIndex = items.map((item) => !item.disabled).lastIndexOf(true);
        if (lastIndex !== -1) {
          items[lastIndex].element.focus();
          setFocusedIndex(lastIndex);
          onFocusChange?.(lastIndex);
        }
      }
    };

    container.addEventListener('keydown', handleKeyDown);
    return () => container.removeEventListener('keydown', handleKeyDown);
  }, [items, focusedIndex, orientation, loop, onFocusChange]);

  return {
    containerRef,
    focusedIndex,
    setFocusedIndex: (index: number) => {
      setFocusedIndex(index);
      onFocusChange?.(index);
    },
  };
}

interface UseTypeAheadOptions {
  onMatch?: (index: number) => void;
  timeout?: number;
  caseSensitive?: boolean;
}

export function useTypeAhead(
  items: Array<{ text: string }>,
  options: UseTypeAheadOptions = {}
) {
  const { onMatch, timeout = 1000, caseSensitive = false } = options;
  const [searchTerm, setSearchTerm] = useState('');
  const resetTimeout = useRef<NodeJS.Timeout>();

  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      // Ignore if user is typing in an input
      if (
        event.target instanceof HTMLInputElement ||
        event.target instanceof HTMLTextAreaElement
      ) {
        return;
      }

      // Only handle printable characters
      if (event.key.length === 1) {
        event.preventDefault();

        const newSearchTerm = searchTerm + event.key;
        setSearchTerm(newSearchTerm);

        // Find matching item
        const searchText = caseSensitive ? newSearchTerm : newSearchTerm.toLowerCase();
        const matchIndex = items.findIndex((item) => {
          const itemText = caseSensitive ? item.text : item.text.toLowerCase();
          return itemText.startsWith(searchText);
        });

        if (matchIndex !== -1) {
          onMatch?.(matchIndex);
        }

        // Reset search term after timeout
        if (resetTimeout.current) {
          clearTimeout(resetTimeout.current);
        }
        resetTimeout.current = setTimeout(() => {
          setSearchTerm('');
        }, timeout);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
      if (resetTimeout.current) {
        clearTimeout(resetTimeout.current);
      }
    };
  }, [items, searchTerm, timeout, caseSensitive, onMatch]);

  return {
    searchTerm,
    clearSearch: () => setSearchTerm(''),
  };
}

// Example usage:
// const items = [
//   { element: ref1.current, disabled: false },
//   { element: ref2.current, disabled: true },
//   { element: ref3.current, disabled: false },
// ];
//
// const { containerRef, focusedIndex } = useFocusGroup(items, {
//   orientation: 'vertical',
//   loop: true,
// });
//
// const { searchTerm } = useTypeAhead(
//   items.map((item) => ({ text: item.element.textContent || '' })),
//   {
//     onMatch: (index) => {
//       items[index].element.focus();
//     },
//   }
// );
