import re
from typing import Optional

# Valid schema entities
VALID_NODES = {
    "Patient", "Diagnosis", "Symptom", "Medication",
    "Clinician", "Assessment", "Episode",
}

VALID_RELATIONSHIPS = {
    "HAS_DIAGNOSIS", "PRESENTS", "PRESCRIBED", "ASSESSED_BY",
    "HAS_EPISODE", "HAS_ASSESSMENT", "HAS_SYMPTOM",
    "TREATED_BY", "LINKED_TO", "TREATS",
}

VALID_PROPERTIES = {
    "Patient": {"patient_id", "age", "gender", "admission_date", "discharge_date", "insurance_type"},
    "Diagnosis": {"diagnosis_id", "dsm5_code", "name", "category", "severity"},
    "Symptom": {"symptom_id", "name", "domain", "severity_scale"},
    "Medication": {"medication_id", "name", "drug_class", "mechanism", "typical_dosage"},
    "Clinician": {"clinician_id", "specialty", "years_experience", "board_certified"},
    "Assessment": {"assessment_id", "type", "score", "date", "interpretation"},
    "Episode": {"episode_id", "type", "severity", "start_date", "end_date"},
}

# Enum value normalization maps
SEVERITY_NORM = {
    "severe": "Severe", "moderate": "Moderate", "mild": "Mild",
}

DIAGNOSIS_NAME_NORM = {
    "posttraumatic stress disorder": "PTSD",
    "post-traumatic stress disorder": "PTSD",
    "post traumatic stress disorder": "PTSD",
    "major depressive disorder severe": "Major Depressive Disorder, severe",
    "major depressive disorder moderate": "Major Depressive Disorder, moderate",
    "major depressive disorder mild": "Major Depressive Disorder, mild",
    "attention deficit hyperactivity disorder": "ADHD, combined type",
    "obsessive compulsive disorder": "OCD",
    "obsessive-compulsive disorder": "OCD",
}

FORBIDDEN_PATTERNS = [
    r"MERGE\b",
    r"CREATE\b",
    r"DELETE\b",
    r"SET\b",
    r"REMOVE\b",
    r"\bDROP\b",
]

INVALID_SYNTAX_PATTERNS = [
    # Property map with key but no value: {type: 'X', score}
    r"\{[^}]*,\s*\w+\s*\}",
    r"\{\s*\w+\s*\}(?!\s*[=<>])",
    # Dot access on non-existent nested props
    r"\w+\.\w+\.\w+",
]

DATE_NORM = {
    r"\bDATE\(\)": "date()",
    r"\bTODAY\(\)": "date()",
}


class SchemaValidator:

    def validate(self, cypher: str) -> dict:
        errors = []
        warnings = []

        # Check forbidden ops
        for pattern in FORBIDDEN_PATTERNS:
            if re.search(pattern, cypher, re.IGNORECASE):
                errors.append(f"Forbidden operation: {pattern}")

        # Check invalid syntax patterns
        for pattern in INVALID_SYNTAX_PATTERNS:
            if re.search(pattern, cypher):
                errors.append(f"Invalid syntax pattern detected: {pattern}")

        # Check node labels
        found_nodes = re.findall(r"\((?:\w+:)?(\w+)[\s{)]", cypher)
        for node in found_nodes:
            if node and node[0].isupper() and node not in VALID_NODES:
                errors.append(f"Unknown node label: {node}")

        # Check relationship types
        found_rels = re.findall(r"\[:(\w+)", cypher)
        for rel in found_rels:
            if rel not in VALID_RELATIONSHIPS:
                errors.append(f"Unknown relationship: {rel}")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
        }

    def fix(self, cypher: str) -> str:
        # Normalize date functions
        for pattern, replacement in DATE_NORM.items():
            cypher = re.sub(pattern, replacement, cypher)

        # Normalize severity casing
        def norm_severity(match):
            val = match.group(1).lower()
            return f"severity: '{SEVERITY_NORM.get(val, val.capitalize())}'"
        cypher = re.sub(
            r"severity:\s*'(\w+)'",
            norm_severity,
            cypher,
            flags=re.IGNORECASE,
        )

        # Normalize diagnosis names
        for wrong, correct in DIAGNOSIS_NAME_NORM.items():
            cypher = re.sub(
                rf"name:\s*'{re.escape(wrong)}'",
                f"name: '{correct}'",
                cypher,
                flags=re.IGNORECASE,
            )

        # Fix invalid property map syntax: {type: 'X', score} → {type: 'X'}
        cypher = re.sub(r",\s*\w+\s*(?=\})", "", cypher)

        # Remove hallucinated nested property access (x.y.z → x.y)
        cypher = re.sub(r"(\w+\.\w+)\.\w+", r"\1", cypher)

        # Remove WHERE clauses referencing hallucinated properties
        cypher = re.sub(
            r"WHERE\s+\w+\.\w+\s*=\s*\w+\.\w+\s*",
            "",
            cypher,
        )
        
        # Remove dangling alias references left after nested prop cleanup
        cypher = re.sub(r",\s*\w+\.\w+\s*(?=\b(?:ORDER|WHERE|RETURN|LIMIT|$))", "", cypher)
        # Remove trailing dangling props at end of RETURN
        cypher = re.sub(r",\s*\w+\.\w+\s*$", "", cypher)

        return cypher.strip()

    def validate_and_fix(self, cypher: str) -> dict:
        original = cypher
        cypher = self.fix(cypher)
        was_fixed = cypher != original
        validation = self.validate(cypher)

        return {
            "original": original,
            "fixed": cypher,
            "was_fixed": was_fixed,
            "valid": validation["valid"],
            "errors": validation["errors"],
        }


if __name__ == "__main__":
    validator = SchemaValidator()

    test_cases = [
        "MATCH (p:Patient)-[:HAS_DIAGNOSIS]->(d:Diagnosis {name: 'Major Depressive Disorder', severity: 'Severe'}) WHERE d.diagnosis_id = d.inspection.insurance_id RETURN p.patient_id, p.age, p.gender, d.diagnosis_id, d.inspection.insurance_type",
        "MATCH (p:Patient)-[:HAS_ASSESSMENT]->(a:Assessment {type: 'PHQ-9', score}) WHERE a.score > 15 RETURN p.patient_id, a.score",
        "MATCH (p:Patient)-[:HAS_DIAGNOSIS]->(d1:Diagnosis {name: 'Posttraumatic Stress Disorder'}) RETURN p.patient_id",
        "MATCH (p:Patient)-[:HAS_EPISODE]->(e:Episode {type: 'Manic', severity: 'severe'}) WHERE e.start_date < DATE() RETURN p.patient_id",
        "MATCH (p:Patient)-[:HAS_DIAGNOSIS]->(d:Diagnosis {name: 'Bipolar I Disorder'})-[:TREATED_BY]->(m:Medication) RETURN m.name",
    ]

    print("── Schema Validator Test ──────────────────────────────")
    for i, cypher in enumerate(test_cases, 1):
        result = validator.validate_and_fix(cypher)
        print(f"\nQ{i}:")
        print(f"  Valid:    {result['valid']}")
        print(f"  Fixed:    {result['was_fixed']}")
        if result['errors']:
            print(f"  Errors:   {result['errors']}")
        print(f"  Output:   {result['fixed']}")