import sys
import json
import subprocess
from pathlib import Path


class WorkerClient:
    """Runs NL2Cypher in a separate subprocess to avoid MPS+asyncio deadlock."""

    def __init__(self):
        worker_path = str(Path(__file__).parent.parent / "serving" / "model_worker.py")
        self.proc = subprocess.Popen(
            [sys.executable, worker_path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )
        # Block until worker signals ready
        while True:
            line = self.proc.stdout.readline().strip()
            if "WORKER_READY" in line:
                break
            if not line and self.proc.poll() is not None:
                err = self.proc.stderr.read()
                raise RuntimeError(f"Worker failed to start:\n{err}")

    def generate(self, question: str) -> dict:
        self.proc.stdin.write(json.dumps({"question": question}) + "\n")
        self.proc.stdin.flush()
        line = self.proc.stdout.readline()
        result = json.loads(line)
        if not result["ok"]:
            raise RuntimeError(result["error"])
        return {
            "cypher":           result["cypher"],
            "valid":            result["valid"],
            "cypher_was_fixed": False,
            "latency_ms":       0,
        }

    def close(self):
        try:
            self.proc.stdin.close()
            self.proc.wait(timeout=5)
        except Exception:
            self.proc.kill()