import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()


def verify():
    driver = GraphDatabase.driver(
        os.getenv("NEO4J_URI"),
        auth=(os.getenv("NEO4J_USER"), os.getenv("NEO4J_PASSWORD")),
    )

    node_labels = [
        "Patient", "Diagnosis", "Symptom", "Medication",
        "Clinician", "Assessment", "Episode",
    ]

    rel_types = [
        "HAS_DIAGNOSIS", "PRESENTS", "PRESCRIBED", "ASSESSED_BY",
        "HAS_EPISODE", "HAS_ASSESSMENT", "HAS_SYMPTOM",
        "TREATED_BY", "LINKED_TO", "TREATS",
    ]

    total_nodes = 0
    total_rels = 0

    with driver.session() as s:
        print("── Nodes ──────────────────────────")
        for label in node_labels:
            count = s.run(f"MATCH (n:{label}) RETURN count(n) AS c").single()["c"]
            print(f"  {label:<15} {count:>8,}")
            total_nodes += count

        print(f"  {'TOTAL':<15} {total_nodes:>8,}")

        print("\n── Relationships ──────────────────")
        for rel in rel_types:
            count = s.run(f"MATCH ()-[r:{rel}]->() RETURN count(r) AS c").single()["c"]
            print(f"  {rel:<20} {count:>8,}")
            total_rels += count

        print(f"  {'TOTAL':<20} {total_rels:>8,}")

    driver.close()


if __name__ == "__main__":
    verify()