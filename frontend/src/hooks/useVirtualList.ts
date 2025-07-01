import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useWindowDimensions } from './useWindowDimensions';

interface UseVirtualListOptions {
  itemHeight: number;
  overscan?: number;
  onEndReached?: () => void;
  endReachedThreshold?: number;
}

interface VirtualItem<T> {
  index: number;
  item: T;
  style: React.CSSProperties;
}

export function useVirtualList<T>(
  items: T[],
  options: UseVirtualListOptions
) {
  const {
    itemHeight,
    overscan = 3,
    onEndReached,
    endReachedThreshold = 0.8,
  } = options;

  const containerRef = useRef<HTMLDivElement>(null);
  const [scrollOffset, setScrollOffset] = useState(0);
  const { height: windowHeight } = useWindowDimensions();

  const containerHeight = useMemo(() => {
    return containerRef.current?.getBoundingClientRect().height || windowHeight;
  }, [windowHeight]);

  const totalHeight = useMemo(() => {
    return items.length * itemHeight;
  }, [items.length, itemHeight]);

  const visibleRange = useMemo(() => {
    const start = Math.floor(scrollOffset / itemHeight);
    const end = Math.min(
      items.length,
      Math.ceil((scrollOffset + containerHeight) / itemHeight)
    );

    return {
      start: Math.max(0, start - overscan),
      end: Math.min(items.length, end + overscan),
    };
  }, [scrollOffset, containerHeight, itemHeight, items.length, overscan]);

  const visibleItems = useMemo(() => {
    return items
      .slice(visibleRange.start, visibleRange.end)
      .map((item, index) => ({
        index: visibleRange.start + index,
        item,
        style: {
          position: 'absolute',
          top: (visibleRange.start + index) * itemHeight,
          height: itemHeight,
          left: 0,
          right: 0,
        },
      }));
  }, [items, visibleRange, itemHeight]);

  const handleScroll = useCallback(
    (event: React.UIEvent<HTMLDivElement>) => {
      const { scrollTop, scrollHeight, clientHeight } = event.currentTarget;
      setScrollOffset(scrollTop);

      // Check if we've reached the end
      if (onEndReached) {
        const threshold = scrollHeight * endReachedThreshold;
        if (scrollTop + clientHeight >= threshold) {
          onEndReached();
        }
      }
    },
    [onEndReached, endReachedThreshold]
  );

  const scrollToIndex = useCallback(
    (index: number, behavior: ScrollBehavior = 'auto') => {
      if (containerRef.current) {
        containerRef.current.scrollTo({
          top: index * itemHeight,
          behavior,
        });
      }
    },
    [itemHeight]
  );

  const scrollToItem = useCallback(
    (item: T, behavior: ScrollBehavior = 'auto') => {
      const index = items.indexOf(item);
      if (index !== -1) {
        scrollToIndex(index, behavior);
      }
    },
    [items, scrollToIndex]
  );

  useEffect(() => {
    const resizeObserver = new ResizeObserver(() => {
      if (containerRef.current) {
        setScrollOffset(containerRef.current.scrollTop);
      }
    });

    if (containerRef.current) {
      resizeObserver.observe(containerRef.current);
    }

    return () => resizeObserver.disconnect();
  }, []);

  return {
    containerRef,
    containerStyle: {
      position: 'relative' as const,
      height: '100%',
      overflow: 'auto',
    },
    totalSize: totalHeight,
    visibleItems,
    scrollToIndex,
    scrollToItem,
    handleScroll,
  };
}

interface UseVirtualGridOptions extends UseVirtualListOptions {
  itemWidth: number;
  columns: number;
}

interface VirtualGridItem<T> extends VirtualItem<T> {
  columnIndex: number;
  rowIndex: number;
}

export function useVirtualGrid<T>(
  items: T[],
  options: UseVirtualGridOptions
) {
  const {
    itemHeight,
    itemWidth,
    columns,
    overscan = 1,
    onEndReached,
    endReachedThreshold = 0.8,
  } = options;

  const containerRef = useRef<HTMLDivElement>(null);
  const [scrollOffset, setScrollOffset] = useState({ x: 0, y: 0 });
  const { width: windowWidth, height: windowHeight } = useWindowDimensions();

  const containerSize = useMemo(() => {
    return {
      width: containerRef.current?.getBoundingClientRect().width || windowWidth,
      height: containerRef.current?.getBoundingClientRect().height || windowHeight,
    };
  }, [windowWidth, windowHeight]);

  const totalSize = useMemo(() => {
    const rows = Math.ceil(items.length / columns);
    return {
      width: columns * itemWidth,
      height: rows * itemHeight,
    };
  }, [items.length, columns, itemWidth, itemHeight]);

  const visibleRange = useMemo(() => {
    const rowStart = Math.floor(scrollOffset.y / itemHeight);
    const rowEnd = Math.ceil((scrollOffset.y + containerSize.height) / itemHeight);
    const colStart = Math.floor(scrollOffset.x / itemWidth);
    const colEnd = Math.ceil((scrollOffset.x + containerSize.width) / itemWidth);

    return {
      rowStart: Math.max(0, rowStart - overscan),
      rowEnd: Math.min(Math.ceil(items.length / columns), rowEnd + overscan),
      colStart: Math.max(0, colStart - overscan),
      colEnd: Math.min(columns, colEnd + overscan),
    };
  }, [
    scrollOffset,
    containerSize,
    itemHeight,
    itemWidth,
    items.length,
    columns,
    overscan,
  ]);

  const visibleItems = useMemo(() => {
    const result: VirtualGridItem<T>[] = [];

    for (let rowIndex = visibleRange.rowStart; rowIndex < visibleRange.rowEnd; rowIndex++) {
      for (let colIndex = visibleRange.colStart; colIndex < visibleRange.colEnd; colIndex++) {
        const index = rowIndex * columns + colIndex;
        if (index >= items.length) break;

        result.push({
          index,
          columnIndex: colIndex,
          rowIndex,
          item: items[index],
          style: {
            position: 'absolute',
            top: rowIndex * itemHeight,
            left: colIndex * itemWidth,
            width: itemWidth,
            height: itemHeight,
          },
        });
      }
    }

    return result;
  }, [items, visibleRange, columns, itemWidth, itemHeight]);

  const handleScroll = useCallback(
    (event: React.UIEvent<HTMLDivElement>) => {
      const { scrollTop, scrollLeft, scrollHeight, clientHeight } = event.currentTarget;
      setScrollOffset({ x: scrollLeft, y: scrollTop });

      // Check if we've reached the end
      if (onEndReached) {
        const threshold = scrollHeight * endReachedThreshold;
        if (scrollTop + clientHeight >= threshold) {
          onEndReached();
        }
      }
    },
    [onEndReached, endReachedThreshold]
  );

  const scrollToIndex = useCallback(
    (index: number, behavior: ScrollBehavior = 'auto') => {
      if (containerRef.current) {
        const rowIndex = Math.floor(index / columns);
        const colIndex = index % columns;

        containerRef.current.scrollTo({
          top: rowIndex * itemHeight,
          left: colIndex * itemWidth,
          behavior,
        });
      }
    },
    [columns, itemHeight, itemWidth]
  );

  return {
    containerRef,
    containerStyle: {
      position: 'relative' as const,
      height: '100%',
      overflow: 'auto',
    },
    totalSize,
    visibleItems,
    scrollToIndex,
    handleScroll,
  };
}
