"""
Simple in-memory rate limiter for API endpoints.

Provides protection against API abuse for AI-intensive endpoints.
"""
import time
from functools import wraps
from flask import request, jsonify

# Store: {ip: [timestamps]}
_rate_limits = {}
WINDOW_SECONDS = 60
MAX_REQUESTS = 10  # 10 requests per minute


def rate_limit(f):
    """
    Decorator to limit requests per IP address.
    
    Returns 429 Too Many Requests when limit exceeded.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        ip = request.remote_addr or 'unknown'
        now = time.time()
        
        # Clean old entries outside the window
        if ip in _rate_limits:
            _rate_limits[ip] = [t for t in _rate_limits[ip] if now - t < WINDOW_SECONDS]
        else:
            _rate_limits[ip] = []
        
        # Check if over limit
        if len(_rate_limits[ip]) >= MAX_REQUESTS:
            return jsonify({
                "error": "Rate limit exceeded",
                "retry_after_seconds": WINDOW_SECONDS
            }), 429
        
        # Record this request
        _rate_limits[ip].append(now)
        return f(*args, **kwargs)
    return decorated


def get_rate_limit_status(ip: str = None) -> dict:
    """Get current rate limit status for debugging."""
    if ip is None:
        return {"total_ips_tracked": len(_rate_limits)}
    
    now = time.time()
    if ip in _rate_limits:
        active = [t for t in _rate_limits[ip] if now - t < WINDOW_SECONDS]
        return {
            "ip": ip,
            "requests_in_window": len(active),
            "max_requests": MAX_REQUESTS,
            "window_seconds": WINDOW_SECONDS
        }
    return {"ip": ip, "requests_in_window": 0}
