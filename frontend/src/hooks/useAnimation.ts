import { useRef, useState, useEffect, useCallback } from 'react';

type EasingFunction = (t: number) => number;

export const easings = {
  linear: (t: number) => t,
  easeInQuad: (t: number) => t * t,
  easeOutQuad: (t: number) => t * (2 - t),
  easeInOutQuad: (t: number) => (t < 0.5 ? 2 * t * t : -1 + (4 - 2 * t) * t),
  easeInCubic: (t: number) => t * t * t,
  easeOutCubic: (t: number) => --t * t * t + 1,
  easeInOutCubic: (t: number) =>
    t < 0.5 ? 4 * t * t * t : (t - 1) * (2 * t - 2) * (2 * t - 2) + 1,
  easeInElastic: (t: number) => {
    const c4 = (2 * Math.PI) / 3;
    return t === 0
      ? 0
      : t === 1
      ? 1
      : -Math.pow(2, 10 * t - 10) * Math.sin((t * 10 - 10.75) * c4);
  },
  easeOutElastic: (t: number) => {
    const c4 = (2 * Math.PI) / 3;
    return t === 0
      ? 0
      : t === 1
      ? 1
      : Math.pow(2, -10 * t) * Math.sin((t * 10 - 0.75) * c4) + 1;
  },
  easeInOutElastic: (t: number) => {
    const c5 = (2 * Math.PI) / 4.5;
    return t === 0
      ? 0
      : t === 1
      ? 1
      : t < 0.5
      ? -(Math.pow(2, 20 * t - 10) * Math.sin((20 * t - 11.125) * c5)) / 2
      : (Math.pow(2, -20 * t + 10) * Math.sin((20 * t - 11.125) * c5)) / 2 + 1;
  },
};

interface AnimationOptions {
  duration?: number;
  easing?: EasingFunction | keyof typeof easings;
  delay?: number;
  loop?: boolean;
  autoplay?: boolean;
  direction?: 'normal' | 'reverse' | 'alternate';
  onComplete?: () => void;
  onLoop?: () => void;
}

interface SpringOptions {
  stiffness?: number;
  damping?: number;
  mass?: number;
  precision?: number;
}

export function useAnimation(
  initialValueProp: number,
  targetValueProp: number,
  options: AnimationOptions = {}
) {
  const {
    duration = 1000,
    easing = 'linear',
    delay = 0,
    loop = false,
    autoplay = true,
    direction = 'normal',
    onComplete,
    onLoop,
  } = options;

  const [value, setValue] = useState(initialValueProp);
  const [isPlaying, setIsPlaying] = useState(autoplay);
  const [progress, setProgress] = useState(0);
  
  const initialValueRef = useRef(initialValueProp);
  const targetValueRef = useRef(targetValueProp);
  const animationRef = useRef<number>();
  const startTimeRef = useRef<number>();
  const easingFn = typeof easing === 'string' ? easings[easing] : easing;

  const animate = useCallback(
    (timestamp: number) => {
      if (!startTimeRef.current) {
        startTimeRef.current = timestamp;
      }

      const elapsed = timestamp - startTimeRef.current;
      let currentProgress = Math.min((elapsed - delay) / duration, 1);

      if (currentProgress < 0) {
        currentProgress = 0;
      }

      if (direction === 'reverse') {
        currentProgress = 1 - currentProgress;
      } else if (direction === 'alternate') {
        currentProgress = currentProgress <= 0.5 ? currentProgress * 2 : (1 - currentProgress) * 2;
      }

      const easedProgress = easingFn(currentProgress);
      const currentValue =
        initialValueRef.current + (targetValueRef.current - initialValueRef.current) * easedProgress;

      setValue(currentValue);
      setProgress(currentProgress);

      if (currentProgress < 1) {
        animationRef.current = requestAnimationFrame(animate);
      } else {
        if (loop) {
          startTimeRef.current = timestamp;
          animationRef.current = requestAnimationFrame(animate);
          onLoop?.();
        } else {
          setIsPlaying(false);
          onComplete?.();
        }
      }
    },
    [duration, delay, loop, direction, easingFn, onComplete, onLoop]
  );

  useEffect(() => {
    initialValueRef.current = initialValueProp;
    targetValueRef.current = targetValueProp;
  }, [initialValueProp, targetValueProp]);

  useEffect(() => {
    if (isPlaying) {
      startTimeRef.current = undefined;
      animationRef.current = requestAnimationFrame(animate);
    }
    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [isPlaying, animate]);

  const play = useCallback(() => {
    setIsPlaying(true);
  }, []);

  const pause = useCallback(() => {
    setIsPlaying(false);
  }, []);

  const stop = useCallback(() => {
    setIsPlaying(false);
    setValue(initialValueRef.current);
    setProgress(0);
  }, []);

  const reverse = useCallback(() => {
    setIsPlaying(true);
    const temp = initialValueRef.current;
    initialValueRef.current = targetValueRef.current;
    targetValueRef.current = temp;
  }, []);

  return {
    value,
    progress,
    isPlaying,
    play,
    pause,
    stop,
    reverse,
  };
}

export function useSpring(
  initialValue: number,
  targetValue: number,
  options: SpringOptions = {}
) {
  const {
    stiffness = 170,
    damping = 26,
    mass = 1,
    precision = 0.01,
  } = options;

  const [value, setValue] = useState(initialValue);
  const [velocity, setVelocity] = useState(0);
  const [isAnimating, setIsAnimating] = useState(true);

  const animationRef = useRef<number>();

  const animate = useCallback(() => {
    const force = -stiffness * (value - targetValue);
    const acceleration = force / mass;
    const newVelocity = (velocity + acceleration) * (1 - damping / 100);
    const newValue = value + newVelocity;

    if (
      Math.abs(newValue - targetValue) < precision &&
      Math.abs(newVelocity) < precision
    ) {
      setValue(targetValue);
      setVelocity(0);
      setIsAnimating(false);
      return;
    }

    setValue(newValue);
    setVelocity(newVelocity);
    animationRef.current = requestAnimationFrame(animate);
  }, [
    value,
    velocity,
    targetValue,
    stiffness,
    damping,
    mass,
    precision,
  ]);

  useEffect(() => {
    if (isAnimating) {
      animationRef.current = requestAnimationFrame(animate);
    }
    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [isAnimating, animate]);

  useEffect(() => {
    setIsAnimating(true);
  }, [targetValue]);

  return value;
}
