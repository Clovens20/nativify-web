/**
 * Simple in-memory cache for API responses
 * Helps reduce unnecessary API calls and improve performance
 */

interface CacheEntry<T> {
  data: T
  timestamp: number
  expiresAt: number
}

class APICache {
  private cache: Map<string, CacheEntry<any>> = new Map()
  private defaultTTL: number = 5 * 60 * 1000 // 5 minutes default

  /**
   * Get cached data if available and not expired
   */
  get<T>(key: string): T | null {
    const entry = this.cache.get(key)
    if (!entry) return null

    if (Date.now() > entry.expiresAt) {
      this.cache.delete(key)
      return null
    }

    return entry.data as T
  }

  /**
   * Set cache entry with optional TTL (time to live in ms)
   */
  set<T>(key: string, data: T, ttl: number = this.defaultTTL): void {
    const now = Date.now()
    this.cache.set(key, {
      data,
      timestamp: now,
      expiresAt: now + ttl,
    })
  }

  /**
   * Delete specific cache entry
   */
  delete(key: string): void {
    this.cache.delete(key)
  }

  /**
   * Clear all cache
   */
  clear(): void {
    this.cache.clear()
  }

  /**
   * Clear expired entries
   */
  clearExpired(): void {
    const now = Date.now()
    const keysToDelete: string[] = []
    
    // Collect expired keys first to avoid modifying Map during iteration
    this.cache.forEach((entry, key) => {
      if (now > entry.expiresAt) {
        keysToDelete.push(key)
      }
    })
    
    // Delete expired entries
    keysToDelete.forEach(key => this.cache.delete(key))
  }

  /**
   * Invalidate cache entries matching a pattern
   */
  invalidatePattern(pattern: string): void {
    const keysToDelete: string[] = []
    
    // Collect matching keys first to avoid modifying Map during iteration
    this.cache.forEach((_, key) => {
      if (key.includes(pattern)) {
        keysToDelete.push(key)
      }
    })
    
    // Delete matching entries
    keysToDelete.forEach(key => this.cache.delete(key))
  }
}

// Singleton instance
export const apiCache = new APICache()

// Auto-cleanup expired entries every minute
if (typeof window !== 'undefined') {
  setInterval(() => {
    apiCache.clearExpired()
  }, 60 * 1000)
}

