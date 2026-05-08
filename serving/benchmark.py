"""
Latency benchmark against local Triton HTTP endpoint.
Run AFTER triton_compose.yml is up.

Usage:
    python serving/benchmark.py --n 200 --url http://localhost:8000
"""
import argparse
import time
import json
import numpy as np

try:
    import requests
except ImportError:
    raise SystemExit("pip install requests")

FEATURE_DIM = 16
URL_TEMPLATE = "{base}/v2/models/risk_scorer/infer"


def make_payload(batch_size: int = 1) -> dict:
    features = np.random.rand(batch_size, FEATURE_DIM).astype(np.float32)
    return {
        "inputs": [
            {
                "name": "features",
                "shape": [batch_size, FEATURE_DIM],
                "datatype": "FP32",
                "data": features.flatten().tolist(),
            }
        ],
        "outputs": [{"name": "risk_score"}],
    }


def benchmark(base_url: str, n_requests: int, batch_size: int):
    url = URL_TEMPLATE.format(base=base_url)
    payload = make_payload(batch_size)
    headers = {"Content-Type": "application/json"}

    print(f"Warming up (10 requests)...")
    for _ in range(10):
        requests.post(url, data=json.dumps(payload), headers=headers)

    print(f"Benchmarking {n_requests} requests (batch_size={batch_size})...")
    latencies = []

    for i in range(n_requests):
        t0 = time.perf_counter()
        resp = requests.post(url, data=json.dumps(payload), headers=headers)
        t1 = time.perf_counter()

        if resp.status_code != 200:
            print(f"  [!] Request {i} failed: {resp.status_code} {resp.text[:100]}")
            continue

        latencies.append((t1 - t0) * 1000)

    latencies = np.array(latencies)
    print(f"\n── Results ({len(latencies)} successful) ──────────────────")
    print(f"  P50  : {np.percentile(latencies, 50):.2f} ms")
    print(f"  P95  : {np.percentile(latencies, 95):.2f} ms")
    print(f"  P99  : {np.percentile(latencies, 99):.2f} ms")
    print(f"  Mean : {latencies.mean():.2f} ms")
    print(f"  Min  : {latencies.min():.2f} ms")
    print(f"  Max  : {latencies.max():.2f} ms")
    print(f"  Throughput: {len(latencies) / latencies.sum() * 1000:.1f} req/s")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=200)
    parser.add_argument("--batch", type=int, default=1)
    parser.add_argument("--url", type=str, default="http://localhost:8000")
    args = parser.parse_args()
    benchmark(args.url, args.n, args.batch)