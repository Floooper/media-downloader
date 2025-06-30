import asyncio
import os
import logging
import aiofiles
import nntplib
import ssl
import socket
import tempfile
import xml.etree.ElementTree as ET
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass
from datetime import datetime
import threading
import queue
import time
import re
import concurrent.futures
import hashlib
import struct
from threading import Lock, Semaphore
from collections import defaultdict
from ..database import SessionLocal
from ..models.download import Download
import binascii

# Import our enhanced error handling
from .error_handling import (
    NZBDownloadError, 
    ErrorCategory, 
    ErrorSeverity,
    ErrorInfo,
    categorize_error,
    handle_nntp_errors, 
    handle_yenc_errors,
    validate_nzb_content,
    EnhancedRetryHandler,
    collect_diagnostic_info,
    log_error_with_context
)

# Configure logging for production
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

try:
    import pynzb
    HAS_PYNZB = True
    logger.info("✅ pynzb available for NZB parsing")
except ImportError:
    HAS_PYNZB = False
    logger.warning("⚠️ pynzb not available - NZB parsing will be limited")

try:
    import sabyenc3 as yenc
    HAS_YENC = True
    logger.info("✅ sabyenc3 available for yEnc decoding")
except ImportError:
    try:
        import yenc
        HAS_YENC = True
        logger.info("✅ yenc available for yEnc decoding")
    except ImportError:
        HAS_YENC = False
        logger.warning("⚠️ No yEnc library available - will use manual decoder")

@dataclass
class SegmentInfo:
    """Information about a segment"""
    number: int
    size: int
    message_id: str
    crc: Optional[str] = None

@dataclass
class FileInfo:
    """Information about a file in NZB"""
    name: str
    size: int
    segments: List[SegmentInfo]
    poster: Optional[str] = None
    date: Optional[datetime] = None

@dataclass 
class ServerConfig:
    """NNTP server configuration"""
    host: str
    port: int = 119
    username: str = ""
    password: str = ""
    ssl_enabled: bool = False
    connections: int = 8
    timeout: int = 30

