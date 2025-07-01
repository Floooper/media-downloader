import { useEffect, useRef, useState, useCallback } from 'react';

interface UseInfiniteScrollOptions {
  threshold?: number;
  rootMargin?: string;
  enabled?: boolean;
  loading?: boolean;
}

export function useInfiniteScroll(
  onLoadMore: () => void,
  options: UseInfiniteScrollOptions = {}
) {
  const {
    threshold = 0.8,
    rootMargin = '20px',
    enabled = true,
    loading = false,
  } = options;

  const [isIntersecting, setIsIntersecting] = useState(false);
  const observerRef = useRef<IntersectionObserver | null>(null);
  const targetRef = useRef<HTMLDivElement | null>(null);

  const handleObserver = useCallback(
    (entries: IntersectionObserverEntry[]) => {
      const [entry] = entries;
      setIsIntersecting(entry.isIntersecting);

      if (entry.isIntersecting && enabled && !loading) {
        onLoadMore();
      }
    },
    [enabled, loading, onLoadMore]
  );

  useEffect(() => {
    if (!enabled) return;

    const observer = new IntersectionObserver(handleObserver, {
      root: null,
      rootMargin,
      threshold,
    });

    observerRef.current = observer;

    const currentTarget = targetRef.current;
    if (currentTarget) {
      observer.observe(currentTarget);
    }

    return () => {
      if (currentTarget) {
        observer.unobserve(currentTarget);
      }
    };
  }, [enabled, rootMargin, threshold, handleObserver]);

  return {
    targetRef,
    isIntersecting,
  };
}

interface UseInfiniteScrollDataOptions<T> extends UseInfiniteScrollOptions {
  initialData?: T[];
  pageSize?: number;
  fetchFn: (page: number, pageSize: number) => Promise<T[]>;
}

export function useInfiniteScrollData<T>(
  options: UseInfiniteScrollDataOptions<T>
) {
  const {
    initialData = [],
    pageSize = 20,
    fetchFn,
    ...scrollOptions
  } = options;

  const [data, setData] = useState<T[]>(initialData);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(false);
  const [hasMore, setHasMore] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const loadMore = useCallback(async () => {
    if (loading || !hasMore) return;

    setLoading(true);
    setError(null);

    try {
      const newData = await fetchFn(page, pageSize);
      setData((prev) => [...prev, ...newData]);
      setHasMore(newData.length === pageSize);
      setPage((p) => p + 1);
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Failed to load data'));
    } finally {
      setLoading(false);
    }
  }, [fetchFn, hasMore, loading, page, pageSize]);

  const { targetRef, isIntersecting } = useInfiniteScroll(loadMore, {
    ...scrollOptions,
    loading,
    enabled: hasMore && !error,
  });

  const refresh = useCallback(async () => {
    setData([]);
    setPage(1);
    setHasMore(true);
    setError(null);

    try {
      const newData = await fetchFn(1, pageSize);
      setData(newData);
      setHasMore(newData.length === pageSize);
      setPage(2);
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Failed to refresh data'));
    }
  }, [fetchFn, pageSize]);

  return {
    data,
    loading,
    error,
    hasMore,
    targetRef,
    isIntersecting,
    refresh,
    loadMore,
  };
}

// Example usage:
// const {
//   data,
//   loading,
//   error,
//   hasMore,
//   targetRef,
//   refresh,
// } = useInfiniteScrollData({
//   fetchFn: async (page, pageSize) => {
//     const response = await api.getItems(page, pageSize);
//     return response.data;
//   },
//   pageSize: 20,
// });
//
// return (
//   <div>
//     {data.map((item) => (
//       <div key={item.id}>{item.name}</div>
//     ))}
//     {loading && <div>Loading...</div>}
//     {error && <div>Error: {error.message}</div>}
//     <div ref={targetRef} />
//   </div>
// );
