from typing import Any


class ContextAssembler:

    def assemble(self, question: str, cypher: str, records: list[dict]) -> str:
        if not records:
            return (
                f"Clinical query: {question}\n"
                f"Graph query returned no results.\n"
                f"This may indicate no matching patients or entities in the knowledge graph."
            )

        context_parts = [
            f"Clinical query: {question}",
            f"Knowledge graph retrieved {len(records)} result(s):",
        ]

        # Detect result type from keys
        keys = set(records[0].keys()) if records else set()

        if self._is_patient_result(keys):
            context_parts.append(self._format_patients(records))
        elif self._is_medication_result(keys):
            context_parts.append(self._format_medications(records))
        elif self._is_symptom_result(keys):
            context_parts.append(self._format_symptoms(records))
        elif self._is_aggregate_result(keys):
            context_parts.append(self._format_aggregates(records))
        else:
            context_parts.append(self._format_generic(records))

        return "\n".join(context_parts)

    def _is_patient_result(self, keys: set) -> bool:
        return any("patient_id" in k or "age" in k or "gender" in k for k in keys)

    def _is_medication_result(self, keys: set) -> bool:
        return any("drug_class" in k or "mechanism" in k or "dosage" in k for k in keys)

    def _is_symptom_result(self, keys: set) -> bool:
        return any("domain" in k or "severity_scale" in k for k in keys)

    def _is_aggregate_result(self, keys: set) -> bool:
        return any("count" in k.lower() or "avg" in k.lower() for k in keys)

    def _format_patients(self, records: list[dict]) -> str:
        lines = []
        for r in records[:20]:
            parts = []
            for k, v in r.items():
                if v is not None:
                    parts.append(f"{k.split('.')[-1]}={v}")
            lines.append("  Patient: " + ", ".join(parts))
        if len(records) > 20:
            lines.append(f"  ... and {len(records) - 20} more patients")
        return "\n".join(lines)

    def _format_medications(self, records: list[dict]) -> str:
        lines = []
        for r in records:
            parts = []
            for k, v in r.items():
                if v is not None:
                    parts.append(f"{k.split('.')[-1]}={v}")
            lines.append("  Medication: " + ", ".join(parts))
        return "\n".join(lines)

    def _format_symptoms(self, records: list[dict]) -> str:
        lines = []
        for r in records:
            parts = []
            for k, v in r.items():
                if v is not None:
                    parts.append(f"{k.split('.')[-1]}={v}")
            lines.append("  Symptom: " + ", ".join(parts))
        return "\n".join(lines)

    def _format_aggregates(self, records: list[dict]) -> str:
        lines = []
        for r in records:
            parts = [f"{k.split('.')[-1]}={v}" for k, v in r.items() if v is not None]
            lines.append("  " + ", ".join(parts))
        return "\n".join(lines)

    def _format_generic(self, records: list[dict]) -> str:
        lines = []
        for r in records[:10]:
            parts = [f"{k.split('.')[-1]}={v}" for k, v in r.items() if v is not None]
            lines.append("  " + ", ".join(parts))
        return "\n".join(lines)


if __name__ == "__main__":
    assembler = ContextAssembler()

    test_records = [
        {"p.patient_id": "abc-123", "p.age": 34, "p.gender": "Female"},
        {"p.patient_id": "def-456", "p.age": 52, "p.gender": "Male"},
    ]

    context = assembler.assemble(
        "Find patients with Major Depressive Disorder, severe",
        "MATCH (p:Patient)-[:HAS_DIAGNOSIS]->(d:Diagnosis {name: 'Major Depressive Disorder, severe'}) RETURN p.patient_id, p.age, p.gender",
        test_records,
    )
    print(context)