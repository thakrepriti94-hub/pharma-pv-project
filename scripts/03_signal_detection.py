# ============================================================
# SCRIPT: 03_signal_detection.py
# PURPOSE: Automate PV signal detection using ROR method
# WHY: Signal detection is the #1 skill in PV jobs.
#      ROR (Reporting Odds Ratio) is the standard method
#      used by EMA, FDA, and WHO VigiBase.
# ============================================================

import sqlite3
import pandas as pd
import numpy as np
from scipy import stats
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')
import os

# ── CONNECT TO DATABASE ───────────────────────────────────────

conn = sqlite3.connect("database/pharmacovigilance.db")


# ── STEP 1: LOAD DATA ─────────────────────────────────────────

print("Loading data from database...")
df = pd.read_sql("SELECT * FROM ae_reports", conn)
print(f"✓ Loaded {len(df)} reports")


# ── STEP 2: DUPLICATE FLAGGING ────────────────────────────────

def flag_duplicates(df):
    """
    Identify potential duplicate reports.
    
    Real PV logic: same drug + same AE + same patient age + same gender
    reported within 7 days = likely duplicate.
    
    WHY: Duplicates inflate signal counts. Removing them = cleaner analysis.
    """
    print("\nRunning duplicate detection...")
    
    # Create a composite key for potential duplicates
    df['dup_key'] = (
        df['drug_name'] + "_" +
        df['adverse_event'] + "_" +
        df['patient_age'].astype(str) + "_" +
        df['patient_gender']
    )
    
    # Count how many times each key appears
    dup_counts = df['dup_key'].value_counts()
    
    # Flag as duplicate if key appears more than once
    df['auto_flagged_duplicate'] = df['dup_key'].map(
        lambda x: 1 if dup_counts[x] > 1 else 0
    )
    
    dups = df['auto_flagged_duplicate'].sum()
    print(f"✓ Flagged {dups} potential duplicates ({dups/len(df)*100:.1f}% of reports)")
    
    return df


# ── STEP 3: SERIOUSNESS FLAGGING ──────────────────────────────

def flag_serious_aes(df):
    """
    Auto-flag reports that require expedited reporting.
    
    ICH E2A Guidelines:
    - Serious AEs must be reported within 7 days (fatal/life-threatening)
    - Other serious within 15 days
    - Non-serious within 30 days
    
    WHY: Regulatory compliance — missing deadlines = massive fines.
    """
    print("\nFlagging serious adverse events...")
    
    # Define serious conditions
    serious_conditions = [
        "Hospitalization", "Life-threatening", 
        "Disability", "Congenital anomaly", "Death"
    ]
    
    serious_severity = ["Severe", "Life-threatening", "Fatal"]
    
    # Create flags
    df['requires_expedited_report'] = (
        df['seriousness'].isin(serious_conditions) |
        df['severity'].isin(serious_severity)
    ).astype(int)
    
    df['reporting_deadline_days'] = df.apply(
        lambda row: 7 if row['seriousness'] in ['Life-threatening', 'Death', 'Fatal']
        else (15 if row['seriousness'] in serious_conditions else 30),
        axis=1
    )
    
    expedited = df['requires_expedited_report'].sum()
    print(f"✓ {expedited} reports flagged for expedited reporting")
    print(f"  - 7-day reports: {len(df[df['reporting_deadline_days'] == 7])}")
    print(f"  - 15-day reports: {len(df[df['reporting_deadline_days'] == 15])}")
    print(f"  - 30-day reports: {len(df[df['reporting_deadline_days'] == 30])}")
    
    return df


# ── STEP 4: SIGNAL DETECTION (ROR METHOD) ────────────────────

