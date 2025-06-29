"""NZB service for downloading from Usenet"""
from typing import Optional, Dict, Any
import nntplib
import logging
import asyncio
from dataclasses import dataclass
from importlib import import_module as import_from_module

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

YENC_DECODER_AVAILABLE = False
try:
    import sabyenc3
    YENC_DECODER_AVAILABLE = True
except ImportError:
    try:
        import yenc
        YENC_DECODER_AVAILABLE = True
    except ImportError:
        pass

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
        self.config = NZBConfig(
            host=config.get('usenet_server', 'localhost'),
            port=config.get('port', 119),
            ssl=config.get('use_ssl', False),
            username=config.get('username'),
            password=config.get('password'),
            max_connections=config.get('max_connections', 10),
            retention_days=config.get('retention_days', 1500),
            download_rate_limit=config.get('download_rate_limit'),
            max_retries=config.get('max_retries', 3)
        )
        self.executor = None
        self.retry_handler = RetryHandler(max_retries=self.config.max_retries)
        self.active_downloads = {}
        self.stats = {
            'total_segments': 0,
            'successful_segments': 0,
            'failed_segments': 0,
            'yenc_decode_failures': 0,
            'server_errors': 0
        }
    
    async def add_nzb_download(self, nzb_content: str, filename: str, download_path: str):
        """Add a new NZB download job"""
        try:
            # Parse the NZB content
            import xml.etree.ElementTree as ET
            from io import StringIO
            
            logger.debug(f"Parsing NZB content for {filename}")
            tree = ET.parse(StringIO(nzb_content))
            root = tree.getroot()
            
            # Extract segments
            segments = []
            for file_elem in root.findall('.//{http://www.newzbin.com/DTD/2003/nzb}file'):
                for seg in file_elem.findall('.//{http://www.newzbin.com/DTD/2003/nzb}segment'):
                    segments.append({
                        'message_id': seg.text.strip(),
                        'number': int(seg.get('number', 1)),
                        'bytes': int(seg.get('bytes', 0))
                    })
            
            logger.debug(f"Found {len(segments)} segments in NZB file")
            
            # Sort segments by number
            segments.sort(key=lambda x: x['number'])
            
            # Download segments
            results = []
            for segment in segments:
                result = await self.download_segment(
                    segment['message_id'],
                    segment['number'],
                    filename
                )
                if result:
                    results.append(result)
            
            logger.debug(f"Successfully downloaded {len(results)} of {len(segments)} segments")
            
            # Combine segment data
            if results:
                combined = b''.join(results)
                logger.debug(f"Combined data size: {len(combined):,} bytes")
                return combined
            return None
            
        except Exception as e:
            logger.error(f"❌ Failed to process NZB file: {e}")
            raise

    def _get_connection(self) -> nntplib.NNTP:
        """Get a new NNTP connection"""
        try:
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
            logger.error(f"Error connecting to NNTP server: {e}")
            raise

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
            resp = conn.article(f'<{message_id}>')
            
            # Convert all items to bytes before joining
            lines = []
            for x in (resp[1].lines if hasattr(resp[1], 'lines') else resp[1]):
                if isinstance(x, bytes):
                    lines.append(x)
                elif isinstance(x, (str, int, float)):
                    lines.append(str(x).encode('utf-8'))
                else:
                    logger.warning(f"Unexpected type in article data: {type(x)}")
                    lines.append(str(x).encode('utf-8'))
            
            article_data = b'\r\n'.join(lines)
            
            # Log article data for debugging
            logger.debug(f"Article data for segment {segment_num} ({len(article_data):,} bytes):\n{article_data[:1000].decode('utf-8', errors='ignore')}")
            
            # Decode yEnc
            decoded_data = self._decode_yenc_with_fallback(article_data, message_id)
            
            if decoded_data:
                logger.debug(f"✅ Downloaded segment {segment_num} ({len(decoded_data):,} bytes)")
                return decoded_data
            else:
                logger.error(f"❌ Failed to decode segment {segment_num}")
                self._update_stats('yenc_decode_failures')
                return None
                
        except nntplib.NNTPError as e:
            error_code = str(e).split()[0] if str(e) else "unknown"
            
            if error_code.startswith('43'):  # Article not found
                logger.warning(f"📰 Article not found for segment {segment_num}: {message_id}")
            else:
                logger.error(f"💥 NNTP error downloading segment {segment_num}: {e}")
                self._update_stats('server_errors')
            
            raise NZBDownloadError("NNTP_ERROR", categorize_error(e), e)
            
        except Exception as e:
            logger.error(f"💥 Error downloading segment {segment_num}: {e}")
            self._update_stats('failed_segments')
            raise NZBDownloadError("DOWNLOAD_ERROR", categorize_error(e), e)
            
        finally:
            if conn:
                try:
                    conn.quit()
                except:
                    pass

    def _decode_yenc_with_fallback(self, data: bytes, message_id: str = "") -> Optional[bytes]:
        """Decode yEnc data with multiple fallback methods"""
        if not data:
            return None
        
        # Try fast decoder first
        result = self._decode_yenc_fast(data, message_id)
        if result is not None:
            return result

        logger.debug("Fast yEnc decoder failed, trying manual decode")
        
        # Fallback to manual decoding
        try:
            return import_from_module('src.services.yenc_decoder', 'decode_yenc').decode_yenc(data)
        except Exception as e:
            logger.error(f"💥 Manual yEnc decode failed for {message_id}: {e}")
            return None
    
    def _decode_yenc_fast(self, data: bytes, message_id: str) -> Optional[bytes]:
        """Fast decoding of yEnc using available library"""
        if YENC_DECODER_AVAILABLE:
            try:
                if 'sabyenc3' in globals():
                    import sabyenc3
                    result = sabyenc3.decode_string(data)
                    if isinstance(result, tuple) and len(result) >= 1:
                        return result[0]
                    return result
                elif 'yenc' in globals():
                    import yenc
                    return yenc.decode(data)[0]
            except Exception as e:
                logger.debug(f"🔧 Fast yEnc decoder failed for {message_id}: {e}")
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
        if error_code.startswith('43'):
            return "ARTICLE_NOT_FOUND"
        elif error_code.startswith('48'):
            return "AUTH_REQUIRED"
        elif error_code.startswith('42'):
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
