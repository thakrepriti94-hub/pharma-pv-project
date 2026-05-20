# ============================================================
# SCRIPT: 05_summary_stats.py
# PURPOSE: Export clean CSVs optimized for Power BI
# WHY: Power BI connects directly to CSV/Excel files.
#      We export pre-aggregated tables so Power BI visuals
#      load fast and are easy to build. 
# ============================================================

import sqlite3
import pandas as pd
from datetime import datetime
import os # Import the os module

# Ensure the export directory exists
export_dir = "data/exports"
if not os.path.exists(export_dir):
    os.makedirs(export_dir)
    print(f"Created directory: {export_dir}/")

conn = sqlite3.connect("database/pharmacovigilance.db")

# Export 1: Full processed reports (main fact table)
df_reports = pd.read_sql("""
    SELECT 
        report_id, report_date, drug_name, adverse_event,
        severity, seriousness, outcome, reporter_type,
        country, causality, patient_age, patient_gender,
        patient_weight_kg, time_to_onset_days,
        is_duplicate, requires_expedited_report,
        reporting_deadline_days
    FROM ae_reports_processed
""", conn)
df_reports.to_csv(f"{export_dir}/pbi_reports.csv", index=False)
print(f"✓ Reports table: {len(df_reports)} rows → pbi_reports.csv")

# Export 2: Monthly trend
df_monthly = pd.read_sql("""
    SELECT year_month, total_reports, serious_reports,
           fatal_reports, duplicate_reports
    FROM monthly_summary
    ORDER BY year_month
""", conn)
df_monthly.to_csv(f"{export_dir}/pbi_monthly.csv", index=False)
print(f"✓ Monthly summary: {len(df_monthly)} rows → pbi_monthly.csv")

# Export 3: Drug summary
df_drugs = pd.read_sql("""
    SELECT 
        drug_name,
        COUNT(*) as total_reports,
        SUM(CASE WHEN seriousness != 'Non-serious' THEN 1 ELSE 0 END) as serious_reports,
        SUM(CASE WHEN seriousness = 'Death' THEN 1 ELSE 0 END) as fatal_reports,
        AVG(patient_age) as avg_patient_age,
        AVG(time_to_onset_days) as avg_onset_days
    FROM ae_reports
    GROUP BY drug_name
    ORDER BY total_reports DESC
""", conn)
df_drugs['avg_patient_age'] = df_drugs['avg_patient_age'].round(1)
df_drugs['avg_onset_days']  = df_drugs['avg_onset_days'].round(1)
df_drugs.to_csv(f"{export_dir}/pbi_drugs.csv", index=False)
print(f"✓ Drug summary: {len(df_drugs)} rows → pbi_drugs.csv")

# Export 4: Signals
df_signals = pd.read_sql("""
    SELECT drug_name, adverse_event, report_count,
           ror_value, ci_lower, ci_upper, signal_strength
    FROM signals
    WHERE ci_lower > 1
    ORDER BY ror_value DESC
""", conn)
df_signals.to_csv(f"{export_dir}/pbi_signals.csv", index=False)
print(f"✓ Signals table: {len(df_signals)} rows → pbi_signals.csv")

# Export 5: Country heatmap data
df_country = pd.read_sql("""
    SELECT country, COUNT(*) as reports,
           AVG(CASE WHEN severity = 'Fatal' THEN 1 ELSE 0 END) * 100 as fatality_rate
    FROM ae_reports
    GROUP BY country
    ORDER BY reports DESC
""", conn)
df_country['fatality_rate'] = df_country['fatality_rate'].round(2)
df_country.to_csv(f"{export_dir}/pbi_countries.csv", index=False)
print(f"✓ Country data: {len(df_country)} rows → pbi_countries.csv")

conn.close()
print("\n✓ All Power BI exports ready in data/exports/")