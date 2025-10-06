"""
Rate Limiting and DDoS Protection
Implements rate limiting, connection throttling, and basic DDoS protection
"""

import time
import asyncio
from typing import Dict, Set
from collections import defaultdict, deque
from fastapi import Request, HTTPException, status
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import logging

logger = logging.getLogger(__name__)

class DDoSProtection:
    """Basic DDoS protection using connection tracking and rate limiting"""
    
    def __init__(self):
        # Track connections per IP
        self.connections_per_ip: Dict[str, Set] = defaultdict(set)
        # Track message frequency per IP
        self.message_counts: Dict[str, deque] = defaultdict(lambda: deque())
        # Track failed authentication attempts
        self.failed_auth: Dict[str, deque] = defaultdict(lambda: deque())
        
        # Configuration
        self.max_connections_per_ip = 5
        self.max_messages_per_minute = 60
        self.max_auth_failures = 5
        self.auth_lockout_duration = 300  # 5 minutes
        
    def get_client_ip(self, request: Request) -> str:
        """Get client IP address, considering proxies"""
        # Check for forwarded headers (behind proxy/load balancer)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fallback to direct connection IP
        return get_remote_address(request)
    
    def is_ip_blocked(self, ip: str) -> bool:
        """Check if IP is temporarily blocked due to failed auth attempts"""
        now = time.time()
        failures = self.failed_auth.get(ip, deque())
        
        # Clean old failures
        while failures and now - failures[0] > self.auth_lockout_duration:
            failures.popleft()
        
        # Check if too many recent failures
        if len(failures) >= self.max_auth_failures:
            logger.warning(f"IP {ip} is blocked due to excessive auth failures")
            return True
        
        return False
    
    def record_auth_failure(self, ip: str):
        """Record a failed authentication attempt"""
        now = time.time()
        self.failed_auth[ip].append(now)
        logger.warning(f"Auth failure recorded for IP: {ip}")
    
    def clear_auth_failures(self, ip: str):
        """Clear authentication failures for successful login"""
        if ip in self.failed_auth:
            del self.failed_auth[ip]
    
    def check_message_rate(self, ip: str) -> bool:
        """Check if IP is sending messages too frequently"""
        now = time.time()
        messages = self.message_counts[ip]
        
        # Clean old messages (older than 1 minute)
        while messages and now - messages[0] > 60:
            messages.popleft()
        
        # Check rate limit
        if len(messages) >= self.max_messages_per_minute:
            logger.warning(f"Rate limit exceeded for IP: {ip}")
            return False
        
        # Record this message
        messages.append(now)
        return True
    
    def add_connection(self, ip: str, connection_id: str):
        """Track a new connection from an IP"""
        connections = self.connections_per_ip[ip]
        connections.add(connection_id)
        
        if len(connections) > self.max_connections_per_ip:
            logger.warning(f"Too many connections from IP: {ip} ({len(connections)} connections)")
    
    def remove_connection(self, ip: str, connection_id: str):
        """Remove a connection from IP tracking"""
        if ip in self.connections_per_ip:
            self.connections_per_ip[ip].discard(connection_id)
            if not self.connections_per_ip[ip]:
                del self.connections_per_ip[ip]
    
    def get_connection_count(self, ip: str) -> int:
        """Get number of active connections for an IP"""
        return len(self.connections_per_ip.get(ip, set()))

# Global DDoS protection instance
ddos_protection = DDoSProtection()

# Rate limiter configuration
limiter = Limiter(
    key_func=ddos_protection.get_client_ip,
    default_limits=["100/minute", "10/second"]
)

def get_rate_limiter():
    """Get rate limiter instance"""
    return limiter

def get_ddos_protection():
    """Get DDoS protection instance"""
    return ddos_protection

# Custom rate limit exceeded handler
async def custom_rate_limit_handler(request: Request, exc: RateLimitExceeded):
    """Custom handler for rate limit exceeded"""
    ip = ddos_protection.get_client_ip(request)
    logger.warning(f"Rate limit exceeded for IP: {ip}")
    
    raise HTTPException(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        detail="Rate limit exceeded. Please try again later.",
        headers={"Retry-After": "60"}
    )
