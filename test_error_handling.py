#!/usr/bin/env python3

import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import logging
import asyncio
import pytest
from services.error_handling import (
    ErrorCategory, ErrorInfo, categorize_error, NZBDownloadError,
    validate_nzb_content, collect_diagnostic_info, EnhancedRetryHandler,
    log_error_with_context
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_error_categorization():
    """Test error categorization functionality"""
    logger.info("Testing error categorization...")
    
    test_errors = [
        ConnectionError("Connection timed out"),
        Exception("No such group"),
        Exception("Authentication failed"), 
        Exception("Article not found"),
        Exception("yEnc decode error"),
        Exception("Invalid segment data"),
        Exception("Too many connections")
    ]
    
    for error in test_errors:
        error_info = categorize_error(error)
        logger.info(f"Error: '{str(error)}' -> Category: {error_info.category.value}, Severity: {error_info.severity.value}")
    
    logger.info("✓ Error categorization test completed")

def test_nzb_validation():
    """Test NZB XML validation"""
    logger.info("Testing NZB validation...")
    
    # Valid NZB XML
    valid_nzb = '''<?xml version="1.0" encoding="UTF-8"?>
    <nzb xmlns="http://www.newzbin.com/DTD/2003/nzb">
        <file poster="test@example.com" date="1234567890" subject="Test File">
            <groups>
                <group>alt.binaries.test</group>
            </groups>
            <segments>
                <segment bytes="1000" number="1">123456789@test.com</segment>
            </segments>
        </file>
    </nzb>'''
    
    # Invalid NZB XML
    invalid_nzb = '''<?xml version="1.0" encoding="UTF-8"?>
    <nzb xmlns="http://www.newzbin.com/DTD/2003/nzb">
        <file poster="test@example.com" date="1234567890" subject="Test File">
            <groups>
            </groups>
        </file>
    </nzb>'''
    
    try:
        validation_result = validate_nzb_content(valid_nzb)
        logger.info(f"Valid NZB validation result: {validation_result}")
        
        validation_result = validate_nzb_content(invalid_nzb)
        logger.info(f"Invalid NZB validation result: {validation_result}")
        
        logger.info("✓ NZB validation test completed")
    except Exception as e:
        logger.error(f"NZB validation test failed: {e}")

def test_diagnostic_collection():
    """Test diagnostic information collection"""
    logger.info("Testing diagnostic collection...")
    
    try:
        diagnostics = collect_diagnostic_info()
        logger.info(f"Diagnostics collected: {len(diagnostics)} items")
        for key, value in diagnostics.items():
            logger.info(f"  {key}: {value}")
        
        logger.info("✓ Diagnostic collection test completed")
    except Exception as e:
        logger.error(f"Diagnostic collection test failed: {e}")

@pytest.mark.asyncio
async def test_retry_handler():
    """Test enhanced retry handler"""
    logger.info("Testing retry handler...")
    
    attempt_count = 0
    
    async def failing_operation():
        nonlocal attempt_count
        attempt_count += 1
        if attempt_count < 3:
            raise ConnectionError("Simulated connection error")
        return f"Success after {attempt_count} attempts"
    
    try:
        retry_handler = EnhancedRetryHandler(max_retries=3, base_delay=0.1)
        result = await retry_handler.retry_async(failing_operation, "test operation")
        logger.info(f"Retry test result: {result}")
        logger.info("✓ Retry handler test completed")
    except Exception as e:
        logger.error(f"Retry handler test failed: {e}")

def test_error_logging():
    """Test error logging with context"""
    logger.info("Testing error logging...")
    
    try:
        error = NZBDownloadError("CONNECTION_FAILED", "Test connection error", {"server": "test.server"})
        log_error_with_context(error, {"operation": "test_download"})
        logger.info("✓ Error logging test completed")
    except Exception as e:
        logger.error(f"Error logging test failed: {e}")

if __name__ == "__main__":
    asyncio.run(run_all_tests())
