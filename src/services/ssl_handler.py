"""
Enhanced SSL connection handler for NNTP connections
Specifically designed to handle TLS/SSL EOF errors and connection pooling
"""
import ssl
import nntplib
import socket
import logging
import time
from typing import Optional, Dict, List
from threading import Lock
import queue
from contextlib import contextmanager

logger = logging.getLogger(__name__)

class SSLConnectionManager:
    """Manages SSL connections with health checks and automatic recovery"""
    
    def __init__(self, host: str, port: int, username: str = None, password: str = None, 
                 max_connections: int = 10, connection_timeout: int = 30):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.max_connections = max_connections
        self.connection_timeout = connection_timeout
        
        # Connection pool
        self.connections = queue.Queue(maxsize=max_connections)
        self.lock = Lock()
        
        # SSL context with robust configuration
        self.ssl_context = self._create_ssl_context()
        
        # Connection tracking
        self.active_connections = 0
        self.total_created = 0
        self.ssl_errors = 0
        self.last_ssl_context_refresh = time.time()
        
    def _create_ssl_context(self) -> ssl.SSLContext:
        """Create a robust SSL context for NNTP connections"""
        context = ssl.create_default_context()
        
        # Disable hostname verification for Usenet servers
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        
        # Configure protocol versions
        context.minimum_version = ssl.TLSVersion.TLSv1_2
        context.maximum_version = ssl.TLSVersion.TLSv1_3
        
        # Configure cipher suites for better compatibility
        context.set_ciphers('ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:DHE+CHACHA20:!aNULL:!MD5:!DSS')
        
        # Enable session reuse
        context.check_hostname = False
        
        return context
    
    def _refresh_ssl_context(self):
        """Refresh SSL context if too many errors occur"""
        current_time = time.time()
        if (self.ssl_errors > 5 and 
            current_time - self.last_ssl_context_refresh > 60):  # Refresh every minute if errors
            
            logger.info("🔄 Refreshing SSL context due to persistent errors")
            self.ssl_context = self._create_ssl_context()
            self.ssl_errors = 0
            self.last_ssl_context_refresh = current_time
    
    def _create_connection(self) -> nntplib.NNTP_SSL:
        """Create a new SSL NNTP connection"""
        try:
            self._refresh_ssl_context()
            
            # Create SSL connection with enhanced configuration
            conn = nntplib.NNTP_SSL(
                self.host,
                self.port,
                ssl_context=self.ssl_context,
                timeout=self.connection_timeout
            )
            
            # Authenticate if credentials provided
            if self.username and self.password:
                conn.login(self.username, self.password)
            
            with self.lock:
                self.total_created += 1
                self.active_connections += 1
            
            logger.debug(f"✅ Created new SSL connection to {self.host}:{self.port}")
            return conn
            
        except ssl.SSLError as e:
            self.ssl_errors += 1
            logger.error(f"🔒 SSL error creating connection: {e}")
            raise
        except Exception as e:
            logger.error(f"💥 Error creating connection: {e}")
            raise
    
    def _test_connection(self, conn: nntplib.NNTP_SSL) -> bool:
        """Test if a connection is still healthy"""
        try:
            # Simple NNTP command to test connection
            conn.date()
            return True
        except Exception:
            return False
    
    @contextmanager
    def get_connection(self):
        """Context manager for getting and returning connections"""
        conn = None
        try:
            # Try to get a connection from the pool
            try:
                conn = self.connections.get_nowait()
                # Test if connection is still healthy
                if not self._test_connection(conn):
                    conn.quit()
                    conn = None
            except queue.Empty:
                pass
            
            # Create new connection if needed
            if conn is None:
                conn = self._create_connection()
            
            yield conn
            
        except ssl.SSLError as e:
            self.ssl_errors += 1
            logger.error(f"🔒 SSL error during connection use: {e}")
            # Don't return faulty connection to pool
            if conn:
                try:
                    conn.quit()
                except:
                    pass
                conn = None
            raise
        except Exception as e:
            logger.error(f"💥 Error during connection use: {e}")
            # Don't return faulty connection to pool
            if conn:
                try:
                    conn.quit()
                except:
                    pass
                conn = None
            raise
        finally:
            # Return connection to pool if it's healthy
            if conn:
                try:
                    if self._test_connection(conn):
                        self.connections.put_nowait(conn)
                    else:
                        conn.quit()
                        with self.lock:
                            self.active_connections -= 1
                except queue.Full:
                    # Pool is full, close connection
                    try:
                        conn.quit()
                        with self.lock:
                            self.active_connections -= 1
                    except:
                        pass
                except Exception:
                    # Connection is bad, close it
                    try:
                        conn.quit()
                        with self.lock:
                            self.active_connections -= 1
                    except:
                        pass
    
    def close_all_connections(self):
        """Close all connections in the pool"""
        while not self.connections.empty():
            try:
                conn = self.connections.get_nowait()
                conn.quit()
            except:
                pass
        
        with self.lock:
            self.active_connections = 0
    
    def get_stats(self) -> Dict:
        """Get connection pool statistics"""
        with self.lock:
            return {
                'active_connections': self.active_connections,
                'total_created': self.total_created,
                'ssl_errors': self.ssl_errors,
                'pool_size': self.connections.qsize(),
                'max_connections': self.max_connections
            }

