import { useState, useEffect } from 'react';
import { CommandPalette } from './CommandPalette';
import type { CommandItem } from './types';

export function useCommandPalette(commands: CommandItem[]) {
  const [isOpen, setIsOpen] = useState(false);

  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (
        (event.metaKey || event.ctrlKey) &&
        event.key === 'k' &&
        !event.repeat
      ) {
        event.preventDefault();
        setIsOpen((open) => !open);
      }

      if (event.key === 'Escape') {
        setIsOpen(false);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  return {
    isOpen,
    setIsOpen,
    CommandPaletteComponent: (
      <CommandPalette
        isOpen={isOpen}
        onClose={() => setIsOpen(false)}
        commands={commands}
      />
    ),
  };
}
