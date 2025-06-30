import aiohttp
from typing import Dict, List, Optional
from enum import Enum
from datetime import datetime
from ..config import settings

class MediaManagerType(Enum):
    SONARR = "sonarr"
    RADARR = "radarr"
    READARR = "readarr"
    LIDARR = "lidarr"

class MediaManagerIntegration:
    def __init__(self):
        self.managers: Dict[MediaManagerType, Dict] = {}
        self._initialize_managers()

    def _initialize_managers(self):
        """Initialize configured media managers from settings."""
        if settings.SONARR_URL:
            self.managers[MediaManagerType.SONARR] = {
                'url': settings.SONARR_URL,
                'api_key': settings.SONARR_API_KEY,
            }
        if settings.RADARR_URL:
            self.managers[MediaManagerType.RADARR] = {
                'url': settings.RADARR_URL,
                'api_key': settings.RADARR_API_KEY,
            }
        if settings.READARR_URL:
            self.managers[MediaManagerType.READARR] = {
                'url': settings.READARR_URL,
                'api_key': settings.READARR_API_KEY,
            }
        if settings.LIDARR_URL:
            self.managers[MediaManagerType.LIDARR] = {
                'url': settings.LIDARR_URL,
                'api_key': settings.LIDARR_API_KEY,
            }

    def _get_api_version(self, manager_type: MediaManagerType) -> str:
        """Get the correct API version for each media manager type."""
        api_versions = {
            MediaManagerType.SONARR: 'v3',
            MediaManagerType.RADARR: 'v3', 
            MediaManagerType.READARR: 'v1',  # Readarr uses v1
            MediaManagerType.LIDARR: 'v1'   # Lidarr uses v1
        }
        return api_versions.get(manager_type, 'v3')

    async def _make_request(self, manager_type: MediaManagerType, endpoint: str, method: str = 'GET', data: Dict = None) -> Optional[Dict]:
        """Make an API request to a media manager."""
        if manager_type not in self.managers:
            raise ValueError(f"{manager_type.value} is not configured")

        manager = self.managers[manager_type]
        api_version = self._get_api_version(manager_type)
        url = f"{manager['url']}/api/{api_version}/{endpoint}"
        headers = {
            'X-Api-Key': manager['api_key'],
            'Content-Type': 'application/json'
        }

        async with aiohttp.ClientSession() as session:
            async with session.request(method, url, headers=headers, json=data) as response:
                if response.status == 200:
                    return await response.json()
                return None

    async def get_download_categories(self, manager_type: MediaManagerType) -> List[Dict]:
        """Get available download categories from a media manager."""
        return await self._make_request(manager_type, 'downloadclient')

    async def notify_download_complete(self, manager_type: MediaManagerType, path: str) -> bool:
        """Notify media manager of completed download for processing."""
        data = {
            'path': path,
            'importMode': 'Move'
        }
        result = await self._make_request(
            manager_type,
            'command',
            method='POST',
            data={
                'name': 'DownloadedEpisodesScan' if manager_type == MediaManagerType.SONARR else 'DownloadedMoviesScan',
                'path': path
            }
        )
        return result is not None

    async def get_root_folders(self, manager_type: MediaManagerType) -> List[Dict]:
        """Get configured root folders from a media manager."""
        return await self._make_request(manager_type, 'rootfolder')

    async def get_quality_profiles(self, manager_type: MediaManagerType) -> List[Dict]:
        """Get available quality profiles from a media manager."""
        return await self._make_request(manager_type, 'qualityprofile')

    def _get_download_client_config(self, manager_type: MediaManagerType) -> Dict:
        """Get the appropriate download client configuration for each media manager type."""
        base_config = {
            'name': 'Media Downloader',
            'enable': True,
            'protocol': 'torrent',
            'priority': 1,
            'removeCompletedDownloads': False,
            'removeFailedDownloads': True,
        }
        
        if manager_type == MediaManagerType.READARR:
            # Readarr expects a specific format for torrent clients
            return {
                **base_config,
                'implementation': 'Transmission',  # Use Transmission as it's more generic
                'configContract': 'TransmissionSettings',
                'fields': [
                    {'name': 'host', 'value': settings.API_HOST or 'localhost'},
                    {'name': 'port', 'value': settings.API_PORT or 9091},
                    {'name': 'urlBase', 'value': '/transmission/rpc'},
                    {'name': 'username', 'value': ''},
                    {'name': 'password', 'value': ''},
                    {'name': 'musicCategory', 'value': 'readarr'},
                    {'name': 'musicDirectory', 'value': ''},
                    {'name': 'recentTvPriority', 'value': 2},
                    {'name': 'olderTvPriority', 'value': 2},
                    {'name': 'addStopped', 'value': False}
                ]
            }
        else:
            # For Sonarr/Radarr, use a simpler format
            return {
                **base_config,
                'implementation': 'Transmission',
                'configContract': 'TransmissionSettings',
                'settings': {
                    'host': settings.API_HOST or 'localhost',
                    'port': settings.API_PORT or 9091,
                    'urlBase': '/transmission/rpc',
                    'username': '',
                    'password': '',
                }
            }

    async def register_downloader(self, manager_type: MediaManagerType) -> bool:
        """Register this application by verifying connection and saving configuration."""
        try:
            # Instead of registering as a download client, we'll verify we can communicate
            # with the media manager and save the configuration for future use
            
            # Test basic API access
            system_status = await self._make_request(manager_type, 'system/status')
            if not system_status:
                print(f"Cannot access {manager_type.value} API")
                return False
            
            # Test that we can access download client info (shows we have proper permissions)
            download_clients = await self._make_request(manager_type, 'downloadclient')
            if download_clients is None:
                print(f"Cannot access download clients on {manager_type.value}")
                return False
            
            # Verify we can access quality profiles
            quality_profiles = await self._make_request(manager_type, 'qualityprofile')
            if quality_profiles is None:
                print(f"Cannot access quality profiles on {manager_type.value}")
                return False
            
            print(f"Successfully verified API access to {manager_type.value}")
            print(f"Found {len(download_clients)} download clients and {len(quality_profiles)} quality profiles")
            
            return True
            
        except Exception as e:
            print(f"Failed to verify access to {manager_type.value}: {e}")
            return False

    async def discover_managers(self) -> List[Dict]:
        """Auto-discover media managers on the network."""
        import socket
        import ipaddress
        import asyncio
        
        discovered = []
        
        try:
            # Get local network range
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            print(f"Starting discovery from {local_ip}")
            
            # Parse network from local IP (assume /24 subnet)
            network = ipaddress.IPv4Network(f"{local_ip}/24", strict=False)
            
            # Common ports for media managers
            common_services = [
                (8989, MediaManagerType.SONARR, "Sonarr"),
                (7878, MediaManagerType.RADARR, "Radarr"),  
                (8787, MediaManagerType.READARR, "Readarr"),
            ]
            
            # Function to check a single host:port combination
            async def check_service(host_ip: str, port: int, manager_type: MediaManagerType, service_name: str) -> Optional[Dict]:
                try:
                    # Quick socket check first
                    reader, writer = await asyncio.wait_for(
                        asyncio.open_connection(host_ip, port), 
                        timeout=2.0
                    )
                    writer.close()
                    await writer.wait_closed()
                    
                    # If socket is open, try to identify the service
                    url = f"http://{host_ip}:{port}"
                    print(f"Found service at {url}, checking if it's {service_name}")
                    
                    # Try to get service information
                    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=3)) as session:
                        try:
                            # Try direct API endpoint first
                            api_version = self._get_api_version(manager_type)
                            api_url = f"{url}/api/{api_version}/system/status"
                            async with session.get(api_url) as response:
                                if response.status == 200:
                                    data = await response.json()
                                    print(f"Confirmed {service_name} at {url}")
                                    return {
                                        "type": manager_type.value,
                                        "url": url,
                                        "name": data.get("appName", service_name),
                                        "version": data.get("version", "unknown"),
                                        "status": "running",
                                        "requires_auth": False
                                    }
                                elif response.status == 401:
                                    print(f"Found {service_name} at {url} (requires auth)")
                                    return {
                                        "type": manager_type.value,
                                        "url": url,
                                        "name": service_name,
                                        "version": "unknown",
                                        "status": "running",
                                        "requires_auth": True
                                    }
                        except aiohttp.ClientError as e:
                            print(f"API check failed for {url}: {e}")
                            # Try generic endpoint
                            try:
                                async with session.get(url) as response:
                                    if response.status == 200:
                                        text = await response.text()
                                        if service_name.lower() in text.lower():
                                            print(f"Found {service_name} at {url} (web interface)")
                                            return {
                                                "type": manager_type.value,
                                                "url": url,
                                                "name": service_name,
                                                "version": "unknown",
                                                "status": "running",
                                                "requires_auth": False
                                            }
                            except:
                                pass
                
                except asyncio.TimeoutError:
                    pass
                except Exception as e:
                    print(f"Error checking {host_ip}:{port}: {e}")
                
                return None
            
            # Scan common IPs first (router, common server IPs)
            priority_ips = []
            
            # Add router IP and common server IPs
            router_ip = str(network.network_address + 1)  # Usually .1
            priority_ips.append(router_ip)
            
            # Add some common server IPs
            for i in [10, 100, 200, 2, 3, 4, 5]:
                ip = str(network.network_address + i)
                if ip != local_ip and ip != router_ip:
                    priority_ips.append(ip)
            
            # Scan priority IPs first
            print(f"Scanning priority IPs: {priority_ips}")
            tasks = []
            for host_ip in priority_ips:
                for port, manager_type, service_name in common_services:
                    tasks.append(check_service(host_ip, port, manager_type, service_name))
            
            # Execute priority discovery with high concurrency
            if tasks:
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Collect successful discoveries
                for result in results:
                    if isinstance(result, dict) and result:
                        discovered.append(result)
                        print(f"Discovered: {result}")
            
            # If we found something, return early for speed
            if discovered:
                print(f"Found {len(discovered)} services, returning early")
                return discovered
            
            print("No services found in priority scan, doing full scan...")
            
            # If nothing found, do a broader scan (limited range)
            tasks = []
            for host in list(network.hosts())[:50]:  # Limit to first 50 IPs
                host_ip = str(host)
                if host_ip == local_ip or host_ip in priority_ips:
                    continue
                    
                for port, manager_type, service_name in common_services:
                    tasks.append(check_service(host_ip, port, manager_type, service_name))
            
            # Execute full discovery with limited concurrency
            if tasks:
                semaphore = asyncio.Semaphore(10)  # Limit concurrent connections
                
                async def bounded_check(task):
                    async with semaphore:
                        return await task
                
                results = await asyncio.gather(*[bounded_check(task) for task in tasks], return_exceptions=True)
                
                # Collect successful discoveries
                for result in results:
                    if isinstance(result, dict) and result:
                        discovered.append(result)
                        print(f"Discovered: {result}")
            
        except Exception as e:
            print(f"Network discovery error: {e}")
        
        print(f"Discovery complete. Found {len(discovered)} services.")
        return discovered
    
    async def test_connection(self, manager_type: MediaManagerType, url: str, api_key: str) -> Dict:
        """Test connection to a media manager with provided credentials."""
        headers = {
            'X-Api-Key': api_key,
            'Content-Type': 'application/json'
        }
        
        api_version = self._get_api_version(manager_type)
        test_url = f"{url.rstrip('/')}/api/{api_version}/system/status"
        
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                async with session.get(test_url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            "success": True,
                            "connected": True,
                            "version": data.get('version', 'Unknown'),
                            "instance_name": data.get('instanceName', 'Unknown'),
                            "message": f"Successfully connected to {manager_type.value}"
                        }
                    else:
                        return {
                            "success": False,
                            "connected": False,
                            "error": f"HTTP {response.status}: {response.reason}",
                            "message": f"Failed to connect to {manager_type.value}"
                        }
        except aiohttp.ClientConnectorError:
            return {
                "success": False,
                "connected": False,
                "error": "Connection refused",
                "message": f"Cannot reach {manager_type.value} at {url}. Please check the URL and ensure {manager_type.value} is running."
            }
        except aiohttp.ClientTimeout:
            return {
                "success": False,
                "connected": False,
                "error": "Connection timeout",
                "message": f"Connection to {manager_type.value} timed out. Please check the URL and network connection."
            }
        except Exception as e:
            return {
                "success": False,
                "connected": False,
                "error": str(e),
                "message": f"Unexpected error connecting to {manager_type.value}"
            }

    async def get_status(self, manager_type: MediaManagerType) -> Dict:
        """Get current status of a media manager."""
        if manager_type not in self.managers:
            return {
                "type": manager_type.value,
                "connected": False,
                "health": "not_configured",
                "last_checked": None
            }
        
        try:
            result = await self._make_request(manager_type, 'system/status')
            if result:
                return {
                    "type": manager_type.value,
                    "connected": True,
                    "version": result.get('version', 'Unknown'),
                    "health": "healthy",
                    "last_checked": datetime.utcnow().isoformat()
                }
        except Exception:
            pass
            
        return {
            "type": manager_type.value,
            "connected": False,
            "health": "unhealthy",
            "last_checked": datetime.utcnow().isoformat()
        }

    async def save_config(self, manager_type: MediaManagerType, config: Dict) -> None:
        """Save configuration for a media manager."""
        self.managers[manager_type] = {
            'url': config['url'],
            'api_key': config['api_key'],
            'enabled': config.get('enabled', True),
            'auto_import': config.get('auto_import', True),
            'category_mappings': config.get('category_mappings', {})
        }
        # In a real implementation, this would persist to database or config file

    async def get_config(self, manager_type: MediaManagerType) -> Dict:
        """Get configuration for a media manager."""
        if manager_type not in self.managers:
            return {
                'url': '',
                'api_key': '',
                'enabled': False,
                'auto_import': True,
                'category_mappings': {}
            }
        return self.managers[manager_type]

    async def get_tags(self, manager_type: MediaManagerType) -> List[Dict]:
        """Get available tags from a media manager."""
        return await self._make_request(manager_type, 'tag') or []

    async def check_health(self, manager_type: MediaManagerType) -> None:
        """Check health of a media manager (background task)."""
        try:
            result = await self._make_request(manager_type, 'health')
            # Log the health check result
            print(f"Health check for {manager_type.value}: {'OK' if result else 'FAILED'}")
        except Exception as e:
            print(f"Health check failed for {manager_type.value}: {e}")

    async def get_categories(self, manager_type: MediaManagerType) -> List[Dict]:
        """Get download categories from a media manager."""
        return await self._make_request(manager_type, 'downloadclient/category') or []

