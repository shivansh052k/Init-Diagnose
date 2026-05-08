// Uniqueness constraints
CREATE CONSTRAINT patient_id IF NOT EXISTS FOR (p:Patient) REQUIRE p.patient_id IS UNIQUE;
CREATE CONSTRAINT diagnosis_id IF NOT EXISTS FOR (d:Diagnosis) REQUIRE d.diagnosis_id IS UNIQUE;
CREATE CONSTRAINT symptom_id IF NOT EXISTS FOR (s:Symptom) REQUIRE s.symptom_id IS UNIQUE;
CREATE CONSTRAINT medication_id IF NOT EXISTS FOR (m:Medication) REQUIRE m.medication_id IS UNIQUE;
CREATE CONSTRAINT clinician_id IF NOT EXISTS FOR (c:Clinician) REQUIRE c.clinician_id IS UNIQUE;
CREATE CONSTRAINT assessment_id IF NOT EXISTS FOR (a:Assessment) REQUIRE a.assessment_id IS UNIQUE;
CREATE CONSTRAINT episode_id IF NOT EXISTS FOR (e:Episode) REQUIRE e.episode_id IS UNIQUE;

// Indexes for frequent lookups
CREATE INDEX patient_age IF NOT EXISTS FOR (p:Patient) ON (p.age);
CREATE INDEX diagnosis_dsm5 IF NOT EXISTS FOR (d:Diagnosis) ON (d.dsm5_code);
CREATE INDEX diagnosis_category IF NOT EXISTS FOR (d:Diagnosis) ON (d.category);
CREATE INDEX symptom_domain IF NOT EXISTS FOR (s:Symptom) ON (s.domain);
CREATE INDEX medication_class IF NOT EXISTS FOR (m:Medication) ON (m.drug_class);
CREATE INDEX episode_type IF NOT EXISTS FOR (e:Episode) ON (e.type);
CREATE INDEX assessment_type IF NOT EXISTS FOR (a:Assessment) ON (a.type);