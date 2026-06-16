import asyncio
from aioresponses import aioresponses
from src import validator


def test_validate_http_success():
    proxies = ["1.2.3.4:8080"]
    with aioresponses() as m:
        m.get("http://httpbin.org/ip", status=200, body='{"origin":"1.2.3.4"}')
        res = asyncio.run(validator.validate_proxies(proxies, concurrency=1, timeout=5, retries=0))
        assert isinstance(res, list)
        assert res[0]["ok"] is True


def test_validate_http_failure():
    proxies = ["5.6.7.8:8080"]
    with aioresponses() as m:
        m.get("http://httpbin.org/ip", status=500)
        res = asyncio.run(validator.validate_proxies(proxies, concurrency=1, timeout=5, retries=0))
        assert res[0]["ok"] is False


def test_validate_socks_without_dependency(monkeypatch):
    monkeypatch.setattr(validator, "_HAS_SOCKS", False)
    proxies = ["socks5://9.9.9.9:1080"]
    res = asyncio.run(validator.validate_proxies(proxies, concurrency=1, timeout=5, retries=0))
    assert "error" in res[0] and "socks support" in res[0]["error"]
