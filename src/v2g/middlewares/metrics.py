import time

from fastapi import Request, Response
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    Counter,
    Histogram,
    generate_latest,
    multiprocess,
)
from starlette.middleware.base import BaseHTTPMiddleware

from v2g.core.config import PATHES_TO_SKIP_METRICS_FOR

REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'path', 'status'],
)

REQUEST_LATENCY = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency in seconds',
    ['method', 'path'],
)

ERROR_COUNT = Counter(
    'http_errors_total',
    'Total HTTP errors',
    ['method', 'path', 'status'],
)


class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # Doesn't work for paths with parameters!
        if path in PATHES_TO_SKIP_METRICS_FOR:
            return await call_next(request)

        start_at = time.perf_counter()

        exception = None
        try:
            response = await call_next(request)
            status = response.status_code
        except Exception as exc:
            exception = exc

        request_time = time.perf_counter() - start_at
        method = request.method

        # Thus 'path' contains things like '/api/v1/conversions/{conversion_id}/'.
        # It allows to group metrics of same route.
        route = request.scope.get('route')
        if route:
            path = route.path

        if exception:
            status = 500
        else:
            status = response.status_code

        REQUEST_COUNT.labels(method=method, path=path, status=status).inc()
        REQUEST_LATENCY.labels(method=method, path=path).observe(request_time)

        if status >= 400:
            ERROR_COUNT.labels(method=method, path=path, status=status).inc()

        if exception:
            raise exception

        return response


def metrics_route(_: Request):
    registry = CollectorRegistry()
    multiprocess.MultiProcessCollector(registry)
    return Response(
        generate_latest(registry),
        status_code=200,
        headers={'Content-Type': CONTENT_TYPE_LATEST},
    )
