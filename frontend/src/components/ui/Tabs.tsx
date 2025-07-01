import React from 'react';
import { Tab } from '@headlessui/react';
import { cn } from '../../utils/styles';

interface TabItem {
  key: string;
  label: React.ReactNode;
  content: React.ReactNode;
  icon?: React.ReactNode;
  disabled?: boolean;
}

interface TabsProps {
  items: TabItem[];
  defaultIndex?: number;
  onChange?: (index: number) => void;
  variant?: 'line' | 'pill' | 'enclosed';
  className?: string;
}

export const Tabs: React.FC<TabsProps> = ({
  items,
  defaultIndex = 0,
  onChange,
  variant = 'line',
  className,
}) => {
  const variantStyles = {
    line: {
      list: 'border-b border-secondary-200',
      tab: 'border-b-2 border-transparent py-4 px-1 text-sm font-medium text-secondary-500 hover:border-secondary-300 hover:text-secondary-700',
      selected:
        '!border-primary-500 !text-primary-600',
      disabled:
        'cursor-not-allowed opacity-50',
    },
    pill: {
      list: 'space-x-2',
      tab: 'rounded-md py-2 px-3 text-sm font-medium text-secondary-500 hover:bg-secondary-100 hover:text-secondary-700',
      selected:
        '!bg-primary-100 !text-primary-700',
      disabled:
        'cursor-not-allowed opacity-50',
    },
    enclosed: {
      list: 'space-x-1',
      tab: 'rounded-t-lg border-t border-l border-r border-transparent py-2 px-3 text-sm font-medium text-secondary-500 hover:bg-secondary-50 hover:text-secondary-700',
      selected:
        'bg-white !border-secondary-200 !text-secondary-900',
      disabled:
        'cursor-not-allowed opacity-50',
    },
  };

  return (
    <Tab.Group defaultIndex={defaultIndex} onChange={onChange}>
      <Tab.List className={cn('flex', variantStyles[variant].list, className)}>
        {items.map((item) => (
          <Tab
            key={item.key}
            disabled={item.disabled}
            className={({ selected }) =>
              cn(
                variantStyles[variant].tab,
                'focus:outline-none',
                selected && variantStyles[variant].selected,
                item.disabled && variantStyles[variant].disabled
              )
            }
          >
            <div className="flex items-center space-x-2">
              {item.icon && <span className="h-5 w-5">{item.icon}</span>}
              <span>{item.label}</span>
            </div>
          </Tab>
        ))}
      </Tab.List>
      <Tab.Panels className="mt-2">
        {items.map((item) => (
          <Tab.Panel
            key={item.key}
            className={cn(
              'rounded-xl focus:outline-none',
              variant === 'enclosed' && 'border border-secondary-200 bg-white p-4'
            )}
          >
            {item.content}
          </Tab.Panel>
        ))}
      </Tab.Panels>
    </Tab.Group>
  );
};

interface VerticalTabsProps extends Omit<TabsProps, 'variant'> {
  sideWidth?: string;
}

export const VerticalTabs: React.FC<VerticalTabsProps> = ({
  items,
  defaultIndex = 0,
  onChange,
  sideWidth = '200px',
  className,
}) => {
  return (
    <Tab.Group
      defaultIndex={defaultIndex}
      onChange={onChange}
      vertical
      className={cn('flex space-x-4', className)}
    >
      <Tab.List
        className="flex flex-col space-y-1"
        style={{ width: sideWidth }}
      >
        {items.map((item) => (
          <Tab
            key={item.key}
            disabled={item.disabled}
            className={({ selected }) =>
              cn(
                'group flex items-center rounded-md px-3 py-2 text-sm font-medium text-secondary-700 hover:bg-secondary-50 hover:text-secondary-900',
                'focus:outline-none',
                selected && 'bg-primary-50 text-primary-700',
                item.disabled && 'cursor-not-allowed opacity-50'
              )
            }
          >
            {item.icon && (
              <span className="mr-3 h-5 w-5 text-secondary-400 group-hover:text-secondary-500">
                {item.icon}
              </span>
            )}
            {item.label}
          </Tab>
        ))}
      </Tab.List>
      <Tab.Panels className="flex-1">
        {items.map((item) => (
          <Tab.Panel
            key={item.key}
            className="rounded-xl focus:outline-none"
          >
            {item.content}
          </Tab.Panel>
        ))}
      </Tab.Panels>
    </Tab.Group>
  );
};
