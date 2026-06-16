import csv
import json
import io
from typing import List, Dict


def to_json(validated: List[Dict]) -> str:
    return json.dumps(validated, indent=2)


def to_txt(validated: List[Dict]) -> str:
    # Return one proxy per line (ip:port) for proxies that passed validation
    lines = [r["proxy"] for r in validated if r.get("ok")]
    return "\n".join(lines)


def to_csv(validated: List[Dict]) -> str:
    # CSV header: proxy,ok,latency_ms
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["proxy", "ok", "latency_ms"])
    for r in validated:
        writer.writerow([r.get("proxy"), r.get("ok"), r.get("latency_ms")])
    return output.getvalue()
