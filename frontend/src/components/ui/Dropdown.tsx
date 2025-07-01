import React from 'react';
import { Menu, Transition } from '@headlessui/react';
import { ChevronDownIcon } from '@heroicons/react/24/outline';
import { cn } from '../../utils/styles';

export interface DropdownItem {
  label: string;
  value: string;
  icon?: React.ReactNode;
  disabled?: boolean;
  onClick?: () => void;
}

interface DropdownProps {
  label: string;
  items: DropdownItem[];
  icon?: React.ReactNode;
  variant?: 'primary' | 'secondary' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
  fullWidth?: boolean;
  disabled?: boolean;
  align?: 'left' | 'right';
  className?: string;
}

const variants = {
  primary: 'bg-primary-600 text-white hover:bg-primary-700 focus-visible:ring-primary-500',
  secondary: 'bg-white text-secondary-900 ring-1 ring-inset ring-secondary-300 hover:bg-secondary-50',
  ghost: 'bg-transparent text-secondary-700 hover:bg-secondary-50 hover:text-secondary-900',
};

const sizes = {
  sm: 'px-2.5 py-1.5 text-sm',
  md: 'px-3 py-2 text-sm',
  lg: 'px-4 py-2 text-base',
};

export const Dropdown: React.FC<DropdownProps> = ({
  label,
  items,
  icon,
  variant = 'primary',
  size = 'md',
  fullWidth = false,
  disabled = false,
  align = 'right',
  className,
}) => {
  return (
    <Menu as="div" className={cn('relative inline-block text-left', { 'w-full': fullWidth }, className)}>
      <Menu.Button
        className={cn(
          'inline-flex items-center justify-center rounded-md font-semibold focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 disabled:opacity-50',
          variants[variant],
          sizes[size],
          { 'w-full': fullWidth }
        )}
        disabled={disabled}
      >
        {icon && <span className="mr-2">{icon}</span>}
        {label}
        <ChevronDownIcon className="ml-2 -mr-1 h-5 w-5" aria-hidden="true" />
      </Menu.Button>

      <Transition
        as={React.Fragment}
        enter="transition ease-out duration-100"
        enterFrom="transform opacity-0 scale-95"
        enterTo="transform opacity-100 scale-100"
        leave="transition ease-in duration-75"
        leaveFrom="transform opacity-100 scale-100"
        leaveTo="transform opacity-0 scale-95"
      >
        <Menu.Items
          className={cn(
            'absolute z-10 mt-2 w-56 rounded-md bg-white shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none',
            {
              'right-0 origin-top-right': align === 'right',
              'left-0 origin-top-left': align === 'left',
            }
          )}
        >
          <div className="py-1">
            {items.map((item) => (
              <Menu.Item key={item.value}>
                {({ active }) => (
                  <button
                    onClick={item.onClick}
                    className={cn(
                      'flex w-full items-center px-4 py-2 text-sm',
                      {
                        'bg-secondary-100 text-secondary-900': active,
                        'text-secondary-700': !active,
                        'opacity-50 cursor-not-allowed': item.disabled,
                      }
                    )}
                    disabled={item.disabled}
                  >
                    {item.icon && (
                      <span className="mr-3 h-5 w-5" aria-hidden="true">
                        {item.icon}
                      </span>
                    )}
                    {item.label}
                  </button>
                )}
              </Menu.Item>
            ))}
          </div>
        </Menu.Items>
      </Transition>
    </Menu>
  );
};

interface DropdownMenuProps {
  children: React.ReactNode;
  items: DropdownItem[];
  align?: 'left' | 'right';
}

export const DropdownMenu: React.FC<DropdownMenuProps> = ({
  children,
  items,
  align = 'right',
}) => {
  return (
    <Menu as="div" className="relative inline-block text-left">
      <Menu.Button as={React.Fragment}>{children}</Menu.Button>

      <Transition
        as={React.Fragment}
        enter="transition ease-out duration-100"
        enterFrom="transform opacity-0 scale-95"
        enterTo="transform opacity-100 scale-100"
        leave="transition ease-in duration-75"
        leaveFrom="transform opacity-100 scale-100"
        leaveTo="transform opacity-0 scale-95"
      >
        <Menu.Items
          className={cn(
            'absolute z-10 mt-2 w-56 rounded-md bg-white shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none',
            {
              'right-0 origin-top-right': align === 'right',
              'left-0 origin-top-left': align === 'left',
            }
          )}
        >
          <div className="py-1">
            {items.map((item) => (
              <Menu.Item key={item.value}>
                {({ active }) => (
                  <button
                    onClick={item.onClick}
                    className={cn(
                      'flex w-full items-center px-4 py-2 text-sm',
                      {
                        'bg-secondary-100 text-secondary-900': active,
                        'text-secondary-700': !active,
                        'opacity-50 cursor-not-allowed': item.disabled,
                      }
                    )}
                    disabled={item.disabled}
                  >
                    {item.icon && (
                      <span className="mr-3 h-5 w-5" aria-hidden="true">
                        {item.icon}
                      </span>
                    )}
                    {item.label}
                  </button>
                )}
              </Menu.Item>
            ))}
          </div>
        </Menu.Items>
      </Transition>
    </Menu>
  );
};
