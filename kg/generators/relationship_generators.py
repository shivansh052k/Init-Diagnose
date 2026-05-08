import random

random.seed(42)


def generate_relationships(
    patients: list[dict],
    diagnoses: list[dict],
    symptoms: list[dict],
    medications: list[dict],
    clinicians: list[dict],
    assessments: list[dict],
    episodes: list[dict],
) -> dict[str, list[dict]]:

    rels = {
        "HAS_DIAGNOSIS": [],
        "PRESENTS": [],
        "PRESCRIBED": [],
        "ASSESSED_BY": [],
        "HAS_EPISODE": [],
        "HAS_ASSESSMENT": [],
        "HAS_SYMPTOM": [],
        "TREATED_BY": [],
        "LINKED_TO": [],
        "TREATS": [],
    }

    assessment_pool = list(assessments)
    episode_pool = list(episodes)
    random.shuffle(assessment_pool)
    random.shuffle(episode_pool)

    assess_idx = 0
    episode_idx = 0

    for patient in patients:
        pid = patient["patient_id"]

        # Patient -[HAS_DIAGNOSIS]-> Diagnosis (1-3 per patient)
        patient_diagnoses = random.sample(diagnoses, k=random.randint(1, 3))
        for diag in patient_diagnoses:
            rels["HAS_DIAGNOSIS"].append({
                "patient_id": pid,
                "diagnosis_id": diag["diagnosis_id"],
                "date_diagnosed": patient["admission_date"],
                "is_primary": diag == patient_diagnoses[0],
            })

        # Patient -[PRESENTS]-> Symptom (2-6 per patient)
        for sym in random.sample(symptoms, k=random.randint(2, 6)):
            rels["PRESENTS"].append({
                "patient_id": pid,
                "symptom_id": sym["symptom_id"],
                "severity_score": random.randint(1, 10),
                "reported_date": patient["admission_date"],
            })

        # Patient -[PRESCRIBED]-> Medication (1-3 per patient)
        for med in random.sample(medications, k=random.randint(1, 3)):
            rels["PRESCRIBED"].append({
                "patient_id": pid,
                "medication_id": med["medication_id"],
                "dosage": med["typical_dosage"],
                "start_date": patient["admission_date"],
                "active": random.random() > 0.3,
            })

        # Patient -[ASSESSED_BY]-> Clinician (1-2 per patient)
        for clin in random.sample(clinicians, k=random.randint(1, 2)):
            rels["ASSESSED_BY"].append({
                "patient_id": pid,
                "clinician_id": clin["clinician_id"],
                "assessment_date": patient["admission_date"],
            })
            # Clinician -[TREATS]-> Patient (inverse)
            rels["TREATS"].append({
                "clinician_id": clin["clinician_id"],
                "patient_id": pid,
            })

        # Patient -[HAS_EPISODE]-> Episode (1-2 per patient)
        for _ in range(random.randint(1, 2)):
            if episode_idx < len(episode_pool):
                rels["HAS_EPISODE"].append({
                    "patient_id": pid,
                    "episode_id": episode_pool[episode_idx]["episode_id"],
                })
                episode_idx += 1
        
        # Patient -[HAS_ASSESSMENT]-> Assessment (1-3 per patient)
        for _ in range(random.randint(1, 3)):
            if assess_idx < len(assessment_pool):
                rels["HAS_ASSESSMENT"].append({
                    "patient_id": pid,
                    "assessment_id": assessment_pool[assess_idx]["assessment_id"],
                    "administered_by": random.choice(clinicians)["clinician_id"],
                })
                assess_idx += 1

    # Diagnosis -[HAS_SYMPTOM]-> Symptom (3-8 per diagnosis)
    for diag in diagnoses:
        for sym in random.sample(symptoms, k=random.randint(3, 8)):
            rels["HAS_SYMPTOM"].append({
                "diagnosis_id": diag["diagnosis_id"],
                "symptom_id": sym["symptom_id"],
                "frequency": random.choice(["Always", "Often", "Sometimes"]),
            })

    # Diagnosis -[TREATED_BY]-> Medication (1-4 per diagnosis)
    for diag in diagnoses:
        for med in random.sample(medications, k=random.randint(1, 4)):
            rels["TREATED_BY"].append({
                "diagnosis_id": diag["diagnosis_id"],
                "medication_id": med["medication_id"],
                "evidence_level": random.choice(["A", "B", "C"]),
            })

    # Episode -[LINKED_TO]-> Diagnosis
    for ep in episodes:
        diag = random.choice(diagnoses)
        rels["LINKED_TO"].append({
            "episode_id": ep["episode_id"],
            "diagnosis_id": diag["diagnosis_id"],
        })

    return rels