class RobustNNTPClient:
    """NNTP client wrapper with enhanced SSL error handling"""
    
    def __init__(self, host: str, port: int, use_ssl: bool = True, 
                 username: str = None, password: str = None,
                 max_connections: int = 10, max_retries: int = 3):
        self.host = host
        self.port = port
        self.use_ssl = use_ssl
        self.username = username
        self.password = password
        self.max_retries = max_retries
        
        if use_ssl:
            self.connection_manager = SSLConnectionManager(
                host, port, username, password, max_connections
            )
        else:
            # For non-SSL connections, use simple connection creation
            self.connection_manager = None
    
    def download_article(self, message_id: str) -> Optional[bytes]:
        """Download an article with retry logic for SSL errors"""
        for attempt in range(self.max_retries + 1):
            try:
                if self.use_ssl and self.connection_manager:
                    with self.connection_manager.get_connection() as conn:
                        resp = conn.article(f'<{message_id}>')
                        return b'\r\n'.join(
                            resp[1].lines if hasattr(resp[1], 'lines') 
                            else (x if isinstance(x, bytes) else str(x).encode('utf-8') for x in resp[1])
                        )
                else:
                    # Non-SSL connection
                    conn = nntplib.NNTP(self.host, self.port, timeout=30)
                    if self.username and self.password:
                        conn.login(self.username, self.password)
                    
                    try:
                        resp = conn.article(f'<{message_id}>')
                        return b'\r\n'.join(
                            resp[1].lines if hasattr(resp[1], 'lines') 
                            else (x if isinstance(x, bytes) else str(x).encode('utf-8') for x in resp[1])
                        )
                    finally:
                        conn.quit()
                        
            except ssl.SSLError as e:
                if "EOF" in str(e) or "closed" in str(e).lower():
                    logger.warning(f"🔒 SSL EOF error on attempt {attempt + 1}: {e}")
                    if attempt < self.max_retries:
                        time.sleep(2 ** attempt)  # Exponential backoff
                        continue
                else:
                    logger.error(f"🔒 SSL error: {e}")
                    break
            except Exception as e:
                logger.error(f"💥 Error downloading article {message_id}: {e}")
                if attempt < self.max_retries:
                    time.sleep(1)
                    continue
                break
        
        return None
    
    def get_stats(self) -> Dict:
        """Get client statistics"""
        if self.connection_manager:
            return self.connection_manager.get_stats()
        return {}
    
    def close(self):
        """Close all connections"""
        if self.connection_manager:
            self.connection_manager.close_all_connections()
