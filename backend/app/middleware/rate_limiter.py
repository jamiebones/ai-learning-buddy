import time
from collections import defaultdict
from typing import Callable, Dict, Tuple

from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware for rate limiting requests by IP address.
    
    Attributes:
        limit: Maximum number of requests allowed in the timeframe
        timeframe: Time window in seconds for the limit
    """
    
    def __init__(
        self, 
        app,
        limit: int = 100,
        timeframe: int = 60,
    ):
        super().__init__(app)
        self.limit = limit
        self.timeframe = timeframe
        # Store request timestamps: {ip_address: [(timestamp, count), ...]}
        self._requests: Dict[str, list] = defaultdict(list)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Get client IP
        client_ip = request.client.host if request.client else "unknown"
        
        # Check if rate limit is exceeded
        if self._is_rate_limited(client_ip):
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"detail": "Rate limit exceeded. Please try again later."},
                headers={"Retry-After": str(self.timeframe)}
            )
        
        # Add current request to history
        self._add_request(client_ip)
        
        # Process the request
        return await call_next(request)
    
    def _is_rate_limited(self, client_ip: str) -> bool:
        """Check if client IP has exceeded rate limit."""
        now = time.time()
        
        # Clean up old request records
        self._clean_old_requests(client_ip, now)
        
        # Count requests in current timeframe
        request_count = sum(count for _, count in self._requests[client_ip])
        
        return request_count >= self.limit
    
    def _add_request(self, client_ip: str) -> None:
        """Add current request to history."""
        now = time.time()
        
        # Attempt to increment the count for the current second
        if self._requests[client_ip] and now - self._requests[client_ip][-1][0] < 1:
            # Same second, increment count
            timestamp, count = self._requests[client_ip][-1]
            self._requests[client_ip][-1] = (timestamp, count + 1)
        else:
            # New second
            self._requests[client_ip].append((now, 1))
    
    def _clean_old_requests(self, client_ip: str, now: float) -> None:
        """Remove request records older than the timeframe."""
        cutoff = now - self.timeframe
        self._requests[client_ip] = [
            (timestamp, count) 
            for timestamp, count in self._requests[client_ip] 
            if timestamp >= cutoff
        ] 