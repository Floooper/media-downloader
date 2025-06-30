// Log levels
export enum LogLevel {
    DEBUG = 'debug',
    INFO = 'info',
    WARN = 'warn',
    ERROR = 'error'
}

// Interface for structured log messages
interface LogMessage {
    level: LogLevel;
    message: string;
    timestamp: string;
    data?: any;
}

// Function to create a log message
const createLogMessage = (level: LogLevel, message: string, data?: any): LogMessage => ({
    level,
    message,
    timestamp: new Date().toISOString(),
    data
});

// Log functions
export const logDebug = (message: string, data?: any) => {
    const logMessage = createLogMessage(LogLevel.DEBUG, message, data);
    console.debug(message, data);
};

export const logInfo = (message: string, data?: any) => {
    const logMessage = createLogMessage(LogLevel.INFO, message, data);
    console.info(message, data);
};

export const logWarn = (message: string, data?: any) => {
    const logMessage = createLogMessage(LogLevel.WARN, message, data);
    console.warn(message, data);
};

export const logError = (message: string, error?: any) => {
    const logMessage = createLogMessage(LogLevel.ERROR, message, error);
    console.error(message, error);
};
