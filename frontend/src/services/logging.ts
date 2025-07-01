export enum LogLevel {
  DEBUG = 'debug',
  INFO = 'info',
  WARNING = 'warning',
  ERROR = 'error'
}

export type LogDetails = unknown;

export interface LogEntry {
  timestamp: Date;
  level: LogLevel;
  message: string;
  details?: LogDetails;
}

class Logger {
  private logs: LogEntry[] = [];
  private maxEntries = 1000;

  debug(message: string, details?: LogDetails) {
    this.log(LogLevel.DEBUG, message, details);
  }

  info(message: string, details?: LogDetails) {
    this.log(LogLevel.INFO, message, details);
  }

  warning(message: string, details?: LogDetails) {
    this.log(LogLevel.WARNING, message, details);
  }

  error(message: string, details?: LogDetails) {
    this.log(LogLevel.ERROR, message, details);
  }

  private log(level: LogLevel, message: string, details?: LogDetails) {
    const entry: LogEntry = {
      timestamp: new Date(),
      level,
      message,
      details
    };

    this.logs.unshift(entry);

    if (this.logs.length > this.maxEntries) {
      this.logs.pop();
    }
  }

  getLogs(): LogEntry[] {
    return this.logs;
  }

  clearLogs(): void {
    this.logs = [];
  }
}

const logger = new Logger();
export default logger;
