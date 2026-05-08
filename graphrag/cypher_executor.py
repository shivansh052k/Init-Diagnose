import os
import time
from typing import Any
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()


class CypherExecutor:
    def __init__(self):
        self.driver = GraphDatabase.driver(
            os.getenv("NEO4J_URI"),
            auth=(os.getenv("NEO4J_USER"), os.getenv("NEO4J_PASSWORD")),
        )

    def close(self):
        self.driver.close()

    def execute(self, cypher: str, params: dict = {}) -> dict:
        t0 = time.time()
        try:
            with self.driver.session() as session:
                result = session.run(cypher, **params)
                records = [dict(r) for r in result]
            latency_ms = (time.time() - t0) * 1000
            return {
                "success": True,
                "records": records,
                "count": len(records),
                "latency_ms": round(latency_ms, 2),
                "error": None,
            }
        except Exception as e:
            latency_ms = (time.time() - t0) * 1000
            return {
                "success": False,
                "records": [],
                "count": 0,
                "latency_ms": round(latency_ms, 2),
                "error": str(e),
            }

    def execute_safe(self, cypher: str, fallback_cypher: str = None) -> dict:
        result = self.execute(cypher)
        if not result["success"] and fallback_cypher:
            result = self.execute(fallback_cypher)
            result["used_fallback"] = True
        return result


if __name__ == "__main__":
    executor = CypherExecutor()

    tests = [
        "MATCH (p:Patient)-[:HAS_DIAGNOSIS]->(d:Diagnosis) RETURN p.patient_id, p.age, d.name LIMIT 5",
        "MATCH (d:Diagnosis)-[:TREATED_BY]->(m:Medication) RETURN d.name, m.name LIMIT 5",
        "MATCH (p:Patient)-[:HAS_ASSESSMENT]->(a:Assessment {type: 'PHQ-9'}) WHERE a.score >= 15 RETURN p.patient_id, a.score LIMIT 5",
    ]

    print("── CypherExecutor Test ─────────────────────────────")
    for cypher in tests:
        result = executor.execute(cypher)
        print(f"\nCypher: {cypher[:70]}...")
        print(f"  Success:  {result['success']}")
        print(f"  Records:  {result['count']}")
        print(f"  Latency:  {result['latency_ms']}ms")
        if result["records"]:
            print(f"  Sample:   {result['records'][0]}")

    executor.close()