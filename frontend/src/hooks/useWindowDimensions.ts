import { useState, useEffect } from 'react';

interface WindowDimensions {
  width: number;
  height: number;
  isMobile: boolean;
  isTablet: boolean;
  isDesktop: boolean;
}

const BREAKPOINTS = {
  mobile: 640,
  tablet: 1024,
};

function getWindowDimensions(): WindowDimensions {
  const { innerWidth: width, innerHeight: height } = window;
  return {
    width,
    height,
    isMobile: width < BREAKPOINTS.mobile,
    isTablet: width >= BREAKPOINTS.mobile && width < BREAKPOINTS.tablet,
    isDesktop: width >= BREAKPOINTS.tablet,
  };
}

export function useWindowDimensions(): WindowDimensions {
  const [windowDimensions, setWindowDimensions] = useState<WindowDimensions>({
    width: 0,
    height: 0,
    isMobile: false,
    isTablet: false,
    isDesktop: true,
  });

  useEffect(() => {
    function handleResize() {
      setWindowDimensions(getWindowDimensions());
    }

    // Set initial dimensions
    handleResize();

    // Add event listener
    window.addEventListener('resize', handleResize);
    
    // Remove event listener on cleanup
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  return windowDimensions;
}

export function useBreakpoint(breakpoint: number): boolean {
  const { width } = useWindowDimensions();
  return width >= breakpoint;
}

export function useIsMobile(): boolean {
  const { isMobile } = useWindowDimensions();
  return isMobile;
}

export function useIsTablet(): boolean {
  const { isTablet } = useWindowDimensions();
  return isTablet;
}

export function useIsDesktop(): boolean {
  const { isDesktop } = useWindowDimensions();
  return isDesktop;
}
