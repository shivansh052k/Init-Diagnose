import uuid
import random
from faker import Faker
from datetime import datetime, timedelta
from kg.schema.ontology import (
    Patient, Diagnosis, Symptom, Medication, Clinician, Assessment, Episode
)

fake = Faker()
random.seed(42)
Faker.seed(42)

# ── Domain data ────────────────────────────────────────────────────────────────

DSM5_DIAGNOSES = [
    ("F32.0", "Major Depressive Disorder, mild", "Mood Disorders"),
    ("F32.1", "Major Depressive Disorder, moderate", "Mood Disorders"),
    ("F32.2", "Major Depressive Disorder, severe", "Mood Disorders"),
    ("F33.0", "Recurrent Depressive Disorder, mild", "Mood Disorders"),
    ("F41.0", "Panic Disorder", "Anxiety Disorders"),
    ("F41.1", "Generalized Anxiety Disorder", "Anxiety Disorders"),
    ("F40.10", "Social Anxiety Disorder", "Anxiety Disorders"),
    ("F42.2", "OCD", "Obsessive-Compulsive Disorders"),
    ("F43.10", "PTSD", "Trauma Disorders"),
    ("F43.20", "Adjustment Disorder", "Trauma Disorders"),
    ("F20.9", "Schizophrenia", "Psychotic Disorders"),
    ("F25.0", "Schizoaffective Disorder", "Psychotic Disorders"),
    ("F31.0", "Bipolar I Disorder", "Bipolar Disorders"),
    ("F31.81", "Bipolar II Disorder", "Bipolar Disorders"),
    ("F90.0", "ADHD, inattentive type", "Neurodevelopmental"),
    ("F90.2", "ADHD, combined type", "Neurodevelopmental"),
    ("F84.0", "Autism Spectrum Disorder", "Neurodevelopmental"),
    ("F50.01", "Anorexia Nervosa", "Eating Disorders"),
    ("F50.2", "Bulimia Nervosa", "Eating Disorders"),
    ("F10.20", "Alcohol Use Disorder", "Substance Disorders"),
    ("F12.20", "Cannabis Use Disorder", "Substance Disorders"),
    ("F60.3", "Borderline Personality Disorder", "Personality Disorders"),
    ("F60.0", "Paranoid Personality Disorder", "Personality Disorders"),
]

SYMPTOMS = [
    ("Depressed mood", "Affective", "0-10"),
    ("Anhedonia", "Affective", "0-10"),
    ("Insomnia", "Sleep", "0-10"),
    ("Hypersomnia", "Sleep", "0-10"),
    ("Fatigue", "Somatic", "0-10"),
    ("Psychomotor agitation", "Behavioral", "0-10"),
    ("Psychomotor retardation", "Behavioral", "0-10"),
    ("Poor concentration", "Cognitive", "0-10"),
    ("Suicidal ideation", "Affective", "0-10"),
    ("Hallucinations", "Psychotic", "0-10"),
    ("Delusions", "Psychotic", "0-10"),
    ("Paranoia", "Psychotic", "0-10"),
    ("Flat affect", "Affective", "0-10"),
    ("Racing thoughts", "Cognitive", "0-10"),
    ("Grandiosity", "Cognitive", "0-10"),
    ("Impulsivity", "Behavioral", "0-10"),
    ("Panic attacks", "Anxiety", "0-10"),
    ("Avoidance behavior", "Behavioral", "0-10"),
    ("Intrusive thoughts", "Cognitive", "0-10"),
    ("Hypervigilance", "Anxiety", "0-10"),
    ("Flashbacks", "Cognitive", "0-10"),
    ("Dissociation", "Cognitive", "0-10"),
    ("Appetite loss", "Somatic", "0-10"),
    ("Weight loss", "Somatic", "0-10"),
    ("Irritability", "Affective", "0-10"),
    ("Social withdrawal", "Behavioral", "0-10"),
    ("Poor insight", "Cognitive", "0-10"),
    ("Compulsions", "Behavioral", "0-10"),
    ("Obsessions", "Cognitive", "0-10"),
    ("Emotional dysregulation", "Affective", "0-10"),
]

MEDICATIONS = [
    ("Sertraline", "SSRI", "Serotonin reuptake inhibition", "50-200mg/day"),
    ("Fluoxetine", "SSRI", "Serotonin reuptake inhibition", "20-80mg/day"),
    ("Escitalopram", "SSRI", "Serotonin reuptake inhibition", "10-20mg/day"),
    ("Venlafaxine", "SNRI", "Serotonin-norepinephrine reuptake inhibition", "75-225mg/day"),
    ("Duloxetine", "SNRI", "Serotonin-norepinephrine reuptake inhibition", "60-120mg/day"),
    ("Bupropion", "NDRI", "Dopamine-norepinephrine reuptake inhibition", "150-450mg/day"),
    ("Mirtazapine", "NaSSA", "Alpha-2 antagonism", "15-45mg/day"),
    ("Lithium", "Mood Stabilizer", "Multiple ion channel modulation", "600-1800mg/day"),
    ("Valproate", "Mood Stabilizer", "GABA enhancement", "500-2000mg/day"),
    ("Lamotrigine", "Mood Stabilizer", "Sodium channel blockade", "100-400mg/day"),
    ("Quetiapine", "Atypical Antipsychotic", "D2/5-HT2A antagonism", "50-800mg/day"),
    ("Risperidone", "Atypical Antipsychotic", "D2/5-HT2A antagonism", "2-8mg/day"),
    ("Aripiprazole", "Atypical Antipsychotic", "D2 partial agonism", "10-30mg/day"),
    ("Olanzapine", "Atypical Antipsychotic", "D2/5-HT2A antagonism", "5-20mg/day"),
    ("Clonazepam", "Benzodiazepine", "GABA-A potentiation", "0.5-4mg/day"),
    ("Lorazepam", "Benzodiazepine", "GABA-A potentiation", "1-4mg/day"),
    ("Methylphenidate", "Stimulant", "Dopamine-norepinephrine reuptake inhibition", "10-60mg/day"),
    ("Amphetamine", "Stimulant", "Monoamine release + reuptake inhibition", "5-40mg/day"),
    ("Buspirone", "Azapirone", "5-HT1A partial agonism", "15-60mg/day"),
    ("Naltrexone", "Opioid Antagonist", "Mu-opioid receptor blockade", "50-100mg/day"),
]

