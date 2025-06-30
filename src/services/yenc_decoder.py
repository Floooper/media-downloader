"""
yEnc decoder implementation
"""
import logging
import re

logger = logging.getLogger(__name__)

def decode_yenc_data(data: bytes) -> bytes:
    """Perform the actual yEnc decoding"""
    decoded = bytearray()
    i = 0
    while i < len(data):
        char = data[i:i+1]
        if char == b"=":
            # Handle yEnc escape
            i += 1
            if i < len(data):
                char = bytes([(data[i] - 64) & 0xFF])
        else:
            # Regular yEnc decoding
            char = bytes([(data[i] - 42) & 0xFF])
        decoded.extend(char)
        i += 1
    return bytes(decoded)

def decode_yenc(data: bytes) -> bytes:
    """Decode yEnc encoded data"""
    try:
        # Convert to string for regex
        text = data.decode("ascii", errors="ignore")
        
        # Find yEnc data boundaries
        begin_match = re.search(r"=ybegin .+\r\n", text)
        if not begin_match:
            logger.error("No ybegin line found")
            return None
            
        # Extract line size from ybegin header
        line_size_match = re.search(r"line=(\d+)", begin_match.group(0))
        if not line_size_match:
            logger.error("No line size specified in ybegin")
            return None
            
        # Find end of header section
        header_end = begin_match.end()
        
        # Look for ypart if it exists
        part_match = re.search(r"=ypart .+\r\n", text[header_end:])
        if part_match:
            header_end = header_end + part_match.end()
            
        # Find yend marker
        end_match = re.search(r"\r\n=yend", text[header_end:])
        if not end_match:
            logger.error("No yend marker found")
            return None
            
        # Get actual data section
        encoded = text[header_end:header_end + end_match.start()].encode("ascii")
        
        # Remove line endings
        encoded = encoded.replace(b"\r\n", b"")
        
        # Decode the actual yEnc data
        return decode_yenc_data(encoded)
        
    except Exception as e:
        logger.error(f"Failed to decode yEnc data: {e}")
        return None
