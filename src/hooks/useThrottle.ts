import { useRef, useCallback } from 'react'

/**
 * Custom hook for throttling function calls
 * @param callback - Function to throttle
 * @param delay - Delay in milliseconds
 * @returns Throttled function
 */
export function useThrottle<T extends (...args: any[]) => any>(
  callback: T,
  delay: number = 300
): T {
  const lastRan = useRef<number>(Date.now())

  return useCallback(
    ((...args: any[]) => {
      const handler = setTimeout(() => {
        if (Date.now() - lastRan.current >= delay) {
          callback(...args)
          lastRan.current = Date.now()
        }
      }, delay - (Date.now() - lastRan.current))

      return () => {
        clearTimeout(handler)
      }
    }) as T,
    [callback, delay]
  )
}

