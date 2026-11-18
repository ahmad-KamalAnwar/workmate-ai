from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

CSRF_HEADER = "X-Requested-With"
CSRF_VALUE = "workmate"
_SAFE_METHODS = frozenset({"GET", "HEAD", "OPTIONS"})


class CSRFHeaderMiddleware(BaseHTTPMiddleware):
    """Require a custom header on state-changing requests.

    Browsers cannot attach custom headers to cross-site form posts, and a cross-origin
    fetch with one triggers a CORS preflight that this API does not allow. Combined with
    the SameSite session cookie this blocks CSRF.
    """

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.method not in _SAFE_METHODS and request.headers.get(CSRF_HEADER) != CSRF_VALUE:
            return JSONResponse(
                {"error": {"code": "csrf_failed", "message": f"Missing {CSRF_HEADER} header"}},
                status_code=403,
            )
        return await call_next(request)
