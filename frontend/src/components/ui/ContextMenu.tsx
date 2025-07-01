import { Menu, Transition } from '@headlessui/react';
import { Fragment, useEffect, useState } from 'react';
import { cn } from '../../utils/styles';

interface Position {
  x: number;
  y: number;
}

interface ContextMenuProps {
  children: React.ReactNode;
  trigger: React.ReactNode;
  onOpen?: () => void;
  onClose?: () => void;
  className?: string;
  disabled?: boolean;
}

export function ContextMenu({
  children,
  trigger,
  onOpen,
  onClose,
  className,
  disabled = false,
}: ContextMenuProps) {
  const [position, setPosition] = useState<Position>({ x: 0, y: 0 });
  const [show, setShow] = useState(false);

  useEffect(() => {
    function handleResize() {
      if (show) {
        setShow(false);
      }
    }

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, [show]);

  useEffect(() => {
    if (show) {
      onOpen?.();
    } else {
      onClose?.();
    }
  }, [show, onOpen, onClose]);

  const handleContextMenu = (event: React.MouseEvent) => {
    if (disabled) return;

    event.preventDefault();

    const { clientX, clientY } = event;
    const menuWidth = 220;
    const menuHeight = 200;
    const windowWidth = window.innerWidth;
    const windowHeight = window.innerHeight;

    let adjustedX = clientX;
    let adjustedY = clientY;

    if (clientX + menuWidth > windowWidth) {
      adjustedX = windowWidth - menuWidth;
    }

    if (clientY + menuHeight > windowHeight) {
      adjustedY = windowHeight - menuHeight;
    }

    setPosition({ x: adjustedX, y: adjustedY });
    setShow(true);
  };

  return (
    <div>
      <div onContextMenu={handleContextMenu}>{trigger}</div>

      <Menu as="div" className="relative">
        <Transition
          show={show}
          as={Fragment}
          enter="transition ease-out duration-100"
          enterFrom="transform opacity-0 scale-95"
          enterTo="transform opacity-100 scale-100"
          leave="transition ease-in duration-75"
          leaveFrom="transform opacity-100 scale-100"
          leaveTo="transform opacity-0 scale-95"
        >
          <div
            className={cn(
              'fixed z-50 w-56 origin-top-right divide-y divide-gray-100 rounded-md bg-white shadow-lg ring-1 ring-black/5 focus:outline-none',
              className
            )}
            style={{
              left: `${position.x}px`,
              top: `${position.y}px`,
            }}
          >
            {children}
          </div>
        </Transition>
      </Menu>
    </div>
  );
}

const styles = {
  group: 'p-1',
  label: 'px-2 py-1.5 text-xs font-medium text-gray-500',
  item: ({ active, disabled }: { active: boolean; disabled?: boolean }) =>
    cn(
      'group flex w-full items-center px-2 py-1.5 text-sm focus:outline-none',
      active ? 'bg-primary-500 text-white' : 'text-gray-900',
      disabled && 'cursor-not-allowed opacity-50'
    ),
  iconLeft: ({ active }: { active: boolean }) =>
    cn(
      'mr-2 h-5 w-5',
      active ? 'text-white' : 'text-gray-400 group-hover:text-gray-500'
    ),
  iconRight: ({ active }: { active: boolean }) =>
    cn(
      'ml-2 h-5 w-5',
      active ? 'text-white' : 'text-gray-400 group-hover:text-gray-500'
    ),
};

export const ContextMenuStyles = styles;
