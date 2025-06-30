import xml.etree.ElementTree as ET
from io import StringIO
import logging
import os
import nntplib
import asyncio
from dataclasses import dataclass
from typing import Optional, Dict, Any
import importlib

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Try to import yenc decoder
try:
    yenc_decoder = importlib.import_module('src.services.yenc_decoder')
    YENC_AVAILABLE = True
    logger.info("✅ yEnc decoder available")
except ImportError:
    YENC_AVAILABLE = False
    logger.warning("⚠️ yEnc decoder not available")

@dataclass
class NZBConfig:
    host: str
    port: int = 119
    ssl: bool = False
    username: Optional[str] = None
    password: Optional[str] = None
    max_connections: int = 10
    retention_days: int = 1500
    download_rate_limit: Optional[int] = None
    max_retries: int = 3

class NZBService:
    def __init__(self, config: Dict[str, Any]):
        """Initialize NZB service with configuration"""
        
        # Force SSL for port 563
        ssl_enabled = config.get("ssl", False)
        if config.get("port", 119) == 563:
            ssl_enabled = True
            logger.debug("Port 563 specified, forcing SSL")
            
        self.config = NZBConfig(
            host=config.get("host", "localhost"),
            port=config.get("port", 119),
            ssl=ssl_enabled,
            username=config.get("username"),
            password=config.get("password"),
            max_connections=config.get("max_connections", 10),
            retention_days=config.get("retention_days", 1500),
            download_rate_limit=config.get("download_rate_limit"),
            max_retries=config.get("max_retries", 3)
        )
        
        # Debug log the config (masking password)
        logger.debug(f"NZB Service initialized with config:")
        logger.debug(f"Host: {self.config.host}")
        logger.debug(f"Port: {self.config.port}")
        logger.debug(f"SSL: {self.config.ssl}")
        logger.debug(f"Username: {self.config.username}")
        logger.debug(f"Max Connections: {self.config.max_connections}")
        
        self.executor = None
        self.retry_handler = RetryHandler(max_retries=self.config.max_retries)
        self.active_downloads = {}
        self.stats = {
            "total_segments": 0,
            "successful_segments": 0,
            "failed_segments": 0,
            "yenc_decode_failures": 0,
            "server_errors": 0
        }

    def _count_files_and_segments(self, nzb_content: str) -> tuple[int, int]:
        """Count the number of files and segments in an NZB file"""
        try:
            tree = ET.parse(StringIO(nzb_content))
            root = tree.getroot()
            
            # Count files
            files = root.findall(".//{http://www.newzbin.com/DTD/2003/nzb}file")
            file_count = len(files)
            
            # Count segments across all files
            segments = root.findall(".//{http://www.newzbin.com/DTD/2003/nzb}segment")
            segment_count = len(segments)
            
            return file_count, segment_count
        except Exception as e:
            logger.error(f"Error counting files and segments: {e}")
            return 0, 0

    async def add_nzb_download(self, nzb_content: str, filename: str, download_path: str, download_id: int, db = None) -> bool:
        """Add a new NZB download job"""
        try:
            logger.debug(f"Parsing NZB content for {filename}", extra={"download_id": download_id})
            tree = ET.parse(StringIO(nzb_content))
            root = tree.getroot()
            
            # Count files and segments
            file_count, segment_count = self._count_files_and_segments(nzb_content)
            logger.info(f"Found {file_count} files with {segment_count} total segments")
            
            # Extract segments
            segments = []
            for file_elem in root.findall(".//{http://www.newzbin.com/DTD/2003/nzb}file"):
                for seg in file_elem.findall(".//{http://www.newzbin.com/DTD/2003/nzb}segment"):
                    segments.append({
                        "message_id": seg.text.strip(),
                        "number": int(seg.get("number", 1)),
                        "bytes": int(seg.get("bytes", 0))
                    })
            
            logger.info(f"Found {len(segments)} segments to download", extra={"download_id": download_id})
            if not segments:
                logger.error("No segments found in NZB file", extra={"download_id": download_id})
                await self.set_download_failed(download_id, db)
                return False
            
            # Sort segments by number
            segments.sort(key=lambda x: x["number"])
            
            # Download segments
            results = []
            for i, segment in enumerate(segments, 1):
                logger.debug(f"Downloading segment {i}/{len(segments)}", extra={"download_id": download_id})
                result = await self.download_segment(
                    segment["message_id"],
                    segment["number"],
                    filename
                )
                if result:
                    results.append(result)
                    logger.debug(f"Segment {i} downloaded successfully ({len(result):,} bytes)", extra={"download_id": download_id})
                    # Update progress
                    progress = (len(results) / len(segments)) * 100
                    await self.update_download_progress(download_id, progress, db)
                else:
                    logger.warning(f"Segment {i} download failed", extra={"download_id": download_id})
            
            logger.info(f"Download complete: {len(results)}/{len(segments)} segments successful", extra={"download_id": download_id})
            
            # Combine and save segments
            if results:
                combined = b"".join(results)
                logger.info(f"Combined data size: {len(combined):,} bytes", extra={"download_id": download_id})
                
                # Create directory if needed
                os.makedirs(download_path, exist_ok=True)
                
                # Save to file
                full_path = os.path.join(download_path, filename)
                self._save_to_file(combined, download_path, filename)
                
                if os.path.exists(full_path):
                    logger.info(f"Successfully wrote file to {full_path}", extra={"download_id": download_id})
                    await self.set_download_completed(download_id, db)
                    return True
                else:
                    logger.error(f"Failed to verify file at {full_path}", extra={"download_id": download_id})
                    await self.set_download_failed(download_id, db)
                    return False
            
            logger.error("No segments downloaded successfully", extra={"download_id": download_id})
            await self.set_download_failed(download_id, db)
            return False
            
        except Exception as e:
            logger.error(f"❌ Failed to process NZB download: {e}", extra={"download_id": download_id})
            await self.set_download_failed(download_id, db)
            raise

    async def update_download_progress(self, download_id: int, progress: float, db = None):
        """Update download progress in database"""
        if db:
            from ..database import Download
            download = db.query(Download).filter(Download.id == download_id).first()
            if download:
                download.progress = progress
                db.commit()

    async def set_download_completed(self, download_id: int, db = None):
        """Mark download as completed in database"""
        if db:
            from ..database import Download, DownloadStatus
            from datetime import datetime
            download = db.query(Download).filter(Download.id == download_id).first()
            if download:
                download.status = DownloadStatus.COMPLETED
                download.completed_at = datetime.utcnow()
                db.commit()

    async def set_download_failed(self, download_id: int, db = None):
        """Mark download as failed in database"""
        if db:
            from ..database import Download, DownloadStatus
            download = db.query(Download).filter(Download.id == download_id).first()
            if download:
                download.status = DownloadStatus.FAILED
                db.commit()

    def _save_to_file(self, data: bytes, download_path: str, filename: str):
        """Save combined data to a file"""
        try:
            # Ensure absolute path
            download_path = os.path.abspath(download_path)
            logger.info(f"Saving file to directory: {download_path}")
            
            # Create directory with full permissions
            os.makedirs(download_path, mode=0o755, exist_ok=True)
            
            # Construct full file path
            file_path = os.path.join(download_path, filename)
            logger.info(f"Writing to file: {file_path}")
            
            # Write data with explicit permissions
            with open(file_path, "wb") as f:
                bytes_written = f.write(data)
                f.flush()
                os.fsync(f.fileno())
            
            # Verify file exists and has content
            if os.path.exists(file_path):
                file_size = os.path.getsize(file_path)
                logger.info(f"✅ File saved successfully: {file_path} ({file_size:,} bytes)")
            else:
                logger.error(f"❌ File not found after writing: {file_path}")
                raise IOError(f"Failed to verify file at {file_path}")
                
        except Exception as e:
            logger.error(f"❌ Failed to save file {filename}: {e}")
            raise

    def _get_connection(self) -> nntplib.NNTP:
        """Get a new NNTP connection"""
        max_attempts = 3
        attempt = 1
        last_error = None
        
        while attempt <= max_attempts:
            try:
                logger.debug(f"Attempting {'SSL' if self.config.ssl else 'non-SSL'} connection to {self.config.host}:{self.config.port} (attempt {attempt})")
                if self.config.ssl:
                    return nntplib.NNTP_SSL(
                        host=self.config.host,
                        port=self.config.port,
                        user=self.config.username,
                        password=self.config.password,
                        timeout=30
                    )
                else:
                    return nntplib.NNTP(
                        host=self.config.host,
                        port=self.config.port,
                        user=self.config.username,
                        password=self.config.password,
                        timeout=30
                    )
            except Exception as e:
                last_error = e
                logger.warning(f"Connection attempt {attempt} failed: {e}")
                attempt += 1
                
        logger.error(f"All connection attempts failed. Last error: {last_error}")
        raise last_error

    def _update_stats(self, key: str, value: int = 1):
        """Update download statistics"""
        if key in self.stats:
            self.stats[key] += value

    async def download_segment(self, message_id: str, segment_num: int, filename: str) -> Optional[bytes]:
        """Download a single NZB segment"""
        if not message_id:
            logger.error(f"❌ No message ID for segment {segment_num}")
            return None
        
        async def download_segment_inner():
            return await asyncio.get_event_loop().run_in_executor(
                self.executor,
                self._download_segment_sync,
                message_id,
                segment_num,
                filename
            )
        
        try:
            return await self.retry_handler.retry_async(
                download_segment_inner
            )
        except Exception as e:
            error_info = categorize_error(e)
            logger.error(f"❌ Failed to download segment {segment_num} after retries: {e}")
            return None

    def _download_segment_sync(self, message_id: str, segment_num: int, filename: str) -> Optional[bytes]:
        """Synchronous segment download for thread executor"""
        conn = None
        try:
            conn = self._get_connection()
            
            # Download article
            logger.debug(f"Downloading article for segment {segment_num}: {message_id}")
            resp = conn.article(f"<{message_id}>")
            
            # Convert all items to bytes before joining
            lines = []
            for x in (resp[1].lines if hasattr(resp[1], "lines") else resp[1]):
                if isinstance(x, bytes):
                    lines.append(x)
                elif isinstance(x, (str, int, float)):
                    lines.append(str(x).encode("utf-8"))
                else:
                    logger.warning(f"Unexpected type in article data: {type(x)}")
                    lines.append(str(x).encode("utf-8"))
            
            article_data = b"\r\n".join(lines)
            
            # Log article data length only
            logger.debug(f"Article data for segment {segment_num} ({len(article_data):,} bytes)")
            
            # Decode yEnc
            decoded_data = self._decode_yenc(article_data, message_id)
            
            if decoded_data:
                logger.debug(f"✅ Downloaded segment {segment_num} ({len(decoded_data):,} bytes)")
                return decoded_data
            else:
                logger.error(f"❌ Failed to decode segment {segment_num}")
                self._update_stats("yenc_decode_failures")
                return None
                
        except nntplib.NNTPError as e:
            error_code = str(e).split()[0] if str(e) else "unknown"
            
            if error_code.startswith("43"):  # Article not found
                logger.warning(f"📰 Article not found for segment {segment_num}: {message_id}")
            else:
                logger.error(f"💥 NNTP error downloading segment {segment_num}: {e}")
                self._update_stats("server_errors")
            
            raise NZBDownloadError("NNTP_ERROR", categorize_error(e), e)
            
        except Exception as e:
            logger.error(f"💥 Error downloading segment {segment_num}: {e}")
            self._update_stats("failed_segments")
            raise NZBDownloadError("DOWNLOAD_ERROR", categorize_error(e), e)
            
        finally:
            if conn:
                try:
                    conn.quit()
                except:
                    pass

    def _decode_yenc(self, data: bytes, message_id: str = "") -> Optional[bytes]:
        """Decode yEnc data"""
        if not data:
            return None
        
        try:
            if not YENC_AVAILABLE:
                logger.error("yEnc decoder not available")
                return None
                
            return yenc_decoder.decode_yenc(data)
                
        except Exception as e:
            logger.error(f"💥 yEnc decode failed for {message_id}: {e}")
            return None

