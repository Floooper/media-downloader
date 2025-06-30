import logging
from typing import Dict, Any, Optional
from .nzb_service import NZBService

logger = logging.getLogger(__name__)

class ServicesManager:
    def __init__(self):
        self._nzb_service: Optional[NZBService] = None
        
    def get_nzb_service(self, config: Dict[str, Any] = None) -> NZBService:
        """Get or create NZB service instance"""
        if not self._nzb_service and config:
            self._nzb_service = NZBService(config)
        return self._nzb_service
