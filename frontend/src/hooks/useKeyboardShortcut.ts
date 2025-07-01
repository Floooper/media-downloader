import { useEffect, useCallback, useRef } from 'react';

type KeyMap = {
  [key: string]: {
    callback: () => void;
    description?: string;
    preventDefault?: boolean;
  };
};

interface KeyboardShortcutOptions {
  enabled?: boolean;
  preventDefault?: boolean;
  targetKey?: string | string[];
  keyEvent?: 'keydown' | 'keyup';
}

export function useKeyboardShortcut(
  shortcut: string | string[],
  callback: () => void,
  options: KeyboardShortcutOptions = {}
) {
  const {
    enabled = true,
    preventDefault = true,
    keyEvent = 'keydown',
  } = options;

  const keys = Array.isArray(shortcut) ? shortcut : shortcut.split('+');
  const pressedKeys = useRef<Set<string>>(new Set());

  const handleKeyPress = useCallback(
    (event: KeyboardEvent) => {
      if (!enabled) return;

      const key = event.key.toLowerCase();
      
      if (event.type === 'keydown') {
        pressedKeys.current.add(key);
      } else {
        pressedKeys.current.delete(key);
      }

      const allKeysPressed = keys.every((k) =>
        pressedKeys.current.has(k.toLowerCase())
      );

      if (allKeysPressed && event.type === keyEvent) {
        if (preventDefault) {
          event.preventDefault();
        }
        callback();
      }
    },
    [callback, enabled, keyEvent, keys, preventDefault]
  );

  useEffect(() => {
    window.addEventListener('keydown', handleKeyPress);
    window.addEventListener('keyup', handleKeyPress);

    return () => {
      window.removeEventListener('keydown', handleKeyPress);
      window.removeEventListener('keyup', handleKeyPress);
    };
  }, [handleKeyPress]);
}

interface KeyboardShortcutsOptions extends KeyboardShortcutOptions {
  scope?: string;
}

export function useKeyboardShortcuts(
  shortcuts: KeyMap,
  options: KeyboardShortcutsOptions = {}
) {
  const pressedKeys = useRef<Set<string>>(new Set());
  
  const handleKeyPress = useCallback(
    (event: KeyboardEvent) => {
      const key = event.key.toLowerCase();
      
      if (event.type === 'keydown') {
        pressedKeys.current.add(key);
      } else {
        pressedKeys.current.delete(key);
      }

      for (const [shortcut, config] of Object.entries(shortcuts)) {
        const keys = shortcut.split('+');
        const allKeysPressed = keys.every((k) =>
          pressedKeys.current.has(k.toLowerCase())
        );

        if (allKeysPressed && event.type === (options.keyEvent || 'keydown')) {
          if (config.preventDefault ?? options.preventDefault) {
            event.preventDefault();
          }
          config.callback();
        }
      }
    },
    [shortcuts, options]
  );

  useEffect(() => {
    if (options.enabled !== false) {
      window.addEventListener('keydown', handleKeyPress);
      window.addEventListener('keyup', handleKeyPress);

      return () => {
        window.removeEventListener('keydown', handleKeyPress);
        window.removeEventListener('keyup', handleKeyPress);
      };
    }
  }, [handleKeyPress, options.enabled]);

  // Return help text for available shortcuts
  return Object.entries(shortcuts).reduce((acc, [shortcut, config]) => {
    if (config.description) {
      acc[shortcut] = config.description;
    }
    return acc;
  }, {} as Record<string, string>);
}

export function useGlobalShortcuts() {
  const shortcuts: KeyMap = {
    'ctrl+k': {
      callback: () => {
        // Focus search input
        const searchInput = document.querySelector(
          '[data-search-input="true"]'
        ) as HTMLInputElement;
        if (searchInput) {
          searchInput.focus();
        }
      },
      description: 'Focus search',
    },
    'ctrl+,': {
      callback: () => {
        // Open settings
        window.location.href = '/settings';
      },
      description: 'Open settings',
    },
    'esc': {
      callback: () => {
        // Close modal or clear search
        const activeElement = document.activeElement as HTMLElement;
        if (activeElement?.tagName === 'INPUT') {
          activeElement.blur();
        }
      },
      description: 'Close modal or clear search',
    },
  };

  return useKeyboardShortcuts(shortcuts);
}