ASSESSMENT_TYPES = [
    ("PHQ-9", 0, 27),
    ("GAF", 1, 100),
    ("HAM-A", 0, 56),
    ("MADRS", 0, 60),
    ("PANSS", 30, 210),
    ("AUDIT", 0, 40),
    ("PCL-5", 0, 80),
    ("YMRS", 0, 60),
]

SPECIALTIES = [
    "General Psychiatry", "Child Psychiatry", "Geriatric Psychiatry",
    "Forensic Psychiatry", "Addiction Psychiatry", "Neuropsychiatry",
]

EPISODE_TYPES = [
    "Manic", "Depressive", "Mixed", "Psychotic", "Hypomanic", "Anxious"
]

SEVERITIES = ["Mild", "Moderate", "Severe"]


# ── Generators ─────────────────────────────────────────────────────────────────

def generate_patients(n: int = 30000) -> list[dict]:
    patients = []
    for _ in range(n):
        admission = fake.date_between(start_date="-5y", end_date="-1m")
        discharged = random.random() > 0.3
        discharge = (
            admission + timedelta(days=random.randint(3, 90))
            if discharged else None
        )
        patients.append(vars(Patient(
            patient_id=str(uuid.uuid4()),
            age=random.randint(18, 85),
            gender=random.choice(["Male", "Female", "Non-binary"]),
            admission_date=str(admission),
            discharge_date=str(discharge) if discharge else None,
            insurance_type=random.choice(["Private", "Medicare", "Medicaid", "Uninsured"]),
        )))
    return patients


def generate_diagnoses() -> list[dict]:
    diagnoses = []
    for dsm5_code, name, category in DSM5_DIAGNOSES:
        diagnoses.append(vars(Diagnosis(
            diagnosis_id=str(uuid.uuid4()),
            dsm5_code=dsm5_code,
            name=name,
            category=category,
            severity=random.choice(SEVERITIES),
        )))
    return diagnoses


def generate_symptoms() -> list[dict]:
    symptoms = []
    for name, domain, scale in SYMPTOMS:
        symptoms.append(vars(Symptom(
            symptom_id=str(uuid.uuid4()),
            name=name,
            domain=domain,
            severity_scale=scale,
        )))
    return symptoms


def generate_medications() -> list[dict]:
    medications = []
    for name, drug_class, mechanism, dosage in MEDICATIONS:
        medications.append(vars(Medication(
            medication_id=str(uuid.uuid4()),
            name=name,
            drug_class=drug_class,
            mechanism=mechanism,
            typical_dosage=dosage,
        )))
    return medications


def generate_clinicians(n: int = 500) -> list[dict]:
    clinicians = []
    for _ in range(n):
        clinicians.append(vars(Clinician(
            clinician_id=str(uuid.uuid4()),
            specialty=random.choice(SPECIALTIES),
            years_experience=random.randint(1, 35),
            board_certified=random.random() > 0.2,
        )))
    return clinicians


def generate_assessments(n: int = 50000) -> list[dict]:
    assessments = []
    for _ in range(n):
        atype, low, high = random.choice(ASSESSMENT_TYPES)
        score = round(random.uniform(low, high), 1)
        if atype == "PHQ-9":
            interp = "Minimal" if score < 5 else "Mild" if score < 10 else "Moderate" if score < 15 else "Severe"
        elif atype == "GAF":
            interp = "Severe" if score < 40 else "Moderate" if score < 60 else "Mild" if score < 80 else "Good"
        else:
            interp = random.choice(["Low", "Moderate", "High"])
        assessments.append(vars(Assessment(
            assessment_id=str(uuid.uuid4()),
            type=atype,
            score=score,
            date=str(fake.date_between(start_date="-5y", end_date="today")),
            interpretation=interp,
        )))
    return assessments


def generate_episodes(n: int = 30000) -> list[dict]:
    episodes = []
    for _ in range(n):
        start = fake.date_between(start_date="-5y", end_date="-1m")
        ended = random.random() > 0.25
        end = start + timedelta(days=random.randint(7, 180)) if ended else None
        episodes.append(vars(Episode(
            episode_id=str(uuid.uuid4()),
            type=random.choice(EPISODE_TYPES),
            severity=random.choice(SEVERITIES),
            start_date=str(start),
            end_date=str(end) if end else None,
        )))
    return episodes