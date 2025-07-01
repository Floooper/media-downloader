# Upload Size Limits Configuration Summary

## Changes Implemented (2025-06-29)

### 1. Nginx Configuration Updates
**File:** `/etc/nginx/sites-available/media.floopy.org`
- **Added:** `client_max_body_size 100M;`
- **Added:** Extended timeouts for API uploads:
  - `proxy_connect_timeout 60s;`
  - `proxy_send_timeout 60s;`
  - `proxy_read_timeout 60s;`

**Before:** Default 1MB limit (nginx default)
**After:** 100MB limit for all uploads

### 2. Application Configuration Updates
**File:** `src/config.py`
- **Added:** `MAX_NZB_FILE_SIZE_MB: int = 50` (increased from 10MB)
- **Added:** `MAX_TORRENT_FILE_SIZE_MB: int = 20` (new limit)

### 3. API Code Improvements
**File:** `src/api/downloads.py`
- **Enhanced:** File size validation using configuration settings
- **Enhanced:** Better error messages with specific file sizes
- **Added:** New endpoint `/api/downloads/limits` to check current limits
- **Fixed:** Route ordering to prevent conflicts

### 4. Service Configuration
**File:** `/etc/systemd/system/media-downloader.service`
- **Fixed:** Database initialization issues
- **Created:** Separate `init_db.py` script for cleaner service startup

## Current Upload Limits

### NZB Files
- **Application Limit:** 50MB (configurable via MAX_NZB_FILE_SIZE_MB)
- **Nginx Limit:** 100MB
- **Effective Limit:** 50MB (application enforced)

### Torrent Files
- **Application Limit:** 20MB (configurable via MAX_TORRENT_FILE_SIZE_MB)
- **Nginx Limit:** 100MB
- **Effective Limit:** 20MB (application enforced)

### General Upload Limit
- **Nginx Limit:** 100MB (for all requests)

## How to Check Current Limits

### Via API:
```bash
curl http://localhost:8000/api/downloads/limits
```

### Via Configuration:
- Application limits: `src/config.py`
- Nginx limits: `/etc/nginx/sites-available/media.floopy.org`

## How to Modify Limits

### To Change Application Limits:
1. Edit `src/config.py`
2. Modify `MAX_NZB_FILE_SIZE_MB` or `MAX_TORRENT_FILE_SIZE_MB`
3. Restart service: `sudo systemctl restart media-downloader`

### To Change Nginx Limits:
1. Edit `/etc/nginx/sites-available/media.floopy.org`
2. Modify `client_max_body_size` value
3. Test config: `sudo nginx -t`
4. Reload nginx: `sudo systemctl reload nginx`

### Environment Variables:
You can also set these via environment variables:
```bash
export MAX_NZB_FILE_SIZE_MB=75
export MAX_TORRENT_FILE_SIZE_MB=30
```

## Error Messages

### File Too Large (NZB):
`HTTP 413: File too large. Maximum size for NZB files is 50MB. Your file is X.XMB.`

### File Too Large (Torrent):
`HTTP 413: File too large. Maximum size for torrent files is 20MB. Your file is X.XMB.`

### Nginx Limit Exceeded:
`HTTP 413: Request Entity Too Large` (when file exceeds 100MB)

## Testing the Limits

### Test with curl:
```bash
# Test limits endpoint
curl http://localhost:8000/api/downloads/limits

# Test NZB upload (replace with actual file)
curl -X POST -F "file=@test.nzb" http://localhost:8000/api/downloads/nzb-file

# Test torrent upload (replace with actual file)
curl -X POST -F "file=@test.torrent" http://localhost:8000/api/downloads/torrent-file
```

## Files Modified/Created

1. `/etc/nginx/sites-available/media.floopy.org` (modified)
2. `/etc/nginx/sites-available/media.floopy.org.backup` (created)
3. `src/config.py` (modified)
4. `src/config.py.backup` (created)
5. `src/api/downloads.py` (modified)
6. `src/api/downloads.py.backup` (created)
7. `/etc/systemd/system/media-downloader.service` (modified)
8. `init_db.py` (created)

## Service Status
- **Service:** `media-downloader.service` - Active and running
- **Nginx:** Configuration reloaded with new limits
- **API:** Available at http://localhost:8000 and https://media.floopy.org
