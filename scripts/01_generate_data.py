# ============================================================
# SCRIPT: 01_generate_data.py
# PURPOSE: Generate realistic fake pharmacovigilance data
# WHY: We need data to work with. Real PV data is confidential,
#      so Faker lets us create realistic fake data safely.
# ============================================================

# Install Faker if not already installed

import pandas as pd          # Data manipulation
import random                 # Random selections
from faker import Faker       # Fake name/date generator
from datetime import datetime, timedelta
import os

# Initialize the Faker library with India locale (or 'en_US')
fake = Faker('en_IN')

# Set random seed so your data is reproducible (same data each run)
random.seed(42)
fake.seed_instance(42)

# ── DEFINE REFERENCE DATA ────────────────────────────────────

# Common drugs in pharmacovigilance databases
DRUGS = [
    "Paracetamol", "Ibuprofen", "Amoxicillin", "Metformin",
    "Atorvastatin", "Omeprazole", "Aspirin", "Lisinopril",
    "Amlodipine", "Ciprofloxacin", "Azithromycin", "Cetirizine",
    "Pantoprazole", "Losartan", "Glimepiride"
]

# Possible adverse events (side effects)
ADVERSE_EVENTS = [
    "Nausea", "Vomiting", "Headache", "Dizziness", "Rash",
    "Itching", "Diarrhea", "Constipation", "Fatigue",
    "Liver toxicity", "Kidney failure", "Anaphylaxis",
    "Stevens-Johnson Syndrome", "Cardiac arrhythmia",
    "Thrombocytopenia", "Abdominal pain", "Insomnia",
    "Edema", "Hypotension", "Fever"
]

# Severity levels (based on ICH E2A guidelines — real industry standard)
SEVERITY_LEVELS = ["Mild", "Moderate", "Severe", "Life-threatening", "Fatal"]

# Seriousness criteria (real regulatory terminology)
SERIOUSNESS = [
    "Non-serious",
    "Hospitalization",
    "Life-threatening",
    "Disability",
    "Congenital anomaly",
    "Death"
]

# Reporter types
REPORTER_TYPES = [
    "Physician", "Pharmacist", "Patient", "Nurse",
    "Other Healthcare Professional"
]

# Outcomes
OUTCOMES = [
    "Recovered", "Recovering", "Not recovered",
    "Recovered with sequelae", "Fatal", "Unknown"
]

# Countries
COUNTRIES = [
    "India", "USA", "UK", "Germany", "Japan",
    "Brazil", "Canada", "Australia", "France", "Italy"
]

# ── GENERATE ADVERSE EVENT REPORTS ───────────────────────────

def generate_ae_report(report_id):
    """
    Generate one realistic adverse event report.
    
    Each report mimics what a real PV database entry looks like.
    Fields follow ICH E2B(R3) standard — the global PV data standard.
    """
    
    # Random start date (last 3 years)
    start_date = datetime.now() - timedelta(days=random.randint(1, 1095))
    
    # Onset date: when the adverse event started
    onset_date = start_date - timedelta(days=random.randint(0, 30))
    
    # Time to onset: days from drug start to AE onset
    time_to_onset = random.randint(0, 60)
    
    # Randomly pick severity (weighted — mild AEs more common)
    severity = random.choices(
        SEVERITY_LEVELS,
        weights=[40, 30, 15, 10, 5],  # 40% mild, 30% moderate, etc.
        k=1
    )[0]
    
    # Serious AEs are more likely if severe
    if severity in ["Severe", "Life-threatening", "Fatal"]:
        seriousness = random.choice(SERIOUSNESS[1:])   # exclude Non-serious
    else:
        seriousness = random.choices(
            SERIOUSNESS,
            weights=[70, 10, 8, 5, 4, 3],
            k=1
        )[0]
    
    # Build the report dictionary
    report = {
        "report_id": f"PV-{report_id:05d}",        # e.g., PV-00001
        "report_date": start_date.strftime("%Y-%m-%d"),
        "drug_name": random.choice(DRUGS),
        "drug_batch": f"BATCH-{random.randint(1000, 9999)}",
        "dose_mg": random.choice([10, 25, 50, 100, 200, 250, 500, 1000]),
        "route": random.choice(["Oral", "IV", "IM", "Topical", "Inhalation"]),
        "patient_age": random.randint(18, 85),
        "patient_gender": random.choice(["Male", "Female", "Unknown"]),
        "patient_weight_kg": random.randint(45, 120),
        "adverse_event": random.choice(ADVERSE_EVENTS),
        "onset_date": onset_date.strftime("%Y-%m-%d"),
        "time_to_onset_days": time_to_onset,
        "severity": severity,
        "seriousness": seriousness,
        "outcome": random.choice(OUTCOMES),
        "reporter_type": random.choice(REPORTER_TYPES),
        "country": random.choice(COUNTRIES),
        "causality": random.choice(["Certain", "Probable", "Possible", "Unlikely", "Unassessable"]),
        "is_duplicate": random.choices([0, 1], weights=[90, 10], k=1)[0],  # 10% duplicates
        "narrative": f"Patient reported {random.choice(ADVERSE_EVENTS).lower()} after taking {random.choice(DRUGS)}.",
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    return report


# ── MAIN EXECUTION ────────────────────────────────────────────

if __name__ == "__main__":
    
    print("Generating pharmacovigilance adverse event reports...")
    
    # Generate 500 reports (good amount for portfolio demo)
    NUM_REPORTS = 500
    
    reports = []
    for i in range(1, NUM_REPORTS + 1):
        reports.append(generate_ae_report(i))
    
    # Convert to DataFrame (tabular format)
    df = pd.DataFrame(reports)
    
    # Save as CSV (raw data)
    output_path = "data/raw/ae_reports.csv"
    os.makedirs(os.path.dirname(output_path), exist_ok=True) # Create directory if it doesn't exist
    df.to_csv(output_path, index=False)
    
    print(f"✓ Generated {NUM_REPORTS} adverse event reports")
    print(f"✓ Saved to: {output_path}")
    print(f"\nData preview:")
    print(df.head(3).to_string())
    print(f"\nColumns: {list(df.columns)}")
    print(f"Shape: {df.shape}")