def calculate_ror(df):
    """
    Calculate Reporting Odds Ratio (ROR) for each drug-AE pair.
    
    FORMULA:
    ROR = (a/b) / (c/d)
    Where:
        a = reports of Drug X causing AE Y
        b = reports of Drug X NOT causing AE Y  
        c = reports of OTHER drugs causing AE Y
        d = reports of OTHER drugs NOT causing AE Y
    
    INTERPRETATION:
    ROR > 1: Drug X associated with AE Y more than other drugs
    ROR > 2 with CI lower bound > 1 = SIGNAL
    
    WHY: This is the WHO/EMA standard signal detection method.
         Knowing this makes you stand out in PV interviews.
    """
    print("\nRunning signal detection (ROR method)...")
    
    total_reports = len(df)
    
    # Get all unique drug-AE combinations
    drug_ae_pairs = df.groupby(['drug_name', 'adverse_event']).size().reset_index(name='a')
    
    signals = []
    
    for _, row in drug_ae_pairs.iterrows():
        drug = row['drug_name']
        ae   = row['adverse_event']
        a    = row['a']   # This drug, this AE
        
        # b = This drug, other AEs
        b = len(df[(df['drug_name'] == drug) & (df['adverse_event'] != ae)])
        
        # c = Other drugs, this AE
        c = len(df[(df['drug_name'] != drug) & (df['adverse_event'] == ae)])
        
        # d = Other drugs, other AEs
        d = len(df[(df['drug_name'] != drug) & (df['adverse_event'] != ae)])
        
        # Avoid division by zero
        if b == 0 or c == 0 or d == 0:
            continue
        
        # Calculate ROR
        ror = (a / b) / (c / d)
        
        # Calculate 95% Confidence Interval (log scale)
        log_ror = np.log(ror)
        se = np.sqrt(1/a + 1/b + 1/c + 1/d)   # Standard error
        ci_lower = np.exp(log_ror - 1.96 * se)
        ci_upper = np.exp(log_ror + 1.96 * se)
        
        # Determine signal strength
        if ci_lower > 2:
            strength = "Strong"
        elif ci_lower > 1:
            strength = "Moderate"
        elif ror > 1:
            strength = "Weak"
        else:
            strength = "No signal"
        
        signals.append({
            'drug_name': drug,
            'adverse_event': ae,
            'report_count': a,
            'ror_value': round(ror, 3),
            'ci_lower': round(ci_lower, 3),
            'ci_upper': round(ci_upper, 3),
            'signal_strength': strength,
            'detected_date': datetime.now().strftime("%Y-%m-%d"),
            'status': 'New'
        })
    
    signals_df = pd.DataFrame(signals)
    
    # Filter to only actual signals (ROR > 1 and CI lower > 1)
    actual_signals = signals_df[signals_df['ci_lower'] > 1].sort_values('ror_value', ascending=False)
    
    print(f"✓ Analyzed {len(drug_ae_pairs)} drug-AE combinations")
    print(f"✓ Detected {len(actual_signals)} potential signals")
    print(f"\nTop 5 Signals:")
    print(actual_signals.head(5)[['drug_name', 'adverse_event', 'report_count', 'ror_value', 'signal_strength']].to_string(index=False))
    
    return signals_df, actual_signals


# ── STEP 5: SAVE RESULTS ──────────────────────────────────────

def save_results(df, signals_df):
    """Save all processed data back to database and CSV."""
    
    print("\nSaving results...")
    
    # Ensure the output directory exists
    output_dir = "data/processed"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created directory: {output_dir}/")

    # Save processed reports
    df.to_sql("ae_reports_processed", conn, if_exists="replace", index=False)
    df.to_csv(os.path.join(output_dir, "ae_reports_processed.csv"), index=False)
    
    # Save signals
    signals_df.to_sql("signals", conn, if_exists="replace", index=False)
    signals_df.to_csv(os.path.join(output_dir, "signals.csv"), index=False)
    
    print("✓ Processed data saved to database")
    print("✓ CSV exports saved to data/processed/")


# ── MAIN ──────────────────────────────────────────────────────

if __name__ == "__main__":
    
    print("="*60)
    print("PHARMACOVIGILANCE SIGNAL DETECTION ENGINE")
    print("="*60)
    
    # Run all automation steps
    df = flag_duplicates(df)
    df = flag_serious_aes(df)
    signals_df, actual_signals = calculate_ror(df)
    save_results(df, signals_df)
    
    conn.close()
    
    print("\n" + "="*60)
    print("✓ Signal detection complete!")
    print("✓ Check data/processed/ for outputs")
    print("="*60)