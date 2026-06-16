import json
from src.formatter import to_json, to_txt, to_csv


def test_to_json_and_txt_and_csv():
    validated = [
        {"proxy": "1.1.1.1:8080", "ok": True, "latency_ms": 123},
        {"proxy": "2.2.2.2:8080", "ok": False, "latency_ms": None},
    ]

    j = to_json(validated)
    assert isinstance(j, str)
    parsed = json.loads(j)
    assert isinstance(parsed, list)
    assert parsed[0]["proxy"] == "1.1.1.1:8080"

    txt = to_txt(validated)
    assert txt.strip() == "1.1.1.1:8080"

    csv = to_csv(validated)
    # header + 2 rows
    assert "proxy,ok,latency_ms" in csv
    assert "1.1.1.1:8080" in csv
    assert "2.2.2.2:8080" in csv
