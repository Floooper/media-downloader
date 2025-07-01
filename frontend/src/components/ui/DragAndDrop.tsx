import React, { useRef } from 'react';
import { useDrag, useDrop, DndProvider } from 'react-dnd';
import { HTML5Backend } from 'react-dnd-html5-backend';
import { cn } from '../../utils/styles';

interface DraggableItemProps {
  id: string | number;
  index: number;
  onMove: (dragIndex: number, hoverIndex: number) => void;
  children: React.ReactNode;
  className?: string;
  disabled?: boolean;
}

const DraggableItem: React.FC<DraggableItemProps> = ({
  id,
  index,
  onMove,
  children,
  className,
  disabled = false,
}) => {
  const ref = useRef<HTMLDivElement>(null);

  const [{ isDragging }, drag] = useDrag({
    type: 'DRAGGABLE_ITEM',
    item: { id, index },
    collect: (monitor) => ({
      isDragging: monitor.isDragging(),
    }),
    canDrag: !disabled,
  });

  const [{ handlerId }, drop] = useDrop({
    accept: 'DRAGGABLE_ITEM',
    collect(monitor) {
      return {
        handlerId: monitor.getHandlerId(),
      };
    },
    hover(item: { id: string | number; index: number }, monitor) {
      if (disabled) return;
      if (!ref.current) return;

      const dragIndex = item.index;
      const hoverIndex = index;

      if (dragIndex === hoverIndex) return;

      const hoverBoundingRect = ref.current?.getBoundingClientRect();
      const hoverMiddleY = (hoverBoundingRect.bottom - hoverBoundingRect.top) / 2;
      const clientOffset = monitor.getClientOffset();
      const hoverClientY = clientOffset!.y - hoverBoundingRect.top;

      if (dragIndex < hoverIndex && hoverClientY < hoverMiddleY) return;
      if (dragIndex > hoverIndex && hoverClientY > hoverMiddleY) return;

      onMove(dragIndex, hoverIndex);
      item.index = hoverIndex;
    },
  });

  drag(drop(ref));

  return (
    <div
      ref={ref}
      className={cn(
        'transition-colors duration-200',
        isDragging && 'opacity-50',
        disabled && 'cursor-not-allowed opacity-50',
        !disabled && 'cursor-move',
        className
      )}
      data-handler-id={handlerId}
    >
      {children}
    </div>
  );
};

interface SortableListProps<T> {
  items: T[];
  onChange: (items: T[]) => void;
  renderItem: (item: T, index: number) => React.ReactNode;
  keyExtractor: (item: T) => string | number;
  className?: string;
  itemClassName?: string;
  disabled?: boolean;
}

export function SortableList<T>({
  items,
  onChange,
  renderItem,
  keyExtractor,
  className,
  itemClassName,
  disabled = false,
}: SortableListProps<T>) {
  const moveItem = (dragIndex: number, hoverIndex: number) => {
    const dragItem = items[dragIndex];
    const newItems = [...items];
    newItems.splice(dragIndex, 1);
    newItems.splice(hoverIndex, 0, dragItem);
    onChange(newItems);
  };

  return (
    <DndProvider backend={HTML5Backend}>
      <div className={className}>
        {items.map((item, index) => (
          <DraggableItem
            key={keyExtractor(item)}
            id={keyExtractor(item)}
            index={index}
            onMove={moveItem}
            className={itemClassName}
            disabled={disabled}
          >
            {renderItem(item, index)}
          </DraggableItem>
        ))}
      </div>
    </DndProvider>
  );
}

interface DroppableZoneProps {
  onDrop: (files: File[]) => void;
  children: React.ReactNode;
  accept?: string[];
  maxSize?: number;
  multiple?: boolean;
  disabled?: boolean;
  className?: string;
}

export const DroppableZone: React.FC<DroppableZoneProps> = ({
  onDrop,
  children,
  accept,
  maxSize,
  multiple = true,
  disabled = false,
  className,
}) => {
  const [{ canDrop, isOver }, drop] = useDrop({
    accept: 'FILE',
    collect: (monitor) => ({
      isOver: monitor.isOver(),
      canDrop: monitor.canDrop(),
    }),
    drop: (item: { files: File[] }) => {
      if (disabled) return;
      
      let files = item.files;
      
      if (accept) {
        files = files.filter((file) =>
          accept.some((type) =>
            type.startsWith('.')
              ? file.name.endsWith(type)
              : file.type.startsWith(type.replace('/*', ''))
          )
        );
      }

      if (maxSize) {
        files = files.filter((file) => file.size <= maxSize);
      }

      if (!multiple) {
        files = files.slice(0, 1);
      }

      onDrop(files);
    },
  });

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();

    if (disabled) return;

    const droppedFiles = Array.from(e.dataTransfer.files);
    let files = droppedFiles;

    if (accept) {
      files = files.filter((file) =>
        accept.some((type) =>
          type.startsWith('.')
            ? file.name.endsWith(type)
            : file.type.startsWith(type.replace('/*', ''))
        )
      );
    }

    if (maxSize) {
      files = files.filter((file) => file.size <= maxSize);
    }

    if (!multiple) {
      files = files.slice(0, 1);
    }

    onDrop(files);
  };

  return (
    <div
      ref={drop}
      onDragOver={handleDragOver}
      onDrop={handleDrop}
      className={cn(
        'relative rounded-lg border-2 border-dashed p-6 transition-colors',
        isOver && canDrop && 'border-primary-500 bg-primary-50',
        disabled && 'cursor-not-allowed opacity-50',
        !disabled && 'cursor-pointer hover:border-primary-400',
        className
      )}
    >
      {children}
      {isOver && canDrop && (
        <div className="absolute inset-0 flex items-center justify-center rounded-lg bg-primary-100 bg-opacity-50">
          <div className="text-lg font-medium text-primary-700">
            Drop files here
          </div>
        </div>
      )}
    </div>
  );
};

// Example usage:
// const items = [
//   { id: 1, name: 'Item 1' },
//   { id: 2, name: 'Item 2' },
//   { id: 3, name: 'Item 3' },
// ];
//
// return (
//   <SortableList
//     items={items}
//     onChange={setItems}
//     keyExtractor={(item) => item.id}
//     renderItem={(item) => (
//       <div className="p-4 bg-white shadow rounded">
//         {item.name}
//       </div>
//     )}
//   />
// );
//
// return (
//   <DroppableZone
//     onDrop={(files) => console.log(files)}
//     accept={['.pdf', 'image/*']}
//     maxSize={5 * 1024 * 1024}
//     multiple={true}
//   >
//     <div className="text-center">
//       <p>Drag and drop files here</p>
//       <p>or</p>
//       <button>Browse files</button>
//     </div>
//   </DroppableZone>
// );
