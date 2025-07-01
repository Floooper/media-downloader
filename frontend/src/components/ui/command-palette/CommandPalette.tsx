import React, { useState, useCallback, useEffect, useMemo } from 'react';
import { Dialog, Combobox } from '@headlessui/react';
import {
  MagnifyingGlassIcon,
  CommandLineIcon,
} from '@heroicons/react/24/outline';
import { cn } from '../../../utils/styles';
import type { CommandPaletteProps } from './types';

export const CommandPalette: React.FC<CommandPaletteProps> = ({
  isOpen,
  onClose,
  commands,
  placeholder = 'Search commands...',
  maxResults = 10,
}) => {
  const [query, setQuery] = useState('');

  useEffect(() => {
    if (!isOpen) {
      setQuery('');
    }
  }, [isOpen]);

  const filteredCommands = useMemo(() => {
    if (!query) return commands;

    const searchQuery = query.toLowerCase();
    return commands
      .filter((command) => {
        const searchableText = [
          command.name,
          command.description,
          command.category,
        ]
          .filter(Boolean)
          .join(' ')
          .toLowerCase();

        return searchableText.includes(searchQuery);
      })
      .slice(0, maxResults);
  }, [commands, query, maxResults]);

  const handleSelect = useCallback(
    (command: CommandItem) => {
      command.action();
      onClose();
    },
    [onClose]
  );

  return (
    <Dialog
      open={isOpen}
      onClose={onClose}
      className="fixed inset-0 z-50 overflow-y-auto p-4 pt-[25vh]"
    >
      <Dialog.Overlay className="fixed inset-0 bg-secondary-900/50" />

      <Combobox
        as="div"
        className="relative mx-auto max-w-xl rounded-xl bg-white shadow-2xl ring-1 ring-black/5"
        onChange={handleSelect}
      >
        <div className="flex items-center border-b border-secondary-200 px-4">
          <MagnifyingGlassIcon className="h-6 w-6 text-secondary-400" />
          <Combobox.Input
            className="h-12 w-full border-0 bg-transparent text-sm text-secondary-800 placeholder-secondary-400 focus:outline-none focus:ring-0"
            placeholder={placeholder}
            onChange={(event) => setQuery(event.target.value)}
          />
          {query.length === 0 && (
            <CommandLineIcon className="h-6 w-6 text-secondary-400" />
          )}
        </div>

        {filteredCommands.length > 0 && (
          <Combobox.Options
            static
            className="max-h-80 overflow-y-auto py-4 text-sm"
          >
            {filteredCommands.map((command) => (
              <Combobox.Option
                key={command.id}
                value={command}
                className={({ active }) =>
                  cn(
                    'flex cursor-pointer items-center justify-between px-4 py-2',
                    active && 'bg-primary-50'
                  )
                }
              >
                {({ active }) => (
                  <>
                    <div className="flex items-center">
                      {command.icon && (
                        <div
                          className={cn(
                            'mr-3 flex-shrink-0 text-secondary-400',
                            active && 'text-primary-600'
                          )}
                        >
                          {command.icon}
                        </div>
                      )}
                      <div>
                        <div
                          className={cn(
                            'font-medium text-secondary-900',
                            active && 'text-primary-600'
                          )}
                        >
                          {command.name}
                        </div>
                        {command.description && (
                          <div
                            className={cn(
                              'text-secondary-500',
                              active && 'text-primary-500'
                            )}
                          >
                            {command.description}
                          </div>
                        )}
                      </div>
                    </div>
                    {command.shortcut && (
                      <div
                        className={cn(
                          'flex items-center text-secondary-400',
                          active && 'text-primary-500'
                        )}
                      >
                        {command.shortcut.map((key, index) => (
                          <React.Fragment key={key}>
                            <kbd
                              className={cn(
                                'rounded px-1.5 font-mono text-xs',
                                active
                                  ? 'bg-primary-100 text-primary-500'
                                  : 'bg-secondary-100 text-secondary-500'
                              )}
                            >
                              {key}
                            </kbd>
                            {index < command.shortcut!.length - 1 && (
                              <span className="mx-1">+</span>
                            )}
                          </React.Fragment>
                        ))}
                      </div>
                    )}
                  </>
                )}
              </Combobox.Option>
            ))}
          </Combobox.Options>
        )}

        {query && filteredCommands.length === 0 && (
          <div className="py-14 px-6 text-center">
            <MagnifyingGlassIcon className="mx-auto h-6 w-6 text-secondary-400" />
            <p className="mt-4 text-sm text-secondary-900">
              No commands found for "{query}"
            </p>
          </div>
        )}
      </Combobox>
    </Dialog>
  );
};
