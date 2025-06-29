"""Manual yEnc decoder implementation"""
import re
from typing import Optional

def _decode_char(c: int) -> int:
    """Decode a single yEnc character"""
    c = c - 42 if c >= 42 else 256 - (42 - c)
    return c & 0xFF  # Keep in byte range

def _calc_crc32(data: bytes) -> int:
    """Calculate CRC32 checksum"""
    crc = 0xFFFFFFFF
    for b in data:
        crc ^= b
        for _ in range(8):
            if crc & 1:
                crc = (crc >> 1) ^ 0xEDB88320
            else:
                crc >>= 1
    return ~crc & 0xFFFFFFFF

def decode_yenc(data: bytes) -> Optional[bytes]:
    """Manual yEnc decoder implementation
    
    Args:
        data: Raw yEnc encoded data
        
    Returns:
        Decoded data as bytes, or None if decoding fails
    """
    try:
        # Convert to string for regex
        content = data.decode('utf-8', errors='ignore')
        
        # Find yEnc header
        header_match = re.search(r'=ybegin.*size=(\d+)', content)
        if not header_match:
            return None
            
        # Extract encoded data between =ybegin and =yend
        encoded_data = re.search(r'=ybegin.*\r\n(.*?)\r\n=yend', content, re.DOTALL)
        if not encoded_data:
            return None
            
        encoded = encoded_data.group(1)
        decoded = bytearray()
        
        # Handle escaped chars and decode
        i = 0
        while i < len(encoded):
            c = ord(encoded[i])
            
            if c == ord('='):
                # Escape sequence
                i += 1
                if i < len(encoded):
                    c = ord(encoded[i])
                    decoded.append(_decode_char(c))
            elif c != ord('\r') and c != ord('\n'):
                # Normal character
                decoded.append(_decode_char(c))
                
            i += 1
            
        # Verify size if provided
        expected_size = int(header_match.group(1))
        if len(decoded) != expected_size:
            return None
            
        return bytes(decoded)
        
    except Exception:
        return None