class RetryHandler:
    def __init__(self, max_retries: int = 3, initial_delay: float = 1.0):
        self.max_retries = max_retries
        self.initial_delay = initial_delay
    
    async def retry_async(self, func, *args, **kwargs):
        last_error = None
        delay = self.initial_delay
        
        for attempt in range(self.max_retries):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(delay)
                    delay *= 2
        
        if last_error:
            raise last_error

class NZBDownloadError(Exception):
    def __init__(self, error_type: str, error_category: str, original_error: Exception = None):
        self.error_type = error_type
        self.error_category = error_category
        self.original_error = original_error
        super().__init__(f"{error_type}: {error_category}")

def categorize_error(e: Exception) -> str:
    """Categorize common NZB download errors"""
    error_str = str(e).lower()
    
    if isinstance(e, nntplib.NNTPError):
        error_code = str(e).split()[0] if str(e) else "unknown"
        if error_code.startswith("43"):
            return "ARTICLE_NOT_FOUND"
        elif error_code.startswith("48"):
            return "AUTH_REQUIRED"
        elif error_code.startswith("42"):
            return "CONNECTION_CLOSED"
        return "NNTP_ERROR"
    
    if "broken pipe" in error_str or "connection reset" in error_str:
        return "CONNECTION_ERROR"
    elif "timeout" in error_str:
        return "TIMEOUT"
    elif "memory" in error_str:
        return "MEMORY_ERROR"
    elif "permission" in error_str:
        return "PERMISSION_ERROR"
    elif "disk" in error_str or "space" in error_str:
        return "DISK_ERROR"
    
    return "UNKNOWN_ERROR"
