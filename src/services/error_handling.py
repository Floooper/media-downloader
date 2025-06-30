"""
Comprehensive error handling and categorization for NZB downloads
"""
import asyncio
import nntplib
import socket
import ssl
import time
import logging
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass
from enum import Enum
from functools import wraps
import xml.etree.ElementTree as ET

logger = logging.getLogger(__name__)

class ErrorSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ErrorCategory(Enum):
    NNTP_SERVER = "nntp_server"
    NETWORK = "network"
    SSL_CONNECTION = "ssl_connection"
    YENC_DECODING = "yenc_decoding"
    FILE_SYSTEM = "file_system"
    NZB_FORMAT = "nzb_format"
    AUTHENTICATION = "authentication"
    UNKNOWN = "unknown"

@dataclass
class ErrorInfo:
    category: ErrorCategory
    severity: ErrorSeverity
    description: str
    retriable: bool
    action: str
    context: Dict[str, Any] = None

    def __post_init__(self):
        if self.context is None:
            self.context = {}

# Comprehensive error categorization
ERROR_PATTERNS = {
    # NNTP Server Errors
    "430": ErrorInfo(
        category=ErrorCategory.NNTP_SERVER,
        severity=ErrorSeverity.HIGH,
        description="Article not found (430)",
        retriable=False,
        action="Skip segment, try alternative sources"
    ),
    "480": ErrorInfo(
        category=ErrorCategory.AUTHENTICATION,
        severity=ErrorSeverity.CRITICAL,
        description="Authentication required (480)",
        retriable=False,
        action="Check credentials and server settings"
    ),
    "502": ErrorInfo(
        category=ErrorCategory.AUTHENTICATION,
        severity=ErrorSeverity.CRITICAL,
        description="Permission denied (502)",
        retriable=False,
        action="Check account permissions"
    ),
    "timeout": ErrorInfo(
        category=ErrorCategory.NETWORK,
        severity=ErrorSeverity.MEDIUM,
        description="Connection timeout",
        retriable=True,
        action="Retry with exponential backoff"
    ),
    "dns": ErrorInfo(
        category=ErrorCategory.NETWORK,
        severity=ErrorSeverity.HIGH,
        description="DNS resolution failed",
        retriable=True,
        action="Check DNS settings and server hostname"
    ),
    "ssl": ErrorInfo(
        category=ErrorCategory.SSL_CONNECTION,
        severity=ErrorSeverity.HIGH,
        description="SSL handshake failed",
        retriable=True,
        action="Check SSL settings and certificates, retry with fresh connection"
    ),
    "ssl_eof": ErrorInfo(
        category=ErrorCategory.SSL_CONNECTION,
        severity=ErrorSeverity.MEDIUM,
        description="SSL connection closed unexpectedly (EOF)",
        retriable=True,
        action="Recreate SSL connection and retry"
    ),
    "ssl_protocol": ErrorInfo(
        category=ErrorCategory.SSL_CONNECTION,
        severity=ErrorSeverity.HIGH,
        description="SSL protocol error",
        retriable=True,
        action="Try different SSL protocol version"
    ),
    "yenc_crc": ErrorInfo(
        category=ErrorCategory.YENC_DECODING,
        severity=ErrorSeverity.HIGH,
        description="yEnc CRC checksum mismatch",
        retriable=False,
        action="Data corruption, try alternative source"
    ),
    "yenc_headers": ErrorInfo(
        category=ErrorCategory.YENC_DECODING,
        severity=ErrorSeverity.HIGH,
        description="Missing yEnc headers (=ybegin, =yend)",
        retriable=False,
        action="Invalid yEnc format, check article content"
    ),
    "yenc_incomplete": ErrorInfo(
        category=ErrorCategory.YENC_DECODING,
        severity=ErrorSeverity.MEDIUM,
        description="Incomplete yEnc data",
        retriable=True,
        action="Retry download, may be temporary server issue"
    ),
    "disk_space": ErrorInfo(
        category=ErrorCategory.FILE_SYSTEM,
        severity=ErrorSeverity.CRITICAL,
        description="Insufficient disk space",
        retriable=False,
        action="Free disk space or change download location"
    ),
    "permission": ErrorInfo(
        category=ErrorCategory.FILE_SYSTEM,
        severity=ErrorSeverity.HIGH,
        description="File system permission denied",
        retriable=False,
        action="Check directory permissions"
    ),
    "nzb_invalid": ErrorInfo(
        category=ErrorCategory.NZB_FORMAT,
        severity=ErrorSeverity.CRITICAL,
        description="Invalid XML format in NZB",
        retriable=False,
        action="NZB file is corrupted"
    ),
    "nzb_empty": ErrorInfo(
        category=ErrorCategory.NZB_FORMAT,
        severity=ErrorSeverity.CRITICAL,
        description="No files found in NZB",
        retriable=False,
        action="Empty or invalid NZB file"
    )
}

