# Schema-constrained Cypher query templates for psychiatry KG

QUERY_TEMPLATES = [
    {
        "id": "q001",
        "description": "Find patients with specific diagnosis",
        "cypher": "MATCH (p:Patient)-[:HAS_DIAGNOSIS]->(d:Diagnosis {{name: '{diagnosis_name}'}}) RETURN p.patient_id, p.age, p.gender",
        "params": ["diagnosis_name"],
    },
    {
        "id": "q002",
        "description": "Find patients on specific medication",
        "cypher": "MATCH (p:Patient)-[:PRESCRIBED]->(m:Medication {{name: '{medication_name}'}}) RETURN p.patient_id, p.age, p.gender",
        "params": ["medication_name"],
    },
    {
        "id": "q003",
        "description": "Find medications for a diagnosis",
        "cypher": "MATCH (d:Diagnosis {{name: '{diagnosis_name}'}})-[:TREATED_BY]->(m:Medication) RETURN m.name, m.drug_class, m.mechanism",
        "params": ["diagnosis_name"],
    },
    {
        "id": "q004",
        "description": "Find symptoms of a diagnosis",
        "cypher": "MATCH (d:Diagnosis {{name: '{diagnosis_name}'}})-[:HAS_SYMPTOM]->(s:Symptom) RETURN s.name, s.domain, s.severity_scale",
        "params": ["diagnosis_name"],
    },
    {
        "id": "q005",
        "description": "Find patients with symptom above severity threshold",
        "cypher": "MATCH (p:Patient)-[r:PRESENTS]->(s:Symptom {{name: '{symptom_name}'}}) WHERE r.severity_score >= {threshold} RETURN p.patient_id, p.age, r.severity_score",
        "params": ["symptom_name", "threshold"],
    },
    {
        "id": "q006",
        "description": "Find clinician patients by specialty",
        "cypher": "MATCH (c:Clinician {{specialty: '{specialty}'}})-[:TREATS]->(p:Patient) RETURN p.patient_id, p.age, p.gender",
        "params": ["specialty"],
    },
    {
        "id": "q007",
        "description": "Find patients with PHQ9 score above threshold",
        "cypher": "MATCH (p:Patient)-[:HAS_ASSESSMENT]->(a:Assessment {{type: 'PHQ-9'}}) WHERE a.score >= {threshold} RETURN p.patient_id, a.score, a.interpretation",
        "params": ["threshold"],
    },
    {
        "id": "q008",
        "description": "Find patients with active prescription",
        "cypher": "MATCH (p:Patient)-[r:PRESCRIBED]->(m:Medication) WHERE r.active = true RETURN p.patient_id, m.name, m.drug_class",
        "params": [],
    },
    {
        "id": "q009",
        "description": "Find patients with severe episode type",
        "cypher": "MATCH (p:Patient)-[:HAS_EPISODE]->(e:Episode {{type: '{episode_type}', severity: 'Severe'}}) RETURN p.patient_id, e.start_date, e.end_date",
        "params": ["episode_type"],
    },
    {
        "id": "q010",
        "description": "Count patients per diagnosis category",
        "cypher": "MATCH (p:Patient)-[:HAS_DIAGNOSIS]->(d:Diagnosis) RETURN d.category, count(p) AS patient_count ORDER BY patient_count DESC",
        "params": [],
    },
    {
        "id": "q011",
        "description": "Find patients with comorbid diagnoses",
        "cypher": "MATCH (p:Patient)-[:HAS_DIAGNOSIS]->(d1:Diagnosis {{name: '{diagnosis_1}'}}), (p)-[:HAS_DIAGNOSIS]->(d2:Diagnosis {{name: '{diagnosis_2}'}}) RETURN p.patient_id, p.age",
        "params": ["diagnosis_1", "diagnosis_2"],
    },
    {
        "id": "q012",
        "description": "Find patients by age range with diagnosis",
        "cypher": "MATCH (p:Patient)-[:HAS_DIAGNOSIS]->(d:Diagnosis {{name: '{diagnosis_name}'}}) WHERE p.age >= {min_age} AND p.age <= {max_age} RETURN p.patient_id, p.age, p.gender",
        "params": ["diagnosis_name", "min_age", "max_age"],
    },
    {
        "id": "q013",
        "description": "Find all assessments for patient",
        "cypher": "MATCH (p:Patient {{patient_id: '{patient_id}'}})-[:HAS_ASSESSMENT]->(a:Assessment) RETURN a.type, a.score, a.date, a.interpretation ORDER BY a.date",
        "params": ["patient_id"],
    },
    {
        "id": "q014",
        "description": "Find patients with specific insurance and diagnosis",
        "cypher": "MATCH (p:Patient {{insurance_type: '{insurance_type}'}})-[:HAS_DIAGNOSIS]->(d:Diagnosis {{category: '{category}'}}) RETURN p.patient_id, p.age, d.name",
        "params": ["insurance_type", "category"],
    },
    {
        "id": "q015",
        "description": "Find drugs of a specific class",
        "cypher": "MATCH (m:Medication {{drug_class: '{drug_class}'}}) RETURN m.name, m.mechanism, m.typical_dosage",
        "params": ["drug_class"],
    },
    {
        "id": "q016",
        "description": "Find patients with anxiety domain symptoms",
        "cypher": "MATCH (p:Patient)-[r:PRESENTS]->(s:Symptom {{domain: '{domain}'}}) RETURN p.patient_id, s.name, r.severity_score ORDER BY r.severity_score DESC",
        "params": ["domain"],
    },
    {
        "id": "q017",
        "description": "Find average PHQ9 score by diagnosis",
        "cypher": "MATCH (p:Patient)-[:HAS_DIAGNOSIS]->(d:Diagnosis), (p)-[:HAS_ASSESSMENT]->(a:Assessment {{type: 'PHQ-9'}}) RETURN d.name, avg(a.score) AS avg_phq9 ORDER BY avg_phq9 DESC",
        "params": [],
    },
    {
        "id": "q018",
        "description": "Find patients with primary diagnosis",
        "cypher": "MATCH (p:Patient)-[r:HAS_DIAGNOSIS {{is_primary: true}}]->(d:Diagnosis {{name: '{diagnosis_name}'}}) RETURN p.patient_id, p.age, p.gender",
        "params": ["diagnosis_name"],
    },
    {
        "id": "q019",
        "description": "Find board certified clinicians by specialty",
        "cypher": "MATCH (c:Clinician {{specialty: '{specialty}', board_certified: true}}) RETURN c.clinician_id, c.years_experience ORDER BY c.years_experience DESC",
        "params": ["specialty"],
    },
    {
        "id": "q020",
        "description": "Find patients with both symptom and diagnosis",
        "cypher": "MATCH (p:Patient)-[:HAS_DIAGNOSIS]->(d:Diagnosis {{name: '{diagnosis_name}'}}), (p)-[:PRESENTS]->(s:Symptom {{name: '{symptom_name}'}}) RETURN p.patient_id, p.age",
        "params": ["diagnosis_name", "symptom_name"],
    },
]