class EnhancedNZBService:
    """Enhanced NZB service with comprehensive error handling"""
    
    def __init__(self, server_config: ServerConfig, download_dir: str = "/tmp/nzb_downloads"):
        self.server_config = server_config
        self.download_dir = download_dir
        self.connection_pool = []
        self.pool_lock = threading.Lock()
        self.connection_semaphore = Semaphore(server_config.connections)
        self.retry_handler = EnhancedRetryHandler(max_retries=3, base_delay=1.0, max_delay=30.0)
        
        # Statistics tracking
        self.stats = {
            'total_segments': 0,
            'successful_segments': 0,
            'failed_segments': 0,
            'retries_used': 0,
            'bytes_downloaded': 0,
            'errors_by_category': defaultdict(int)
        }
        
        # Ensure download directory exists
        os.makedirs(download_dir, exist_ok=True)
        
        logger.info(f"EnhancedNZBService initialized with {server_config.connections} connections to {server_config.host}:{server_config.port}")

    @handle_nntp_errors
    def _create_connection(self) -> nntplib.NNTP:
        """Create a new NNTP connection with enhanced error handling"""
        try:
            if self.server_config.ssl_enabled:
                context = ssl.create_default_context()
                connection = nntplib.NNTP_SSL(
                    self.server_config.host,
                    self.server_config.port,
                    user=self.server_config.username,
                    password=self.server_config.password,
                    ssl_context=context,
                    timeout=self.server_config.timeout
                )
            else:
                connection = nntplib.NNTP(
                    self.server_config.host,
                    self.server_config.port,
                    user=self.server_config.username,
                    password=self.server_config.password,
                    timeout=self.server_config.timeout
                )
            
            logger.debug(f"✅ Created NNTP connection to {self.server_config.host}")
            return connection
            
        except Exception as e:
            logger.error(f"❌ Failed to create NNTP connection: {e}")
            raise

    def _get_connection(self) -> nntplib.NNTP:
        """Get a connection from the pool or create a new one"""
        with self.pool_lock:
            if self.connection_pool:
                return self.connection_pool.pop()
            else:
                return self._create_connection()

    def _return_connection(self, connection: nntplib.NNTP):
        """Return a connection to the pool"""
        with self.pool_lock:
            if len(self.connection_pool) < self.server_config.connections:
                self.connection_pool.append(connection)
            else:
                try:
                    connection.quit()
                except:
                    pass

    async def parse_nzb_with_validation(self, nzb_path: str) -> List[FileInfo]:
        """Parse NZB file with comprehensive validation and error handling"""
        try:
            async with aiofiles.open(nzb_path, 'r', encoding='utf-8') as f:
                nzb_content = await f.read()
            
            # Validate NZB content
            validation_result = validate_nzb_content(nzb_content)
            
            if not validation_result["valid"]:
                error_info = ErrorInfo(
                    category=ErrorCategory.NZB_FORMAT,
                    severity=ErrorSeverity.CRITICAL,
                    description=f"Invalid NZB file: {', '.join(validation_result['errors'])}",
                    retriable=False,
                    action="Check NZB file format and integrity"
                )
                raise NZBDownloadError(f"NZB validation failed: {validation_result['errors']}", error_info)
            
            # Log validation results
            logger.info(f"📊 NZB validation successful: {validation_result['file_count']} files, "
                       f"{validation_result['segment_count']} segments, "
                       f"~{validation_result['size_estimate'] / (1024*1024):.1f} MB")
            
            if validation_result["warnings"]:
                logger.warning(f"⚠️ NZB warnings: {', '.join(validation_result['warnings'])}")
            
            # Parse with pynzb if available
            if HAS_PYNZB:
                return await self._parse_with_pynzb(nzb_content)
            else:
                return await self._parse_with_etree(nzb_content)
                
        except NZBDownloadError:
            raise
        except Exception as e:
            error_info = categorize_error(e, {"nzb_path": nzb_path})
            raise NZBDownloadError(f"Failed to parse NZB file {nzb_path}: {str(e)}", error_info, e)

    async def _parse_with_pynzb(self, nzb_content: str) -> List[FileInfo]:
        """Parse NZB using pynzb library"""
        try:
            nzb_files = pynzb.nzb_parser.parse(nzb_content)
            files = []
            
            for nzb_file in nzb_files:
                segments = []
                for segment in nzb_file.segments:
                    segments.append(SegmentInfo(
                        number=segment.number,
                        size=segment.bytes,
                        message_id=segment.message_id
                    ))
                
                files.append(FileInfo(
                    name=nzb_file.filename,
                    size=sum(s.size for s in segments),
                    segments=segments,
                    poster=nzb_file.poster,
                    date=nzb_file.date
                ))
            
            return files
            
        except Exception as e:
            error_info = categorize_error(e, {"parser": "pynzb"})
            raise NZBDownloadError(f"pynzb parsing failed: {str(e)}", error_info, e)

    async def _parse_with_etree(self, nzb_content: str) -> List[FileInfo]:
        """Parse NZB using ElementTree as fallback"""
        try:
            root = ET.fromstring(nzb_content)
            files = []
            
            for file_elem in root.findall('.//file'):
                segments = []
                for segment_elem in file_elem.findall('.//segment'):
                    try:
                        segment_number = int(segment_elem.get('number', 0))
                        segment_size = int(segment_elem.get('bytes', 0))
                        message_id = segment_elem.text.strip()
                        
                        segments.append(SegmentInfo(
                            number=segment_number,
                            size=segment_size,
                            message_id=message_id
                        ))
                    except (ValueError, AttributeError) as e:
                        logger.warning(f"⚠️ Skipping invalid segment: {e}")
                        continue
                
                if segments:
                    files.append(FileInfo(
                        name=file_elem.get('subject', 'unknown'),
                        size=sum(s.size for s in segments),
                        segments=segments,
                        poster=file_elem.get('poster')
                    ))
            
            return files
            
        except Exception as e:
            error_info = categorize_error(e, {"parser": "etree"})
            raise NZBDownloadError(f"ElementTree parsing failed: {str(e)}", error_info, e)

    @handle_yenc_errors
    def _decode_yenc_data(self, data: bytes) -> bytes:
        """Decode yEnc data with enhanced error handling"""
        if not data:
            raise NZBDownloadError("Empty data for yEnc decoding", 
                                 ErrorInfo(ErrorCategory.YENC_DECODING, ErrorSeverity.HIGH, 
                                         "Empty data", False, "Check segment download"))
        
        # Try fast library first
        if HAS_YENC:
            try:
                if hasattr(yenc, 'decode'):
                    decoded, crc = yenc.decode(data)
                    return decoded
                else:
                    # sabyenc3 format
                    result = yenc.decode_usenet_chunks([data])
                    return result[0]
            except Exception as e:
                logger.warning(f"⚠️ Fast yEnc decode failed, falling back to manual: {e}")
        
        # Manual yEnc decoder as fallback
        return self._manual_yenc_decode(data)

    def _manual_yenc_decode(self, data: bytes) -> bytes:
        """Manual yEnc decoder implementation"""
        try:
            lines = data.decode('latin1').split('\n')
            
            # Find ybegin line
            ybegin_line = None
            data_start = 0
            for i, line in enumerate(lines):
                if line.startswith('=ybegin'):
                    ybegin_line = line
                    data_start = i + 1
                    break
            
            if not ybegin_line:
                raise ValueError("No =ybegin line found")
            
            # Extract size info
            size_match = re.search(r'size=(\d+)', ybegin_line)
            if size_match:
                expected_size = int(size_match.group(1))
            else:
                expected_size = None
            
            # Find yend line
            yend_line = None
            data_end = len(lines)
            for i in range(len(lines) - 1, -1, -1):
                if lines[i].startswith('=yend'):
                    yend_line = lines[i]
                    data_end = i
                    break
            
            if not yend_line:
                raise ValueError("No =yend line found")
            
            # Decode data lines
            decoded_data = bytearray()
            for line in lines[data_start:data_end]:
                if line.startswith('='):
                    continue
                
                line = line.rstrip('\r\n')
                if not line:
                    continue
                
                # yEnc decode
                for char in line:
                    if char == '=':
                        continue
                    byte_val = (ord(char) - 42) % 256
                    decoded_data.append(byte_val)
            
            # Validate size if available
            if expected_size and len(decoded_data) != expected_size:
                logger.warning(f"⚠️ Size mismatch: expected {expected_size}, got {len(decoded_data)}")
            
            return bytes(decoded_data)
            
        except Exception as e:
            error_info = ErrorInfo(
                category=ErrorCategory.YENC_DECODING,
                severity=ErrorSeverity.HIGH,
                description=f"Manual yEnc decode failed: {str(e)}",
                retriable=False,
                action="Check yEnc format and data integrity"
            )
            raise NZBDownloadError(f"Manual yEnc decode failed: {str(e)}", error_info, e)

    async def download_segment_with_retry(self, segment: SegmentInfo, file_name: str) -> bytes:
        """Download a single segment with comprehensive retry logic"""
        context = {
            "segment_number": segment.number,
            "message_id": segment.message_id,
            "file_name": file_name,
            "size": segment.size
        }
        
        async def _download_segment():
            return await self._download_segment_internal(segment, context)
        
        try:
            self.stats['total_segments'] += 1
            result = await self.retry_handler.retry_async(_download_segment, context=context)
            self.stats['successful_segments'] += 1
            self.stats['bytes_downloaded'] += len(result)
            return result
            
        except NZBDownloadError as e:
            self.stats['failed_segments'] += 1
            self.stats['errors_by_category'][e.error_info.category.value] += 1
            log_error_with_context(e, context)
            raise
        except Exception as e:
            self.stats['failed_segments'] += 1
            error_info = categorize_error(e, context)
            nzb_error = NZBDownloadError(f"Segment download failed: {str(e)}", error_info, e)
            log_error_with_context(nzb_error, context)
            raise nzb_error

    async def _download_segment_internal(self, segment: SegmentInfo, context: Dict) -> bytes:
        """Internal segment download logic"""
        with self.connection_semaphore:
            connection = None
            try:
                connection = self._get_connection()
                
                # Download article
                response = connection.article(f"<{segment.message_id}>")
                if response[0] != '220':
                    error_info = categorize_error(
                        Exception(f"NNTP response: {response[0]}"), 
                        context
                    )
                    raise NZBDownloadError(f"Article fetch failed: {response[0]}", error_info)
                
                # Combine article lines
                article_data = b'\r\n'.join(response[1].lines) + b'\r\n'
                
                # Validate size if specified
                if segment.size > 0 and abs(len(article_data) - segment.size) > 100:
                    logger.warning(f"⚠️ Size mismatch for segment {segment.number}: "
                                 f"expected ~{segment.size}, got {len(article_data)}")
                
                # Decode yEnc
                decoded_data = self._decode_yenc_data(article_data)
                
                logger.debug(f"✅ Downloaded segment {segment.number}: {len(decoded_data)} bytes")
                return decoded_data
                
            finally:
                if connection:
                    self._return_connection(connection)

    async def download_file(self, file_info: FileInfo) -> str:
        """Download a complete file with parallel segment downloading"""
        logger.info(f"📥 Starting download: {file_info.name} ({len(file_info.segments)} segments)")
        
        # Create tasks for parallel download
        tasks = []
        for segment in file_info.segments:
            task = asyncio.create_task(
                self.download_segment_with_retry(segment, file_info.name)
            )
            tasks.append((segment.number, task))
        
        # Wait for all segments
        segment_data = {}
        failed_segments = []
        
        for segment_number, task in tasks:
            try:
                data = await task
                segment_data[segment_number] = data
            except Exception as e:
                logger.error(f"❌ Segment {segment_number} failed: {e}")
                failed_segments.append(segment_number)
        
        # Check if we have enough segments
        success_rate = len(segment_data) / len(file_info.segments)
        if success_rate < 0.8:  # Require at least 80% success
            error_info = ErrorInfo(
                category=ErrorCategory.NNTP_SERVER,
                severity=ErrorSeverity.HIGH,
                description=f"Too many failed segments: {len(failed_segments)}/{len(file_info.segments)}",
                retriable=False,
                action="Check server availability and article retention"
            )
            raise NZBDownloadError(
                f"File download failed: only {success_rate:.1%} segments successful", 
                error_info
            )
        
        # Combine segments in order
        combined_data = bytearray()
        for i in range(1, len(file_info.segments) + 1):
            if i in segment_data:
                combined_data.extend(segment_data[i])
            else:
                logger.warning(f"⚠️ Missing segment {i}, file may be incomplete")
        
        # Save to file
        safe_filename = self._sanitize_filename(file_info.name)
        output_path = os.path.join(self.download_dir, safe_filename)
        
        async with aiofiles.open(output_path, 'wb') as f:
            await f.write(combined_data)
        
        logger.info(f"✅ Downloaded: {file_info.name} ({len(combined_data)} bytes) -> {output_path}")
        return output_path

    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for safe filesystem storage"""
        # Remove/replace dangerous characters
        safe_chars = re.sub(r'[<>:"/\\|?*]', '_', filename)
        # Limit length
        if len(safe_chars) > 255:
            name, ext = os.path.splitext(safe_chars)
            safe_chars = name[:250-len(ext)] + ext
        return safe_chars

    async def download_nzb(self, nzb_path: str, download_id: Optional[str] = None) -> Dict[str, Any]:
        """Download complete NZB with comprehensive error handling and progress tracking"""
        start_time = time.time()
        
        try:
            logger.info(f"🚀 Starting NZB download: {nzb_path}")
            
            # Parse NZB
            files = await self.parse_nzb_with_validation(nzb_path)
            
            # Download files
            downloaded_files = []
            total_files = len(files)
            
            for i, file_info in enumerate(files):
                try:
                    logger.info(f"📁 Processing file {i+1}/{total_files}: {file_info.name}")
                    output_path = await self.download_file(file_info)
                    downloaded_files.append(output_path)
                    
                except NZBDownloadError as e:
                    logger.error(f"❌ File download failed: {file_info.name} - {e}")
                    if e.error_info.severity == ErrorSeverity.CRITICAL:
                        raise  # Stop on critical errors
                    continue  # Skip non-critical errors
                except Exception as e:
                    logger.error(f"❌ Unexpected error downloading {file_info.name}: {e}")
                    continue
            
            # Generate summary
            duration = time.time() - start_time
            success_rate = len(downloaded_files) / total_files if total_files > 0 else 0
            
            result = {
                "success": success_rate > 0.5,  # At least 50% success
                "downloaded_files": downloaded_files,
                "total_files": total_files,
                "success_rate": success_rate,
                "duration": duration,
                "stats": self.stats.copy(),
                "diagnostic_info": collect_diagnostic_info()
            }
            
            logger.info(f"🎉 NZB download completed: {len(downloaded_files)}/{total_files} files "
                       f"({success_rate:.1%} success) in {duration:.1f}s")
            
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            if isinstance(e, NZBDownloadError):
                log_error_with_context(e, {"nzb_path": nzb_path, "duration": duration})
            else:
                error_info = categorize_error(e, {"nzb_path": nzb_path, "duration": duration})
                nzb_error = NZBDownloadError(f"NZB download failed: {str(e)}", error_info, e)
                log_error_with_context(nzb_error)
            
            return {
                "success": False,
                "error": str(e),
                "duration": duration,
                "stats": self.stats.copy(),
                "diagnostic_info": collect_diagnostic_info()
            }

    def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive download statistics"""
        total_attempts = self.stats['total_segments']
        if total_attempts > 0:
            success_rate = self.stats['successful_segments'] / total_attempts
        else:
            success_rate = 0
        
        return {
            **self.stats,
            "success_rate": success_rate,
            "average_segment_size": (
                self.stats['bytes_downloaded'] / self.stats['successful_segments'] 
                if self.stats['successful_segments'] > 0 else 0
            ),
            "connection_pool_size": len(self.connection_pool)
        }

    async def test_connection(self) -> Dict[str, Any]:
        """Test NNTP connection and return diagnostic information"""
        try:
            connection = self._create_connection()
            
            # Test basic operations
            response = connection.capabilities()
            capabilities = response[1] if len(response) > 1 else []
            
            # Test group listing (just get a few)
            try:
                groups_response = connection.list()
                group_count = len(groups_response[1]) if len(groups_response) > 1 else 0
            except:
                group_count = 0
            
            connection.quit()
            
            return {
                "success": True,
                "server": f"{self.server_config.host}:{self.server_config.port}",
                "ssl_enabled": self.server_config.ssl_enabled,
                "capabilities": capabilities,
                "group_count": group_count,
                "diagnostic_info": collect_diagnostic_info()
            }
            
        except Exception as e:
            error_info = categorize_error(e, {"test": "connection"})
            return {
                "success": False,
                "error": str(e),
                "error_category": error_info.category.value,
                "error_severity": error_info.severity.value,
                "suggested_action": error_info.action,
                "diagnostic_info": collect_diagnostic_info()
            }

    def cleanup(self):
        """Clean up connections and resources"""
        logger.info("🧹 Cleaning up NZB service...")
        
        with self.pool_lock:
            for connection in self.connection_pool:
                try:
                    connection.quit()
                except:
                    pass
            self.connection_pool.clear()
        
        logger.info("✅ NZB service cleanup completed")

# Legacy wrapper for compatibility
class NZBService(EnhancedNZBService):
    """Legacy NZB service wrapper for backward compatibility"""
    
    def __init__(self, **kwargs):
        # Convert legacy parameters to ServerConfig
        server_config = ServerConfig(
            host=kwargs.get('host', 'localhost'),
            port=kwargs.get('port', 119),
            username=kwargs.get('username', ''),
            password=kwargs.get('password', ''),
            ssl_enabled=kwargs.get('ssl', False),
            connections=kwargs.get('connections', 8),
            timeout=kwargs.get('timeout', 30)
        )
        
        download_dir = kwargs.get('download_dir', '/tmp/nzb_downloads')
        super().__init__(server_config, download_dir)

