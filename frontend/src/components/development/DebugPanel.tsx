import React from 'react';
import { ChevronDownIcon, ChevronUpIcon } from '@heroicons/react/24/outline';
import { Card } from '../ui/Card';
import { cn } from '../../utils/styles';

interface DebugPanelProps {
  data: unknown;
  title?: string;
  expanded?: boolean;
  className?: string;
}

export const DebugPanel: React.FC<DebugPanelProps> = ({
  data,
  title = 'Debug Info',
  expanded = false,
  className,
}) => {
  const [isExpanded, setIsExpanded] = React.useState(expanded);

  return (
    <Card
      variant="flat"
      className={cn('bg-secondary-50 overflow-hidden', className)}
    >
      <button
        type="button"
        className="flex w-full items-center justify-between p-4 text-left text-sm font-medium text-secondary-900 hover:bg-secondary-100"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <span>{title}</span>
        {isExpanded ? (
          <ChevronUpIcon className="h-5 w-5 text-secondary-500" />
        ) : (
          <ChevronDownIcon className="h-5 w-5 text-secondary-500" />
        )}
      </button>

      {isExpanded && (
        <div className="border-t border-secondary-200 bg-white p-4">
          <pre className="whitespace-pre-wrap text-xs text-secondary-700">
            {JSON.stringify(data, null, 2)}
          </pre>
        </div>
      )}
    </Card>
  );
};

interface QueryDebuggerProps {
  queryKey: unknown[];
  data: unknown;
  error: Error | null;
  isLoading: boolean;
  isFetching: boolean;
}

export const QueryDebugger: React.FC<QueryDebuggerProps> = ({
  queryKey,
  data,
  error,
  isLoading,
  isFetching,
}) => {
  return (
    <DebugPanel
      title="Query Debug"
      data={{
        queryKey,
        data,
        error: error ? { message: error.message, stack: error.stack } : null,
        state: {
          isLoading,
          isFetching,
        },
      }}
    />
  );
};

interface ActionLog<T, A> {
  timestamp: number;
  action: string;
  args: A[];
  stateBefore: T;
  stateAfter: T;
}

interface StoreDebuggerProps<T> {
  store: T;
  actions?: Record<string, (...args: unknown[]) => void>;
}

export function StoreDebugger<T>({ store, actions }: StoreDebuggerProps<T>): JSX.Element {
  const [actionLog, setActionLog] = React.useState<ActionLog<T, unknown>[]>([]);

  // Wrap actions to log their execution
  const wrappedActions = React.useMemo(() => {
    if (!actions) return {};

    return Object.entries(actions).reduce<Record<string, (...args: unknown[]) => unknown>>((acc, [name, action]) => {
      acc[name] = (...args: unknown[]) => {
        const stateBefore = { ...store };
        const result = action(...args);
        const stateAfter = { ...store };

        setActionLog((log) => [
          {
            timestamp: Date.now(),
            action: name,
            args,
            stateBefore,
            stateAfter,
          },
          ...log,
        ]);

        return result;
      };
      return acc;
    }, {});
  }, [actions, store]);

  return (
    <div className="space-y-4">
      <DebugPanel title="Store State" data={store} />
      {actions && (
        <DebugPanel
          title="Store Actions"
          data={{
            available: Object.keys(actions),
            wrapped: Object.keys(wrappedActions),
            log: actionLog,
          }}
        />
      )}
    </div>
  );
}
