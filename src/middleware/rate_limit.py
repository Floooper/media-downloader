import time
from typing import Dict, Optional, Tuple
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from ..config import settings

class RateLimiter:
    """Rate limiting implementation using sliding window"""
    def __init__(self, window_size: int = 60, max_requests: int = 100):
        self.window_size = window_size  # seconds
        self.max_requests = max_requests
        self.requests: Dict[str, list] = {}  # client_id -> list of timestamps

    def is_rate_limited(self, client_id: str) -> Tuple[bool, Optional[float]]:
        """Check if client is rate limited"""
        now = time.time()
        
        # Remove old requests outside the window
        if client_id in self.requests:
            self.requests[client_id] = [
                ts for ts in self.requests[client_id]
                if now - ts < self.window_size
            ]
        else:
            self.requests[client_id] = []
        
        # Check number of requests in window
        if len(self.requests[client_id]) >= self.max_requests:
            oldest_timestamp = min(self.requests[client_id])
            retry_after = oldest_timestamp + self.window_size - now
            return True, retry_after
        
        # Add new request
        self.requests[client_id].append(now)
        return False, None

    def get_remaining(self, client_id: str) -> int:
        """Get remaining requests in current window"""
        if client_id not in self.requests:
            return self.max_requests
        
        now = time.time()
        current_requests = len([
            ts for ts in self.requests[client_id]
            if now - ts < self.window_size
        ])
        return max(0, self.max_requests - current_requests)

# Create rate limiters for different client types
authenticated_limiter = RateLimiter(
    window_size=60,
    max_requests=settings.API_RATE_LIMIT
)
unauthenticated_limiter = RateLimiter(
    window_size=60,
    max_requests=settings.API_RATE_LIMIT // 10
)

async def rate_limit_middleware(request: Request, call_next):
    """Middleware for rate limiting requests"""
    # Skip rate limiting for WebSocket connections
    if request.url.path.startswith("/api/ws"):
        return await call_next(request)
    
    # Get client identifier
    client_id = request.headers.get("Authorization", request.client.host)
    
    # Choose appropriate limiter
    limiter = authenticated_limiter if "Authorization" in request.headers else unauthenticated_limiter
    
    # Check rate limit
    is_limited, retry_after = limiter.is_rate_limited(client_id)
    if is_limited:
        return JSONResponse(
            status_code=429,
            content={
                "detail": "Too many requests",
                "retry_after": retry_after
            },
            headers={
                "Retry-After": str(int(retry_after)),
                "X-RateLimit-Limit": str(limiter.max_requests),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(int(time.time() + retry_after))
            }
        )
    
    # Add rate limit headers
    response = await call_next(request)
    remaining = limiter.get_remaining(client_id)
    response.headers["X-RateLimit-Limit"] = str(limiter.max_requests)
    response.headers["X-RateLimit-Remaining"] = str(remaining)
    response.headers["X-RateLimit-Reset"] = str(
        int(time.time() + limiter.window_size)
    )
    
    return response

class WebSocketRateLimiter:
    """Rate limiting for WebSocket connections"""
    def __init__(self, max_messages: int = 100, window_size: int = 60):
        self.max_messages = max_messages
        self.window_size = window_size
        self.connections: Dict[str, Dict] = {}

    async def check_limit(self, client_id: str) -> bool:
        """Check if client has exceeded message limit"""
        now = time.time()
        
        if client_id not in self.connections:
            self.connections[client_id] = {
                "messages": [],
                "last_warning": 0
            }
        
        conn = self.connections[client_id]
        
        # Remove old messages
        conn["messages"] = [
            ts for ts in conn["messages"]
            if now - ts < self.window_size
        ]
        
        # Check limit
        if len(conn["messages"]) >= self.max_messages:
            # Only send warning once per window
            if now - conn["last_warning"] > self.window_size:
                conn["last_warning"] = now
                return False
            return True
        
        # Add new message
        conn["messages"].append(now)
        return False

    def remove_client(self, client_id: str):
        """Remove client from tracking"""
        self.connections.pop(client_id, None)

# Create WebSocket rate limiter
ws_rate_limiter = WebSocketRateLimiter(
    max_messages=settings.WS_MESSAGE_QUEUE_SIZE,
    window_size=60
)
