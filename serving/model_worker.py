"""
Persistent model worker process.
Reads JSON queries from stdin, writes JSON results to stdout.
Run standalone: python serving/model_worker.py
"""
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from nl2graph.inference.nl2cypher import NL2Cypher

model = NL2Cypher()
print("WORKER_READY", flush=True)

for line in sys.stdin:
    line = line.strip()
    if not line:
        continue
    try:
        req = json.loads(line)
        result = model.generate(req["question"])
        print(json.dumps({"ok": True, "cypher": result["cypher"], "valid": result["valid"]}), flush=True)
    except Exception as e:
        print(json.dumps({"ok": False, "error": str(e)}), flush=True)