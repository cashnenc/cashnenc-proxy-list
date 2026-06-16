import asyncio
from src.validator import validate_proxies


def test_validate_empty_list():
    res = asyncio.run(validate_proxies([]))
    assert isinstance(res, list)
    assert res == []