def categorize_error(error: Exception, context: Dict = None) -> ErrorInfo:
    """Categorize an error and provide recommended actions"""
    if context is None:
        context = {}
    
    error_str = str(error).lower()
    error_type = type(error).__name__
    
    # SSL/TLS errors (prioritize these checks)
    if "ssl" in error_str and "eof" in error_str:
        info = ERROR_PATTERNS["ssl_eof"]
    elif "ssl" in error_str and ("closed" in error_str or "connection" in error_str):
        info = ERROR_PATTERNS["ssl_eof"]
    elif "tls" in error_str and ("closed" in error_str or "eof" in error_str):
        info = ERROR_PATTERNS["ssl_eof"]
    elif "_ssl.c" in error_str:
        info = ERROR_PATTERNS["ssl_eof"]
    elif "ssl" in error_str and "protocol" in error_str:
        info = ERROR_PATTERNS["ssl_protocol"]
    elif "ssl" in error_str or "certificate" in error_str:
        info = ERROR_PATTERNS["ssl"]
    # NNTP errors
    elif "430" in error_str or "no such article" in error_str:
        info = ERROR_PATTERNS["430"]
    elif "480" in error_str or "authentication" in error_str:
        info = ERROR_PATTERNS["480"]
    elif "502" in error_str or "permission denied" in error_str:
        info = ERROR_PATTERNS["502"]
    # Network errors
    elif "timeout" in error_str or error_type == "timeout":
        info = ERROR_PATTERNS["timeout"]
    elif "name resolution" in error_str or "dns" in error_str:
        info = ERROR_PATTERNS["dns"]
    # yEnc errors
    elif "crc" in error_str:
        info = ERROR_PATTERNS["yenc_crc"]
    elif "ybegin" in error_str or "yend" in error_str:
        info = ERROR_PATTERNS["yenc_headers"]
    elif "incomplete" in error_str or "truncated" in error_str:
        info = ERROR_PATTERNS["yenc_incomplete"]
    # File system errors
    elif "no space" in error_str or "disk full" in error_str:
        info = ERROR_PATTERNS["disk_space"]
    elif "permission" in error_str and "denied" in error_str:
        info = ERROR_PATTERNS["permission"]
    # NZB format errors
    elif "xml" in error_str and "invalid" in error_str:
        info = ERROR_PATTERNS["nzb_invalid"]
    elif "no files" in error_str or "empty" in error_str:
        info = ERROR_PATTERNS["nzb_empty"]
    # Default for unknown errors
    else:
        info = ErrorInfo(
            category=ErrorCategory.UNKNOWN,
            severity=ErrorSeverity.MEDIUM,
            description=f"Unknown error: {error_str[:100]}",
            retriable=True,
            action="Generic retry with backoff"
        )
    
    # Add context to error info
    info.context.update(context)
    return info

class NZBDownloadError(Exception):
    """Custom exception for NZB download errors"""
    def __init__(self, message: str, error_info: ErrorInfo, original_error: Exception = None):
        super().__init__(message)
        self.error_info = error_info
        self.original_error = original_error

def handle_nntp_errors(func):
    """Decorator to catch and classify NNTP errors"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except nntplib.NNTPError as e:
            error_info = categorize_error(e, {"function": func.__name__})
            raise NZBDownloadError(f"NNTP error in {func.__name__}: {str(e)}", error_info, e)
        except (socket.timeout, socket.gaierror, socket.error) as e:
            error_info = categorize_error(e, {"function": func.__name__})
            raise NZBDownloadError(f"Network error in {func.__name__}: {str(e)}", error_info, e)
        except ssl.SSLError as e:
            error_info = categorize_error(e, {"function": func.__name__})
            raise NZBDownloadError(f"SSL error in {func.__name__}: {str(e)}", error_info, e)
        except Exception as e:
            error_info = categorize_error(e, {"function": func.__name__})
            raise NZBDownloadError(f"Unexpected error in {func.__name__}: {str(e)}", error_info, e)
    return wrapper

def handle_yenc_errors(func):
    """Decorator to handle yEnc decoding errors"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            error_str = str(e).lower()
            if "crc" in error_str:
                error_info = ERROR_PATTERNS["yenc_crc"]
            elif "ybegin" in error_str or "yend" in error_str:
                error_info = ERROR_PATTERNS["yenc_headers"]
            elif "incomplete" in error_str:
                error_info = ERROR_PATTERNS["yenc_incomplete"]
            else:
                error_info = categorize_error(e, {"function": func.__name__})
            
            raise NZBDownloadError(f"yEnc decoding error in {func.__name__}: {str(e)}", error_info, e)
    return wrapper

