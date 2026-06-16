"""
Async proxy validator. Attempts a simple HTTP GET through each proxy.
Supports HTTP/HTTPS proxies. For SOCKS support, aiohttp_socks is optional.
Improved to reuse a shared ClientSession for HTTP proxies and limited retries/backoff.
"""

import asyncio
import logging
import time
from typing import List, Dict, Optional

import aiohttp

try:
    from aiohttp_socks import ProxyConnector
    _HAS_SOCKS = True
except Exception:
    _HAS_SOCKS = False

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


async def _check_proxy_http(session: aiohttp.ClientSession, proxy: str, timeout: int = 10, retries: int = 1) -> Dict:
    result = {"proxy": proxy, "ok": False, "latency_ms": None}
    url = "http://httpbin.org/ip"
    proxy_url = proxy if "://" in proxy else f"http://{proxy}"
    backoff = 0.5
    for attempt in range(retries + 1):
        try:
            start = time.perf_counter()
            async with session.get(url, proxy=proxy_url, timeout=timeout) as r:
                if r.status == 200:
                    elapsed = time.perf_counter() - start
                    result["ok"] = True
                    result["latency_ms"] = int(elapsed * 1000)
                    return result
                else:
                    logger.debug("Proxy %s returned status %s", proxy, r.status)
        except Exception as exc:
            logger.debug("HTTP proxy %s attempt %d failed: %s", proxy, attempt, exc)
            if attempt < retries:
                await asyncio.sleep(backoff * (2 ** attempt))
    return result


async def _check_proxy_socks(proxy: str, timeout: int = 10, retries: int = 1) -> Dict:
    result = {"proxy": proxy, "ok": False, "latency_ms": None}
    if not _HAS_SOCKS:
        result["error"] = "socks support not installed (aiohttp_socks)"
        return result

    url = "http://httpbin.org/ip"
    backoff = 0.5
    for attempt in range(retries + 1):
        try:
            connector = ProxyConnector.from_url(proxy)
            timeout_obj = aiohttp.ClientTimeout(total=timeout)
            start = time.perf_counter()
            async with aiohttp.ClientSession(connector=connector, timeout=timeout_obj) as session:
                async with session.get(url) as r:
                    if r.status == 200:
                        elapsed = time.perf_counter() - start
                        result["ok"] = True
                        result["latency_ms"] = int(elapsed * 1000)
                        return result
                    else:
                        logger.debug("SOCKS proxy %s returned status %s", proxy, r.status)
        except Exception as exc:
            logger.debug("SOCKS proxy %s attempt %d failed: %s", proxy, attempt, exc)
            if attempt < retries:
                await asyncio.sleep(backoff * (2 ** attempt))
    return result


async def validate_proxies(proxies: List[str], concurrency: int = 50, timeout: int = 10, retries: int = 1) -> List[Dict]:
    """Validate a list of proxies concurrently and return their results.

    - Reuses a single aiohttp.ClientSession for HTTP(S) proxies.
    - Creates per-proxy sessions for SOCKS proxies using aiohttp_socks when available.
    - Limits concurrency via a semaphore.
    """
    results: List[Dict] = []
    sem = asyncio.Semaphore(concurrency)

    timeout_obj = aiohttp.ClientTimeout(total=timeout)

    async def _worker(session: aiohttp.ClientSession, p: str):
        async with sem:
            try:
                if p.lower().startswith("socks"):
                    return await _check_proxy_socks(p, timeout=timeout, retries=retries)
                else:
                    return await _check_proxy_http(session, p, timeout=timeout, retries=retries)
            except Exception as e:
                logger.debug("Unexpected error checking proxy %s: %s", p, e)
                return {"proxy": p, "ok": False, "latency_ms": None}

    async with aiohttp.ClientSession(timeout=timeout_obj) as shared_session:
        tasks = [asyncio.create_task(_worker(shared_session, p)) for p in proxies]
        for t in asyncio.as_completed(tasks):
            res = await t
            results.append(res)

    return results


if __name__ == "__main__":
    import asyncio

    sample = ["8.8.8.8:8080"]
    print(asyncio.run(validate_proxies(sample)))
