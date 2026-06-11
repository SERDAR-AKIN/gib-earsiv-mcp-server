from fastmcp import FastMCP, Context
from fastmcp.server.middleware.error_handling import RetryMiddleware, ErrorHandlingMiddleware
from fastmcp.server.middleware.rate_limiting import RateLimitingMiddleware
import httpx

from .core.session import app_lifespan
from .core.config import settings

mcp = FastMCP(
    "GIB e-Arsiv MCP", 
    lifespan=app_lifespan
)

mcp.add_middleware(ErrorHandlingMiddleware(
    include_traceback=True,
    transform_errors=True
))

mcp.add_middleware(RateLimitingMiddleware(
    max_requests_per_second=10,
    burst_capacity=30,
    global_limit=False
))

mcp.add_middleware(RetryMiddleware(
    max_retries=3,
    base_delay=1.0,
    max_delay=10.0,
    backoff_multiplier=2.0,
    retry_exceptions=(ConnectionError, TimeoutError, httpx.HTTPStatusError),
))

from . import tools

if __name__ == "__main__":
    mcp.run()
