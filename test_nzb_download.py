#!/usr/bin/env python3

import sys
import os
import asyncio
import logging
from src.services.nzb_service import NZBService

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_download():
    # Test configuration
    config = {
        'host': 'news.usenetserver.com',
        'port': 563,
        'ssl': True,
        'username': 'test_user',
        'password': 'test_pass'
    }
    
    # Initialize service
    service = NZBService(config)
    
    # Test message ID and segment
    message_id = "test1234@example.com"
    segment_num = 1
    filename = "test.nzb"
    
    try:
        # Attempt download
        result = await service.download_segment(message_id, segment_num, filename)
        if result:
            logger.info(f"✅ Successfully downloaded segment {segment_num}")
            logger.debug(f"Segment size: {len(result)} bytes")
        else:
            logger.error(f"❌ Failed to download segment {segment_num}")
            
    except Exception as e:
        logger.error(f"💥 Error during download: {e}")

if __name__ == "__main__":
    asyncio.run(test_download())
