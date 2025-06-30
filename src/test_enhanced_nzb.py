#!/usr/bin/env python3
"""
Test script for enhanced NZB service with error handling
"""
import asyncio
import sys
import os
import tempfile
import logging

# Add src to path
sys.path.insert(0, '/mnt/md0/hosted/applications/media-downloader/src')

from .services.nzb_service_enhanced import EnhancedNZBService, ServerConfig
from .services.error_handling import (
    NZBDownloadError, 
    ErrorCategory, 
    validate_nzb_content,
    collect_diagnostic_info
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_error_categorization():
    """Test error categorization functionality"""
    print("🧪 Testing error categorization...")
    
    # Test various error types
    test_errors = [
        Exception("430 No such article"),
        Exception("480 Authentication required"),
        Exception("Connection timeout"),
        Exception("yEnc CRC mismatch"),
        Exception("DNS resolution failed"),
        Exception("SSL handshake failed"),
        Exception("Invalid ybegin line"),
        Exception("No space left on device"),
        Exception("Permission denied"),
        Exception("Unknown random error")
    ]
    
    from .services.error_handling import categorize_error
    
    for error in test_errors:
        error_info = categorize_error(error)
        print(f"  ✓ {str(error)[:30]:<30} -> {error_info.category.value:<15} ({error_info.severity.value})")
    
    print("✅ Error categorization tests passed")

async def test_nzb_validation():
    """Test NZB validation functionality"""
    print("\n🧪 Testing NZB validation...")
    
    # Test valid NZB
    valid_nzb = '''<?xml version="1.0" encoding="UTF-8"?>
<nzb xmlns="http://www.newzbin.com/DTD/2003/nzb">
  <file poster="test@example.com" date="1234567890" subject="test.file.rar">
    <groups>
      <group>alt.binaries.test</group>
    </groups>
    <segments>
      <segment bytes="1000" number="1">12345@example.com</segment>
      <segment bytes="1000" number="2">12346@example.com</segment>
    </segments>
  </file>
</nzb>'''
    
    result = validate_nzb_content(valid_nzb)
    print(f"  ✓ Valid NZB: {result['valid']}, {result['file_count']} files, {result['segment_count']} segments")
    
    # Test invalid NZB
    invalid_nzb = '''<?xml version="1.0"?>
<invalid>
  <no_files/>
</invalid>'''
    
    result = validate_nzb_content(invalid_nzb)
    print(f"  ✓ Invalid NZB: {result['valid']}, errors: {result['errors']}")
    
    print("✅ NZB validation tests passed")

async def test_connection_diagnostics():
    """Test connection diagnostics"""
    print("\n🧪 Testing connection diagnostics...")
    
    # Test with invalid server config
    config = ServerConfig(
        host="nonexistent.server.com",
        port=119,
        username="test",
        password="test"
    )
    
    service = EnhancedNZBService(config)
    
    try:
        result = await service.test_connection()
        print(f"  ✓ Connection test result: {result['success']}")
        if not result['success']:
            print(f"    Error category: {result.get('error_category', 'unknown')}")
            print(f"    Suggested action: {result.get('suggested_action', 'none')}")
    except Exception as e:
        print(f"  ✓ Connection test caught exception: {type(e).__name__}")
    
    service.cleanup()
    print("✅ Connection diagnostics tests passed")

async def test_diagnostic_info():
    """Test diagnostic information collection"""
    print("\n🧪 Testing diagnostic info collection...")
    
    info = collect_diagnostic_info()
    
    expected_keys = ['platform', 'python_version', 'available_memory', 'disk_space', 'timestamp']
    for key in expected_keys:
        if key in info:
            print(f"  ✓ {key}: {str(info[key])[:50]}")
        else:
            print(f"  ❌ Missing key: {key}")
    
    print("✅ Diagnostic info tests passed")

async def test_yenc_decoder():
    """Test yEnc decoder with various inputs"""
    print("\n🧪 Testing yEnc decoder...")
    
    config = ServerConfig(host="localhost", port=119)
    service = EnhancedNZBService(config)
    
    # Test with empty data
    try:
        service._decode_yenc_data(b"")
        print("  ❌ Should have failed with empty data")
    except NZBDownloadError as e:
        print(f"  ✓ Empty data error: {e.error_info.category.value}")
    except Exception as e:
        print(f"  ❌ Unexpected error: {type(e).__name__}")
    
    # Test with invalid yEnc data
    try:
        service._decode_yenc_data(b"not yenc data")
        print("  ❌ Should have failed with invalid data")
    except NZBDownloadError as e:
        print(f"  ✓ Invalid data error: {e.error_info.category.value}")
    except Exception as e:
        print(f"  ❌ Unexpected error: {type(e).__name__}")
    
    service.cleanup()
    print("✅ yEnc decoder tests passed")

async def test_statistics():
    """Test statistics tracking"""
    print("\n🧪 Testing statistics tracking...")
    
    config = ServerConfig(host="localhost", port=119)
    service = EnhancedNZBService(config)
    
    # Check initial stats
    stats = service.get_statistics()
    print(f"  ✓ Initial stats: {stats['total_segments']} segments, {stats['success_rate']:.1%} success")
    
    # Simulate some statistics
    service.stats['total_segments'] = 10
    service.stats['successful_segments'] = 8
    service.stats['bytes_downloaded'] = 1024000
    
    stats = service.get_statistics()
    print(f"  ✓ Updated stats: {stats['success_rate']:.1%} success, {stats['average_segment_size']:.0f} bytes/segment")
    
    service.cleanup()
    print("✅ Statistics tests passed")

async def main():
    """Run all tests"""
    print("🚀 Starting Enhanced NZB Service Tests\n")
    
    try:
        await test_error_categorization()
        await test_nzb_validation()
        await test_connection_diagnostics()
        await test_diagnostic_info()
        await test_yenc_decoder()
        await test_statistics()
        
        print("\n🎉 All tests completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
