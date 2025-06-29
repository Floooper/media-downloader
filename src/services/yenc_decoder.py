"""Manual yEnc decoder implementation"""
import re
from typing import Optional, List, Dict

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

def _parse_yenc_header(header: str) -> Dict[str, str]:
    """Parse yEnc header into key-value pairs"""
    parts = header.split(' ')
    result = {}
    for part in parts:
        if '=' in part:
            key, value = part.split('=', 1)
            result[key] = value
    return result

def _find_yenc_parts(content: str) -> List[Dict[str, str]]:
    """Find all yEnc parts in content"""
    parts = []
    ybegin_pattern = r'=ybegin .*?\r\n'
    ypart_pattern = r'=ypart .*?\r\n'
    yend_pattern = r'\r\n=yend.*'
    
    # Find all ybegin sections
    positions = [(m.start(), m.end()) for m in re.finditer(ybegin_pattern, content, re.DOTALL)]
    
    for i, (start, header_end) in enumerate(positions):
        try:
            # Find the next ybegin or end of content
            next_start = positions[i + 1][0] if i + 1 < len(positions) else len(content)
            part_text = content[start:next_start]
            
            # Parse headers
            ybegin_text = re.search(ybegin_pattern, part_text).group(0)
            ybegin = _parse_yenc_header(ybegin_text.strip())
            
            # Check for ypart header
            ypart_match = re.search(ypart_pattern, part_text)
            ypart = _parse_yenc_header(ypart_match.group(0).strip()) if ypart_match else {}
            
            # Find yend header
            yend_match = re.search(yend_pattern, part_text)
            yend = _parse_yenc_header(yend_match.group(0).strip()) if yend_match else {}
            
            # Extract data
            data_start = header_end
            if ypart_match:
                data_start = ypart_match.end()
            data_end = yend_match.start() if yend_match else next_start
            
            parts.append({
                'ybegin': ybegin,
                'ypart': ypart,
                'yend': yend,
                'data': part_text[data_start:data_end].strip()
            })
            
        except Exception:
            continue
            
    return parts

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
        
        # Find all yEnc parts
        parts = _find_yenc_parts(content)
        if not parts:
            return None
            
        # Process each part
        decoded_parts = []
        for part in parts:
            try:
                encoded = part['data']
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
                
                # Add to parts list in correct order
                part_num = int(part['ypart'].get('part', '1')) - 1 if part['ypart'] else 0
                while len(decoded_parts) <= part_num:
                    decoded_parts.append(None)
                decoded_parts[part_num] = bytes(decoded)
                
            except Exception:
                continue
        
        # Combine parts
        if all(p is not None for p in decoded_parts):
            return b''.join(decoded_parts)
            
        return None
        
    except Exception:
        return None
