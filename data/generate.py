import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from tqdm import tqdm
from kg.generators.node_generators import (
    generate_patients, generate_diagnoses, generate_symptoms,
    generate_medications, generate_clinicians, generate_assessments,
    generate_episodes,
)
from kg.generators.relationship_generators import generate_relationships

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "synthetic")


def save(name: str, data: list[dict]) -> None:
    path = os.path.join(OUTPUT_DIR, f"{name}.json")
    with open(path, "w") as f:
        json.dump(data, f)
    print(f"  saved {len(data):>6,} records → {path}")


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print("Generating nodes...")
    patients    = generate_patients(30000)
    diagnoses   = generate_diagnoses()
    symptoms    = generate_symptoms()
    medications = generate_medications()
    clinicians  = generate_clinicians(500)
    assessments = generate_assessments(50000)
    episodes    = generate_episodes(30000)

    for name, data in [
        ("patients",    patients),
        ("diagnoses",   diagnoses),
        ("symptoms",    symptoms),
        ("medications", medications),
        ("clinicians",  clinicians),
        ("assessments", assessments),
        ("episodes",    episodes),
    ]:
        save(name, data)

    total_nodes = sum([
        len(patients), len(diagnoses), len(symptoms), len(medications),
        len(clinicians), len(assessments), len(episodes),
    ])
    print(f"\nTotal nodes: {total_nodes:,}")

    print("\nGenerating relationships...")
    rels = generate_relationships(
        patients, diagnoses, symptoms, medications,
        clinicians, assessments, episodes,
    )

    for name, data in rels.items():
        save(f"rel_{name}", data)

    total_rels = sum(len(v) for v in rels.values())
    print(f"\nTotal relationships: {total_rels:,}")
    print("\nDone.")


if __name__ == "__main__":
    main()