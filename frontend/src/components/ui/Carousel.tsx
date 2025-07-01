import React, { useState, useCallback, useRef, useEffect } from 'react';
import { ChevronLeftIcon, ChevronRightIcon } from '@heroicons/react/24/outline';
import { cn } from '../../utils/styles';

interface CarouselProps {
  items: React.ReactNode[];
  initialIndex?: number;
  autoPlay?: boolean;
  interval?: number;
  showArrows?: boolean;
  showDots?: boolean;
  infinite?: boolean;
  className?: string;
  onSlideChange?: (index: number) => void;
}

export const Carousel: React.FC<CarouselProps> = ({
  items,
  initialIndex = 0,
  autoPlay = false,
  interval = 5000,
  showArrows = true,
  showDots = true,
  infinite = true,
  className,
  onSlideChange,
}) => {
  const [currentIndex, setCurrentIndex] = useState(initialIndex);
  const [isAnimating, setIsAnimating] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const timerRef = useRef<NodeJS.Timeout>();

  const goToSlide = useCallback(
    (index: number) => {
      if (isAnimating) return;

      setIsAnimating(true);
      let nextIndex = index;

      if (infinite) {
        if (index < 0) nextIndex = items.length - 1;
        if (index >= items.length) nextIndex = 0;
      } else {
        if (index < 0 || index >= items.length) return;
      }

      setCurrentIndex(nextIndex);
      if (onSlideChange) {
        onSlideChange(nextIndex);
      }
      setTimeout(() => setIsAnimating(false), 500);
    },
    [infinite, items.length, isAnimating, onSlideChange]
  );

  const nextSlide = useCallback(() => {
    goToSlide(currentIndex + 1);
  }, [currentIndex, goToSlide]);

  const previousSlide = useCallback(() => {
    goToSlide(currentIndex - 1);
  }, [currentIndex, goToSlide]);

  useEffect(() => {
    if (autoPlay && !isPaused) {
      timerRef.current = setInterval(nextSlide, interval);
      return () => clearInterval(timerRef.current);
    }
  }, [autoPlay, interval, isPaused, nextSlide]);

  const handleMouseEnter = () => {
    setIsPaused(true);
  };

  const handleMouseLeave = () => {
    setIsPaused(false);
  };

  return (
    <div
      className={cn('relative', className)}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
    >
      <div className="overflow-hidden">
        <div
          className="flex transition-transform duration-500 ease-in-out"
          style={{
            transform: `translateX(-${currentIndex * 100}%)`,
          }}
        >
          {items.map((item, index) => (
            <div
              key={index}
              className="w-full flex-shrink-0"
              aria-hidden={index !== currentIndex}
            >
              {item}
            </div>
          ))}
        </div>
      </div>

      {showArrows && (
        <>
          <button
            onClick={previousSlide}
            disabled={!infinite && currentIndex === 0}
            className={cn(
              'absolute left-4 top-1/2 -translate-y-1/2 rounded-full bg-white p-2 shadow-lg transition-all hover:bg-secondary-50',
              'focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2',
              (!infinite && currentIndex === 0) &&
                'cursor-not-allowed opacity-50'
            )}
          >
            <ChevronLeftIcon className="h-6 w-6 text-secondary-700" />
          </button>
          <button
            onClick={nextSlide}
            disabled={!infinite && currentIndex === items.length - 1}
            className={cn(
              'absolute right-4 top-1/2 -translate-y-1/2 rounded-full bg-white p-2 shadow-lg transition-all hover:bg-secondary-50',
              'focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2',
              (!infinite && currentIndex === items.length - 1) &&
                'cursor-not-allowed opacity-50'
            )}
          >
            <ChevronRightIcon className="h-6 w-6 text-secondary-700" />
          </button>
        </>
      )}

      {showDots && (
        <div className="absolute bottom-4 left-1/2 flex -translate-x-1/2 space-x-2">
          {items.map((_, index) => (
            <button
              key={index}
              onClick={() => goToSlide(index)}
              className={cn(
                'h-2 w-2 rounded-full transition-all',
                'focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2',
                index === currentIndex
                  ? 'bg-primary-500'
                  : 'bg-white/50 hover:bg-white'
              )}
            >
              <span className="sr-only">Go to slide {index + 1}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
};

interface InfiniteCarouselProps<T> extends Omit<CarouselProps, 'items'> {
  items: T[];
  renderItem: (item: T) => React.ReactNode;
  keyExtractor: (item: T) => string | number;
  onEndReached?: () => void;
  endReachedThreshold?: number;
}

export function InfiniteCarousel<T>({
  items,
  renderItem,
  keyExtractor,
  onEndReached,
  endReachedThreshold = 5,
  ...props
}: InfiniteCarouselProps<T>) {
  const [currentIndex, setCurrentIndex] = useState(props.initialIndex || 0);

  useEffect(() => {
    if (
      onEndReached &&
      items.length - currentIndex <= endReachedThreshold
    ) {
      onEndReached();
    }
  }, [currentIndex, items.length, onEndReached, endReachedThreshold]);

  const renderedItems = items.map((item) => (
    <div key={keyExtractor(item)}>
      {renderItem(item)}
    </div>
  ));

  return (
    <Carousel
      {...props}
      items={renderedItems}
      initialIndex={currentIndex}
      onSlideChange={setCurrentIndex}
    />
  );
}