def validate_nzb_content(nzb_content: str) -> Dict[str, Any]:
    """Validate NZB content and provide diagnostic information"""
    diagnostics = {
        "valid": False,
        "errors": [],
        "warnings": [],
        "file_count": 0,
        "segment_count": 0,
        "size_estimate": 0
    }
    
    try:
        # Handle escaped newlines in NZB content
        if "\\n" in nzb_content:
            nzb_content = nzb_content.replace("\\n", "\n")
        if "\\t" in nzb_content:
            nzb_content = nzb_content.replace("\\t", "\t")
        if "\\r" in nzb_content:
            nzb_content = nzb_content.replace("\\r", "\r")
            
        # Parse XML
        root = ET.fromstring(nzb_content)
        
        # Check if root element is 'nzb' (handle both with and without namespaces)
        if not (root.tag == 'nzb' or root.tag.endswith('}nzb')):
            diagnostics["errors"].append("Root element is not 'nzb'")
            return diagnostics
            
        # Get namespace if present
        namespace = ""
        if '}' in root.tag:
            namespace = "{" + root.tag.split('}')[0].strip('{') + "}"
            
        # Count files and segments (handle namespace)
        file_tag = f"{namespace}file" if namespace else "file"
        files = root.findall(f".//{file_tag}")
        diagnostics["file_count"] = len(files)
        
        if diagnostics["file_count"] == 0:
            diagnostics["errors"].append("No files found in NZB")
            return diagnostics
            
        total_segments = 0
        total_size = 0
        
        for file_elem in files:
            segment_tag = f"{namespace}segment" if namespace else "segment"
            segments = file_elem.findall(f".//{segment_tag}")
            segment_count = len(segments)
            total_segments += segment_count
            
            if segment_count == 0:
                diagnostics["warnings"].append(f"File '{file_elem.get('subject', 'unknown')}' has no segments")
                continue
                
            # Estimate size from segment info
            for segment in segments:
                try:
                    size = int(segment.get('bytes', 0))
                    total_size += size
                except (ValueError, TypeError):
                    diagnostics["warnings"].append("Invalid segment size information")
        
        diagnostics["segment_count"] = total_segments
        diagnostics["size_estimate"] = total_size
        diagnostics["valid"] = True
        
        if total_segments == 0:
            diagnostics["errors"].append("No segments found in any files")
            diagnostics["valid"] = False
            
    except ET.ParseError as e:
        diagnostics["errors"].append(f"XML parsing error: {str(e)}")
    except Exception as e:
        diagnostics["errors"].append(f"Unexpected validation error: {str(e)}")
    
    return diagnostics

