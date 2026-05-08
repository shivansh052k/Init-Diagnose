from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Patient:
    patient_id: str
    age: int
    gender: str
    admission_date: str
    discharge_date: Optional[str]
    insurance_type: str


@dataclass
class Diagnosis:
    diagnosis_id: str
    dsm5_code: str
    name: str
    category: str
    severity: str


@dataclass
class Symptom:
    symptom_id: str
    name: str
    domain: str
    severity_scale: str


@dataclass
class Medication:
    medication_id: str
    name: str
    drug_class: str
    mechanism: str
    typical_dosage: str


@dataclass
class Clinician:
    clinician_id: str
    specialty: str
    years_experience: int
    board_certified: bool


@dataclass
class Assessment:
    assessment_id: str
    type: str
    score: float
    date: str
    interpretation: str


@dataclass
class Episode:
    episode_id: str
    type: str
    severity: str
    start_date: str
    end_date: Optional[str]