# ============================================================
# SCRIPT: 02_create_database.py
# PURPOSE: Create SQLite database and load data into it
# WHY: SQL databases are industry-standard for PV systems.
#      SQLite is perfect for portfolios — no server needed.
#      This shows employers you understand database design.
# ============================================================

import sqlite3    # Built into Python — no install needed!
import pandas as pd
import os

# ── DATABASE CONNECTION ───────────────────────────────────────

def get_connection():
    """
    Create/connect to SQLite database.
    If the .db file doesn't exist, SQLite creates it automatically.
    """
    # Ensure the directory exists
    db_dir = "database"
    if not os.path.exists(db_dir):
        os.makedirs(db_dir)
        print(f"Created directory: {db_dir}/")

    conn = sqlite3.connect(f"{db_dir}/pharmacovigilance.db")
    return conn


# ── CREATE TABLES ─────────────────────────────────────────────

def create_tables(conn):
    """
    Create all database tables with proper schema.
    
    WHY MULTIPLE TABLES?
    This is called 'normalization' — separating data into logical
    tables avoids repetition and makes queries faster.
    """
    
    cursor = conn.cursor()
    
    # Table 1: Main adverse event reports table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ae_reports (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            report_id       TEXT UNIQUE NOT NULL,
            report_date     DATE,
            drug_name       TEXT,
            drug_batch      TEXT,
            dose_mg         INTEGER,
            route           TEXT,
            patient_age     INTEGER,
            patient_gender  TEXT,
            patient_weight_kg INTEGER,
            adverse_event   TEXT,
            onset_date      DATE,
            time_to_onset_days INTEGER,
            severity        TEXT,
            seriousness     TEXT,
            outcome         TEXT,
            reporter_type   TEXT,
            country         TEXT,
            causality       TEXT,
            is_duplicate    INTEGER DEFAULT 0,
            narrative       TEXT,
            created_at      DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Table 2: Signal tracking table
    # A "signal" in PV = a drug-AE combination that appears suspiciously often
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS signals (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            drug_name       TEXT,
            adverse_event   TEXT,
            report_count    INTEGER,
            ror_value       REAL,         -- Reporting Odds Ratio (signal metric)
            signal_strength TEXT,         -- Weak / Moderate / Strong
            detected_date   DATE,
            status          TEXT DEFAULT 'New'
        )
    """)
    
    # Table 3: Summary statistics table (for Power BI)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS monthly_summary (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            year_month      TEXT,
            total_reports   INTEGER,
            serious_reports INTEGER,
            fatal_reports   INTEGER,
            duplicate_reports INTEGER,
            top_drug        TEXT,
            top_ae          TEXT
        )
    """)
    
    conn.commit()
    print("✓ Tables created successfully")


# ── LOAD DATA ─────────────────────────────────────────────────

