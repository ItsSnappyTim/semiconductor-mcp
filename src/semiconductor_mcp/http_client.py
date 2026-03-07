"""Process-wide shared httpx.AsyncClient with centralised retry/timeout policy.

All source adapters should call get_client() instead of creating per-call clients.
This enables TCP connection reuse across requests and keeps resilience policy in
one place rather than scattered across 11 source modules.
"""

import asyncio
import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)

_DEFAULT_HEADERS = {"User-Agent": "semiconductor-mcp-research/1.0"}
_client: httpx.AsyncClient | None = None


def get_client() -> httpx.AsyncClient:
    """Return the process-wide shared HTTP client, creating it if needed."""
    global _client
    if _client is None or _client.is_closed:
        _client = httpx.AsyncClient(
            headers=_DEFAULT_HEADERS,
            timeout=httpx.Timeout(30.0),
            follow_redirects=True,
        )
    return _client


async def close_client() -> None:
    """Gracefully close the shared client. Call on server shutdown."""
    global _client
    if _client and not _client.is_closed:
        await _client.aclose()
    _client = None


def reset_client() -> None:
    """Discard the cached client reference so the next get_client() call creates a
    fresh one. Used in tests to ensure each test gets a clean client that respx
    can patch at the transport level.
    """
    global _client
    _client = None


async def request_with_retry(
    url: str,
    *,
    method: str = "GET",
    params: Any = None,
    headers: dict[str, str] | None = None,
    json: Any = None,
    data: Any = None,
    timeout: float = 30.0,
    retry_delays: list[float] | None = None,
) -> httpx.Response:
    """Make an HTTP request, retrying on 429 with configurable backoff.

    Returns the final response. Does NOT call raise_for_status() — callers
    decide how to handle non-2xx statuses, including exhausted-429 responses.

    Raises the last httpx network exception if all attempts fail due to
    connectivity/timeout errors.

    Args:
        url: Target URL.
        method: HTTP method (default GET).
        params: Query parameters.
        headers: Additional request headers merged with client defaults.
        json: JSON-serialisable request body.
        data: Form-encoded request body.
        timeout: Per-request timeout in seconds.
        retry_delays: Seconds to wait before each retry, e.g. [3.0, 6.0] gives
                      up to 3 attempts (initial + 2 retries).
    """
    delays = [0.0, *(retry_delays or [])]
    client = get_client()
    last_resp: httpx.Response | None = None

    for i, delay in enumerate(delays):
        if delay:
            await asyncio.sleep(delay)
        try:
            resp = await client.request(
                method,
                url,
                params=params,
                headers=headers,
                json=json,
                data=data,
                timeout=timeout,
            )
            if resp.status_code == 429 and i < len(delays) - 1:
                last_resp = resp
                logger.debug(
                    "Rate limited by %s (attempt %d/%d), retrying in %.1fs",
                    url, i + 1, len(delays), delays[i + 1],
                )
                continue
            return resp
        except (httpx.TimeoutException, httpx.ConnectError, httpx.ReadError) as exc:
            if i < len(delays) - 1:
                logger.debug("Request to %s failed (%s), retrying", url, exc)
                continue
            raise

    # All retries exhausted on 429 — return the last 429 response
    if last_resp is not None:
        return last_resp
    raise RuntimeError(f"request_with_retry: no response or exception for {url}")
