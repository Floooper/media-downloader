#!/usr/bin/env python3

import sys
import os
import asyncio
import logging

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_import_enhanced_service():
    """Test importing the enhanced NZB service"""
    try:
        # Import without initializing to test syntax
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "nzb_service_enhanced", 
            "src/services/nzb_service_enhanced.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        logger.info("✓ Enhanced NZB service imports successfully")
        logger.info(f"Available classes: {[name for name in dir(module) if name[0].isupper()]}")
        return True
    except Exception as e:
        logger.error(f"✗ Enhanced NZB service import failed: {e}")
        return False

def test_error_handling_import():
    """Test importing error handling module"""
    try:
        from services.error_handling import (
            ErrorCategory, ErrorInfo, categorize_error, NZBDownloadError,
            validate_nzb_content, collect_diagnostic_info, EnhancedRetryHandler
        )
        logger.info("✓ Error handling module imports successfully")
        return True
    except Exception as e:
        logger.error(f"✗ Error handling import failed: {e}")
        return False

def test_current_service_functionality():
    """Test that the current NZB service still works"""
    try:
        # Test basic import first
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src', 'services'))
        import nzb_service
        
        logger.info("✓ Current NZB service imports successfully")
        
        # Check if we can create an instance (may fail due to missing dependencies)
        try:
            service = nzb_service.NZBService()
            logger.info("✓ NZB service can be instantiated")
        except Exception as e:
            logger.warning(f"NZB service instantiation failed (expected): {e}")
        
        return True
    except Exception as e:
        logger.error(f"✗ Current NZB service test failed: {e}")
        return False

def check_dependencies():
    """Check if required dependencies are available"""
    dependencies = {
        'pynzb': 'pynzb',
        'aiofiles': 'aiofiles', 
        'psutil': 'psutil',
        'nntplib': 'nntplib'
    }
    
    missing = []
    for name, module in dependencies.items():
        try:
            __import__(module)
            logger.info(f"✓ {name} is available")
        except ImportError:
            logger.warning(f"✗ {name} is missing")
            missing.append(name)
    
    return len(missing) == 0, missing

async def run_integration_tests():
    """Run all integration tests"""
    logger.info("Starting integration tests...")
    
    # Check dependencies first
    deps_ok, missing_deps = check_dependencies()
    if not deps_ok:
        logger.warning(f"Missing dependencies: {missing_deps}")
    
    # Test imports
    error_handling_ok = test_error_handling_import()
    current_service_ok = test_current_service_functionality()
    enhanced_service_ok = test_import_enhanced_service()
    
    # Summary
    results = {
        "Dependencies": deps_ok,
        "Error Handling": error_handling_ok,
        "Current Service": current_service_ok,
        "Enhanced Service": enhanced_service_ok
    }
    
    logger.info("Integration test results:")
    for test, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        logger.info(f"  {test}: {status}")
    
    all_passed = all(results.values())
    logger.info(f"Overall result: {'✓ ALL TESTS PASSED' if all_passed else '✗ SOME TESTS FAILED'}")
    
    return all_passed

if __name__ == "__main__":
    success = asyncio.run(run_integration_tests())
    sys.exit(0 if success else 1)
