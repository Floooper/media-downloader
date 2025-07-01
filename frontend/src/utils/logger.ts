type LogLevel = 'debug' | 'info' | 'warn' | 'error';

type LogData = Record<string, unknown>;

interface ErrorLogData extends LogData {
  message?: string;
  stack?: string;
  source?: string;
  line?: number;
  column?: number;
}

interface LogEntry {
  timestamp: string;
  level: LogLevel;
  message: string;
  data?: LogData;
  stack?: string;
}

class Logger {
  private static instance: Logger;
  private logs: LogEntry[] = [];
  private maxLogs = 1000;
  private debugMode = process.env.NODE_ENV === 'development';

  private constructor() {
    // Initialize error handler for uncaught errors
    window.addEventListener('error', (event) => {
      this.error('Uncaught error', {
        message: event.error?.message,
        stack: event.error?.stack,
        source: event.filename,
        line: event.lineno,
        column: event.colno,
      });
    });

    // Initialize handler for unhandled promise rejections
    window.addEventListener('unhandledrejection', (event) => {
      this.error('Unhandled promise rejection', {
        reason: event.reason,
        stack: event.reason?.stack,
      });
    });
  }

  public static getInstance(): Logger {
    if (!Logger.instance) {
      Logger.instance = new Logger();
    }
    return Logger.instance;
  }

  private createLogEntry(
    level: LogLevel,
    message: string,
    data?: LogData
  ): LogEntry {
    const entry: LogEntry = {
      timestamp: new Date().toISOString(),
      level,
      message,
      data: data ? this.sanitizeData(data) : undefined,
    };

    if (level === 'error' && isErrorLogData(data) && data.stack) {
      entry.stack = data.stack;
    }

    return entry;
  }

  private sanitizeData(data: unknown): LogData | unknown {
    const sensitiveKeys = ['password', 'token', 'apiKey', 'secret', 'credentials'];
    
    if (!data) return data;

    if (typeof data === 'object' && data !== null) {
      const sanitized = Array.isArray(data) 
        ? [...data] as unknown[]
        : { ...data as Record<string, unknown> };
      
      Object.entries(sanitized).forEach(([key, value]) => {
        if (sensitiveKeys.some(sensitive => key.toLowerCase().includes(sensitive))) {
          sanitized[key] = '[REDACTED]';
        } else if (typeof value === 'object' && value !== null) {
          sanitized[key] = this.sanitizeData(value);
        }
      });

      return sanitized;
    }

    return data;
  }

  private addLog(entry: LogEntry) {
    this.logs.push(entry);
    if (this.logs.length > this.maxLogs) {
      this.logs.shift();
    }

    // In development, also log to console
    if (this.debugMode) {
      const consoleMethod = console[entry.level] || console.log;
      consoleMethod(
        `[${entry.timestamp}] ${entry.level.toUpperCase()}: ${entry.message}`,
        entry.data || '',
        entry.stack ? `\n${entry.stack}` : ''
      );
    }

    // You could also send logs to a server here
    void this.sendToServer(entry);
  }

  private async sendToServer(entry: LogEntry): Promise<void> {
    if (entry.level === 'error' || entry.level === 'warn') {
      try {
        const response = await fetch('/api/logs', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(entry),
        });

        if (!response.ok) {
          console.error('Failed to send log to server:', response.statusText);
        }
      } catch (error) {
        console.error('Failed to send log to server:', error);
      }
    }
  }

  public getLogs(): LogEntry[] {
    return [...this.logs];
  }

  public clearLogs(): void {
    this.logs = [];
  }

  public setDebugMode(enabled: boolean): void {
    this.debugMode = enabled;
  }

  public debug(message: string, data?: LogData): void {
    this.addLog(this.createLogEntry('debug', message, data));
  }

  public info(message: string, data?: LogData): void {
    this.addLog(this.createLogEntry('info', message, data));
  }

  public warn(message: string, data?: LogData): void {
    this.addLog(this.createLogEntry('warn', message, data));
  }

  public error(message: string, data?: ErrorLogData): void {
    this.addLog(this.createLogEntry('error', message, data));
  }
}

// Type guard for ErrorLogData
function isErrorLogData(data: unknown): data is ErrorLogData {
  return typeof data === 'object' && data !== null && 'stack' in data;
}

// Export a single logger instance
export const logger = Logger.getInstance();

// Export convenience functions
export const logDebug = (message: string, data?: LogData) => logger.debug(message, data);
export const logInfo = (message: string, data?: LogData) => logger.info(message, data);
export const logWarn = (message: string, data?: LogData) => logger.warn(message, data);
export const logError = (message: string, data?: ErrorLogData) => logger.error(message, data);

// Export the logger instance as default
export default logger;
