import React from 'react';
import { ChevronUpDownIcon, ChevronUpIcon, ChevronDownIcon } from '@heroicons/react/24/outline';
import { cn } from '../../utils/styles';

export type SortDirection = 'asc' | 'desc';

export interface Column<T> {
  key: string;
  header: React.ReactNode;
  cell: (item: T) => React.ReactNode;
  sortable?: boolean;
  width?: string | number;
  align?: 'left' | 'center' | 'right';
  className?: string;
}

interface TableProps<T> {
  data: T[];
  columns: Column<T>[];
  sortColumn?: string;
  sortDirection?: SortDirection;
  onSort?: (column: string, direction: SortDirection) => void;
  onRowClick?: (item: T) => void;
  isLoading?: boolean;
  emptyState?: React.ReactNode;
  selectedRows?: Set<string | number>;
  onRowSelect?: (id: string | number) => void;
  getRowId?: (item: T) => string | number;
  className?: string;
}

export function Table<T extends { id?: string | number }>({
  data,
  columns,
  sortColumn,
  sortDirection,
  onSort,
  onRowClick,
  isLoading,
  emptyState,
  selectedRows,
  onRowSelect,
  getRowId = (item: T) => item.id ?? '',
  className,
}: TableProps<T>) {
  const handleSort = (column: string) => {
    if (!onSort) return;

    const newDirection =
      sortColumn === column && sortDirection === 'asc' ? 'desc' : 'asc';
    onSort(column, newDirection);
  };

  const getSortIcon = (column: string) => {
    if (sortColumn !== column) {
      return <ChevronUpDownIcon className="h-4 w-4" />;
    }
    return sortDirection === 'asc' ? (
      <ChevronUpIcon className="h-4 w-4" />
    ) : (
      <ChevronDownIcon className="h-4 w-4" />
    );
  };

  if (data.length === 0 && !isLoading) {
    return emptyState || null;
  }

  return (
    <div className={cn('overflow-x-auto', className)}>
      <table className="min-w-full divide-y divide-secondary-200">
        <thead className="bg-secondary-50">
          <tr>
            {selectedRows && (
              <th scope="col" className="relative w-12 px-6 sm:w-16 sm:px-8">
                <input
                  type="checkbox"
                  className="absolute left-4 top-1/2 -mt-2 h-4 w-4 rounded border-secondary-300 text-primary-600 focus:ring-primary-600"
                  checked={
                    data.length > 0 &&
                    data.every((item) =>
                      selectedRows.has(getRowId(item))
                    )
                  }
                  onChange={(e) => {
                    if (!onRowSelect) return;
                    data.forEach((item) => {
                      const id = getRowId(item);
                      if (e.target.checked) {
                        onRowSelect(id);
                      } else {
                        onRowSelect(id);
                      }
                    });
                  }}
                />
              </th>
            )}
            {columns.map((column) => (
              <th
                key={column.key}
                scope="col"
                className={cn(
                  'py-3.5 pl-4 pr-3 text-left text-sm font-semibold text-secondary-900 sm:pl-6',
                  column.align === 'center' && 'text-center',
                  column.align === 'right' && 'text-right',
                  column.className
                )}
                style={{ width: column.width }}
              >
                {column.sortable ? (
                  <button
                    type="button"
                    className="group inline-flex items-center gap-x-1"
                    onClick={() => handleSort(column.key)}
                  >
                    {column.header}
                    <span className="ml-2 flex-none rounded text-secondary-400 group-hover:visible group-focus:visible">
                      {getSortIcon(column.key)}
                    </span>
                  </button>
                ) : (
                  column.header
                )}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-secondary-200 bg-white">
          {isLoading ? (
            <tr>
              <td
                colSpan={columns.length + (selectedRows ? 1 : 0)}
                className="px-3 py-4 text-sm text-secondary-500"
              >
                <div className="flex justify-center">
                  <svg
                    className="h-5 w-5 animate-spin text-secondary-500"
                    xmlns="http://www.w3.org/2000/svg"
                    fill="none"
                    viewBox="0 0 24 24"
                  >
                    <circle
                      className="opacity-25"
                      cx="12"
                      cy="12"
                      r="10"
                      stroke="currentColor"
                      strokeWidth="4"
                    />
                    <path
                      className="opacity-75"
                      fill="currentColor"
                      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                    />
                  </svg>
                </div>
              </td>
            </tr>
          ) : (
            data.map((item) => (
              <tr
                key={getRowId(item)}
                className={cn(
                  'hover:bg-secondary-50',
                  onRowClick && 'cursor-pointer'
                )}
                onClick={() => onRowClick?.(item)}
              >
                {selectedRows && (
                  <td className="relative w-12 px-6 sm:w-16 sm:px-8">
                    <input
                      type="checkbox"
                      className="absolute left-4 top-1/2 -mt-2 h-4 w-4 rounded border-secondary-300 text-primary-600 focus:ring-primary-600"
                      checked={selectedRows.has(getRowId(item))}
                      onChange={() => onRowSelect?.(getRowId(item))}
                    />
                  </td>
                )}
                {columns.map((column) => (
                  <td
                    key={column.key}
                    className={cn(
                      'whitespace-nowrap py-4 pl-4 pr-3 text-sm text-secondary-500 sm:pl-6',
                      column.align === 'center' && 'text-center',
                      column.align === 'right' && 'text-right',
                      column.className
                    )}
                  >
                    {column.cell(item)}
                  </td>
                ))}
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}

interface TablePaginationProps {
  currentPage: number;
  pageSize: number;
  totalItems: number;
  onPageChange: (page: number) => void;
  onPageSizeChange?: (pageSize: number) => void;
  pageSizeOptions?: number[];
  className?: string;
}

export const TablePagination: React.FC<TablePaginationProps> = ({
  currentPage,
  pageSize,
  totalItems,
  onPageChange,
  onPageSizeChange,
  pageSizeOptions = [10, 20, 30, 40, 50],
  className,
}) => {
  const totalPages = Math.ceil(totalItems / pageSize);
  const startItem = (currentPage - 1) * pageSize + 1;
  const endItem = Math.min(currentPage * pageSize, totalItems);

  return (
    <div
      className={cn(
        'flex items-center justify-between border-t border-secondary-200 bg-white px-4 py-3 sm:px-6',
        className
      )}
    >
      <div className="flex flex-1 justify-between sm:hidden">
        <button
          onClick={() => onPageChange(currentPage - 1)}
          disabled={currentPage === 1}
          className="relative inline-flex items-center rounded-md border border-secondary-300 bg-white px-4 py-2 text-sm font-medium text-secondary-700 hover:bg-secondary-50 disabled:opacity-50"
        >
          Previous
        </button>
        <button
          onClick={() => onPageChange(currentPage + 1)}
          disabled={currentPage === totalPages}
          className="relative ml-3 inline-flex items-center rounded-md border border-secondary-300 bg-white px-4 py-2 text-sm font-medium text-secondary-700 hover:bg-secondary-50 disabled:opacity-50"
        >
          Next
        </button>
      </div>
      <div className="hidden sm:flex sm:flex-1 sm:items-center sm:justify-between">
        <div>
          <p className="text-sm text-secondary-700">
            Showing <span className="font-medium">{startItem}</span> to{' '}
            <span className="font-medium">{endItem}</span> of{' '}
            <span className="font-medium">{totalItems}</span> results
          </p>
        </div>
        <div className="flex items-center space-x-4">
          {onPageSizeChange && (
            <select
              value={pageSize}
              onChange={(e) => onPageSizeChange(Number(e.target.value))}
              className="rounded-md border-secondary-300 py-1.5 text-sm text-secondary-700 focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
            >
              {pageSizeOptions.map((size) => (
                <option key={size} value={size}>
                  {size} per page
                </option>
              ))}
            </select>
          )}
          <nav
            className="relative z-0 inline-flex -space-x-px rounded-md shadow-sm"
            aria-label="Pagination"
          >
            <button
              onClick={() => onPageChange(currentPage - 1)}
              disabled={currentPage === 1}
              className="relative inline-flex items-center rounded-l-md border border-secondary-300 bg-white px-2 py-2 text-sm font-medium text-secondary-500 hover:bg-secondary-50 disabled:opacity-50"
            >
              <span className="sr-only">Previous</span>
              <ChevronDownIcon className="h-5 w-5 rotate-90" aria-hidden="true" />
            </button>
            {/* Add page numbers here if needed */}
            <button
              onClick={() => onPageChange(currentPage + 1)}
              disabled={currentPage === totalPages}
              className="relative inline-flex items-center rounded-r-md border border-secondary-300 bg-white px-2 py-2 text-sm font-medium text-secondary-500 hover:bg-secondary-50 disabled:opacity-50"
            >
              <span className="sr-only">Next</span>
              <ChevronDownIcon className="h-5 w-5 -rotate-90" aria-hidden="true" />
            </button>
          </nav>
        </div>
      </div>
    </div>
  );
};