class EnhancedRetryHandler:
    """Advanced retry handler with exponential backoff and error classification"""
    
    def __init__(self, max_retries: int = 3, base_delay: float = 1.0, max_delay: float = 60.0):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        
    def should_retry(self, error_info: ErrorInfo, attempt: int) -> bool:
        """Determine if an operation should be retried based on error info"""
        if attempt >= self.max_retries:
            return False
        
        # SSL connection errors are retriable with fresh connections
        if error_info.category == ErrorCategory.SSL_CONNECTION:
            return True
            
        return error_info.retriable
    
    def get_delay(self, attempt: int) -> float:
        """Calculate delay for exponential backoff"""
        delay = self.base_delay * (2 ** attempt)
        return min(delay, self.max_delay)
    
    def retry(self, func: Callable, *args, context: Dict = None, **kwargs):
        """Retry a sync function with exponential backoff"""
        if context is None:
            context = {}

        last_error = None

        for attempt in range(self.max_retries + 1):
            try:
                return func(*args, **kwargs)
            except NZBDownloadError as e:
                last_error = e

                if not self.should_retry(e.error_info, attempt):
                    logger.error(f"Non-retriable error in {func.__name__}: {e}")
                    raise
                
                if attempt < self.max_retries:
                    delay = self.get_delay(attempt)
                    logger.warning(f"Attempt {attempt + 1} failed for {func.__name__}: {e}. Retrying in {delay}s")
                    time.sleep(delay)
                else:
                    logger.error(f"All retry attempts exhausted for {func.__name__}: {e}")
                    raise
            except Exception as e:
                # Categorize unknown errors
                error_info = categorize_error(e, context)
                last_error = NZBDownloadError(f"Error in {func.__name__}: {str(e)}", error_info, e)
                
                if not self.should_retry(error_info, attempt):
                    logger.error(f"Non-retriable error in {func.__name__}: {e}")
                    raise last_error
                    
                if attempt < self.max_retries:
                    delay = self.get_delay(attempt)
                    logger.warning(f"Attempt {attempt + 1} failed for {func.__name__}: {e}. Retrying in {delay}s")
                    time.sleep(delay)
                else:
                    logger.error(f"All retry attempts exhausted for {func.__name__}: {e}")
                    raise last_error

        logger.error(f"Failed to complete {func.__name__} after retries. Last error: {last_error}")
        raise last_error
    
    async def retry_async(self, func: Callable, *args, context: Dict = None, **kwargs):
        """Retry an async function with exponential backoff"""
        if context is None:
            context = {}
            
        last_error = None
        
        for attempt in range(self.max_retries + 1):
            try:
                return await func(*args, **kwargs)
            except NZBDownloadError as e:
                last_error = e
                
                if not self.should_retry(e.error_info, attempt):
                    logger.error(f"Non-retriable error in {func.__name__}: {e}")
                    raise
                    
                if attempt < self.max_retries:
                    delay = self.get_delay(attempt)
                    logger.warning(f"Attempt {attempt + 1} failed for {func.__name__}: {e}. Retrying in {delay}s")
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"All retry attempts exhausted for {func.__name__}: {e}")
                    raise
            except Exception as e:
                # Categorize unknown errors
                error_info = categorize_error(e, context)
                last_error = NZBDownloadError(f"Error in {func.__name__}: {str(e)}", error_info, e)
                
                if not self.should_retry(error_info, attempt):
                    logger.error(f"Non-retriable error in {func.__name__}: {e}")
                    raise last_error
                    
                if attempt < self.max_retries:
                    delay = self.get_delay(attempt)
                    logger.warning(f"Attempt {attempt + 1} failed for {func.__name__}: {e}. Retrying in {delay}s")
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"All retry attempts exhausted for {func.__name__}: {e}")
                    raise last_error
                    
        raise last_error

def collect_diagnostic_info() -> Dict[str, Any]:
    """Collect diagnostic information about the environment"""
    import platform
    import psutil
    import socket
    
    return {
        "platform": platform.platform(),
        "python_version": platform.python_version(),
        "available_memory": psutil.virtual_memory().available,
        "disk_space": psutil.disk_usage('/').free,
        "network_interfaces": [iface for iface in socket.if_nameindex()],
        "timestamp": time.time()
    }

def log_error_with_context(error: NZBDownloadError, additional_context: Dict = None):
    """Log error with comprehensive context and suggestions"""
    context = error.error_info.context.copy()
    if additional_context:
        context.update(additional_context)
    
    logger.error(
        f"[{error.error_info.category.value.upper()}] {error.error_info.description}\n"
        f"Severity: {error.error_info.severity.value}\n"
        f"Retriable: {error.error_info.retriable}\n"
        f"Action: {error.error_info.action}\n"
        f"Context: {context}\n"
        f"Original Error: {error.original_error}"
    )
    
    # Provide specific suggestions based on error category
    if error.error_info.category == ErrorCategory.AUTHENTICATION:
        logger.info("💡 Suggestion: Check your NNTP server credentials in the configuration")
    elif error.error_info.category == ErrorCategory.NETWORK:
        logger.info("💡 Suggestion: Check your internet connection and DNS settings")
    elif error.error_info.category == ErrorCategory.SSL_CONNECTION:
        logger.info("💡 Suggestion: SSL connection issue - will retry with fresh connection")
    elif error.error_info.category == ErrorCategory.YENC_DECODING:
        logger.info("💡 Suggestion: This may indicate corrupt data - try downloading from a different server")
    elif error.error_info.category == ErrorCategory.FILE_SYSTEM:
        logger.info("💡 Suggestion: Check available disk space and directory permissions")
