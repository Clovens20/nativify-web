/**
 * Structured logging utility for production
 * Replaces console.log/error with proper logging
 */

type LogLevel = 'debug' | 'info' | 'warn' | 'error'

interface LogContext {
  [key: string]: any
}

class Logger {
  private isDevelopment = process.env.NODE_ENV === 'development'
  private isProduction = process.env.NODE_ENV === 'production'

  private formatMessage(level: LogLevel, message: string, context?: LogContext): string {
    const timestamp = new Date().toISOString()
    const contextStr = context ? ` ${JSON.stringify(context)}` : ''
    
    if (this.isProduction) {
      // Structured JSON logging for production
      return JSON.stringify({
        timestamp,
        level: level.toUpperCase(),
        message,
        ...context
      })
    } else {
      // Human-readable logging for development
      return `[${timestamp}] [${level.toUpperCase()}] ${message}${contextStr}`
    }
  }

  debug(message: string, context?: LogContext): void {
    if (this.isDevelopment) {
      console.debug(this.formatMessage('debug', message, context))
    }
  }

  info(message: string, context?: LogContext): void {
    if (this.isDevelopment || this.isProduction) {
      console.info(this.formatMessage('info', message, context))
    }
  }

  warn(message: string, context?: LogContext): void {
    console.warn(this.formatMessage('warn', message, context))
  }

  error(message: string, error?: Error | unknown, context?: LogContext): void {
    const errorContext = {
      ...context,
      error: error instanceof Error ? {
        message: error.message,
        stack: error.stack,
        name: error.name
      } : error
    }
    console.error(this.formatMessage('error', message, errorContext))
    
    // In production, send to error tracking service (Sentry, etc.)
    if (this.isProduction && error) {
      // TODO: Integrate with Sentry or similar
      // Sentry.captureException(error, { extra: context })
    }
  }
}

export const logger = new Logger()

