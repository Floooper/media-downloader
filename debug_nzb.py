#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, '/mnt/md0/hosted/applications/media-downloader/src')

# Debug the NZBDownloader class
try:
    from services.nzb_service import NZBDownloader
    print("✅ Successfully imported NZBDownloader")
    
    # Create an instance
    nzb = NZBDownloader(
        usenet_server="test.server.com",
        port=563,
        use_ssl=True,
        username="test",
        password="test"
    )
    print("✅ Successfully created NZBDownloader instance")
    
    # Check if method exists
    if hasattr(nzb, '_count_files_and_segments'):
        print("✅ _count_files_and_segments method exists")
        print(f"Method type: {type(getattr(nzb, '_count_files_and_segments'))}")
        
        # Test calling it with dummy content
        try:
            result = nzb._count_files_and_segments("<?xml version='1.0'?><nzb></nzb>")
            print(f"✅ Method call successful: {result}")
        except Exception as e:
            print(f"❌ Error calling method: {e}")
    else:
        print("❌ _count_files_and_segments method does NOT exist")
        
    # List all methods
    print("\nAll methods in NZBDownloader:")
    methods = [m for m in dir(nzb) if not m.startswith('__')]
    for method in sorted(methods):
        if method.startswith('_count') or 'count' in method.lower():
            print(f"  🔍 {method}")
        else:
            print(f"  - {method}")
            
except Exception as e:
    print(f"❌ Import error: {e}")
    import traceback
    traceback.print_exc()