def load_data(conn):
    """
    Load CSV data into the database.
    
    pandas + sqlite3 work together: 
    df.to_sql() writes the entire DataFrame into a SQL table.
    """
    
    data_dir = "data/raw"
    csv_path = os.path.join(data_dir, "ae_reports.csv")

    # Ensure the data directory exists
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
        print(f"Created directory: {data_dir}/")

    # If CSV doesn't exist, create a dummy one
    if not os.path.exists(csv_path):
        print(f"Creating dummy data file: {csv_path}")
        dummy_data = {
            'report_id': [f'REP{i:03d}' for i in range(1, 11)],
            'report_date': pd.to_datetime(['2023-01-15', '2023-02-20', '2023-03-10', '2023-01-25', '2023-04-05', '2023-02-10', '2023-03-22', '2023-01-01', '2023-04-15', '2023-02-28']),
            'drug_name': ['DrugA', 'DrugB', 'DrugA', 'DrugC', 'DrugB', 'DrugA', 'DrugD', 'DrugC', 'DrugB', 'DrugA'],
            'drug_batch': ['B101', 'B202', 'B101', 'B303', 'B202', 'B101', 'B404', 'B303', 'B202', 'B101'],
            'dose_mg': [10, 20, 10, 50, 20, 10, 5, 50, 20, 10],
            'route': ['Oral', 'IV', 'Oral', 'Subcut', 'IV', 'Oral', 'Oral', 'Subcut', 'IV', 'Oral'],
            'patient_age': [34, 67, 55, 42, 78, 29, 61, 38, 71, 49],
            'patient_gender': ['F', 'M', 'F', 'M', 'F', 'M', 'F', 'M', 'F', 'M'],
            'patient_weight_kg': [65, 80, 70, 90, 60, 75, 58, 88, 62, 73],
            'adverse_event': ['Nausea', 'Headache', 'Rash', 'Dizziness', 'Fatigue', 'Nausea', 'Vomiting', 'Rash', 'Headache', 'Nausea'],
            'onset_date': pd.to_datetime(['2023-01-16', '2023-02-21', '2023-03-11', '2023-01-26', '2023-04-06', '2023-02-11', '2023-03-23', '2023-01-02', '2023-04-16', '2023-03-01']),
            'time_to_onset_days': [1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
            'severity': ['Mild', 'Moderate', 'Severe', 'Mild', 'Moderate', 'Mild', 'Severe', 'Mild', 'Moderate', 'Mild'],
            'seriousness': ['Non-serious', 'Serious', 'Serious', 'Non-serious', 'Serious', 'Non-serious', 'Serious', 'Non-serious', 'Serious', 'Non-serious'],
            'outcome': ['Recovered', 'Recovered', 'Recovered with sequelae', 'Recovered', 'Recovered', 'Recovered', 'Fatal', 'Recovered', 'Recovered', 'Recovered'],
            'reporter_type': ['Patient', 'HCP', 'HCP', 'Patient', 'HCP', 'Patient', 'HCP', 'Patient', 'HCP', 'Patient'],
            'country': ['USA', 'CAN', 'USA', 'GBR', 'GER', 'USA', 'FRA', 'GBR', 'GER', 'USA'],
            'causality': ['Probable', 'Possible', 'Probable', 'Possible', 'Probable', 'Possible', 'Probable', 'Possible', 'Probable', 'Possible'],
            'is_duplicate': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            'narrative': [f'Narrative for report {i}' for i in range(1, 11)],
            'created_at': pd.to_datetime(['2023-01-15', '2023-02-20', '2023-03-10', '2023-01-25', '2023-04-05', '2023-02-10', '2023-03-22', '2023-01-01', '2023-04-15', '2023-02-28'])
        }
        df = pd.DataFrame(dummy_data)
        df.to_csv(csv_path, index=False)
        print(f"Generated dummy data with {len(df)} records.")
    else:
        # Read the CSV we generated in Step 1
        df = pd.read_csv(csv_path)
    
    # Load into ae_reports table
    # if_exists='replace' = clear and reload (good for development)
    df.to_sql("ae_reports", conn, if_exists="replace", index=False)
    
    print(f"✓ Loaded {len(df)} records into ae_reports table")
    return df


# ── RUN SQL QUERIES (ANALYSIS) ────────────────────────────────

def run_analysis_queries(conn):
    """
    Run SQL queries to analyze the data.
    This section shows your SQL skills to employers.
    """
    
    print("\n" + "="*60)
    print("SQL ANALYSIS RESULTS")
    print("="*60)
    
    # Query 1: Total reports by drug
    print("\n[Query 1] Top 5 drugs by adverse event count:")
    query1 = """
        SELECT 
            drug_name,
            COUNT(*) AS total_reports,
            SUM(CASE WHEN seriousness != 'Non-serious' THEN 1 ELSE 0 END) AS serious_reports,
            ROUND(
                100.0 * SUM(CASE WHEN seriousness != 'Non-serious' THEN 1 ELSE 0 END) / COUNT(*),
                1
            ) AS serious_percentage
        FROM ae_reports
        GROUP BY drug_name
        ORDER BY total_reports DESC
        LIMIT 5
    """
    result1 = pd.read_sql(query1, conn)
    print(result1.to_string(index=False))
    
    # Query 2: Severity distribution
    print("\n[Query 2] Severity distribution:")
    query2 = """
        SELECT 
            severity,
            COUNT(*) AS count,
            ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM ae_reports), 1) AS percentage
        FROM ae_reports
        GROUP BY severity
        ORDER BY count DESC
    """
    result2 = pd.read_sql(query2, conn)
    print(result2.to_string(index=False))
    
    # Query 3: Monthly trend (last 12 months)
    print("\n[Query 3] Monthly report trend (last 6 months):")
    query3 = """
        SELECT 
            strftime('%Y-%m', report_date) AS year_month,
            COUNT(*) AS total_reports,
            SUM(CASE WHEN seriousness = 'Death' THEN 1 ELSE 0 END) AS fatal_reports
        FROM ae_reports
        WHERE report_date >= date('now', '-12 months')
        GROUP BY year_month
        ORDER BY year_month DESC
        LIMIT 6
    """
    result3 = pd.read_sql(query3, conn)
    print(result3.to_string(index=False))
    
    # Query 4: Drug-AE combination frequency (for signal detection)!
    print("\n[Query 4] Top drug-AE combinations (potential signals):")
    query4 = """
        SELECT 
            drug_name,
            adverse_event,
            COUNT(*) AS report_count,
            AVG(patient_age) AS avg_patient_age,
            SUM(CASE WHEN severity IN ('Severe', 'Life-threatening', 'Fatal') THEN 1 ELSE 0 END) AS severe_count
        FROM ae_reports
        GROUP BY drug_name, adverse_event
        HAVING report_count >= 3
        ORDER BY report_count DESC
        LIMIT 10
    """
    result4 = pd.read_sql(query4, conn)
    print(result4.to_string(index=False))
    
    # Query 5: Duplicate detection
    print("\n[Query 5] Potential duplicate reports:")
    query5 = """
        SELECT 
            COUNT(*) AS total_duplicates,
            ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM ae_reports), 1) AS duplicate_rate
        FROM ae_reports
        WHERE is_duplicate = 1
    """
    result5 = pd.read_sql(query5, conn)
    print(result5.to_string(index=False))
    
    # Save monthly summary to database (for Power BI)
    query_monthly = """
        SELECT 
            strftime('%Y-%m', report_date) AS year_month,
            COUNT(*) AS total_reports,
            SUM(CASE WHEN seriousness != 'Non-serious' THEN 1 ELSE 0 END) AS serious_reports,
            SUM(CASE WHEN seriousness = 'Death' THEN 1 ELSE 0 END) AS fatal_reports,
            SUM(CASE WHEN is_duplicate = 1 THEN 1 ELSE 0 END) AS duplicate_reports
        FROM ae_reports
        GROUP BY year_month
        ORDER BY year_month
    """
    monthly_df = pd.read_sql(query_monthly, conn)
    monthly_df.to_sql("monthly_summary", conn, if_exists="replace", index=False)
    print("\n✓ Monthly summary saved to database")
    
    return result4   # Return signals data for next step


# ── MAIN ──────────────────────────────────────────────────────

if __name__ == "__main__":
    
    print("Setting up pharmacovigilance database...")
    
    conn = get_connection()
    create_tables(conn)
    load_data(conn)
    signals_data = run_analysis_queries(conn)
    
    conn.close()
    print("\n✓ Database setup complete: database/pharmacovigilance.db")