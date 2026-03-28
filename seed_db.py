import pandas as pd
import math
import sys
import os
import json
from database import get_connection, save_transaction, USE_MYSQL

CSV_PATH = r"C:\Users\User\.cache\kagglehub\datasets\ealaxi\paysim1\versions\2\PS_20174392719_1491204439457_log.csv"

def seed_database(limit=None):
    if not os.path.exists(CSV_PATH):
        print(f"[ERROR] PaySim dataset not found at {CSV_PATH}")
        sys.exit(1)
        
    print("[INFO] Loading CSV data into pandas...")
    # Load columns needed: step, type, amount, oldbalanceOrg, newbalanceOrig, oldbalanceDest, newbalanceDest, isFraud
    df = pd.read_csv(CSV_PATH)
    
    # If limit is set, take all fraud + random sample of legit
    if limit is not None and len(df) > limit:
        print(f"[INFO] Sampling dataset to {limit} rows...")
        fraud_df = df[df['isFraud'] == 1]
        legit_df = df[df['isFraud'] == 0].sample(n=limit - len(fraud_df), random_state=42)
        df = pd.concat([fraud_df, legit_df]).sample(frac=1, random_state=42).reset_index(drop=True)
        
    print(f"[INFO] Formatting {len(df)} transactions for database insertion... (This will take a moment)")
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # Prepare batch insertion
    chunk_size = 5000
    total_chunks = math.ceil(len(df) / chunk_size)
    
    placeholder = '%s' if USE_MYSQL else '?'
    insert_sql = f"""
        INSERT INTO transactions
        (transaction_id, type, amount, orig_before, orig_after,
         dest_before, dest_after, is_fraud, fraud_prob, risk_level, status)
        VALUES ({placeholder},{placeholder},{placeholder},{placeholder},{placeholder},
                {placeholder},{placeholder},{placeholder},{placeholder},{placeholder},{placeholder})
    """
    
    # Truncate existing transactions table to ensure fresh seed
    try:
        cursor.execute("TRUNCATE TABLE transactions")
        print("[INFO] Cleared existing transactions.")
    except Exception as e:
        cursor.execute("DELETE FROM transactions")
        print("[INFO] Deleted existing transactions.")
        
    for i in range(total_chunks):
        chunk = df.iloc[i * chunk_size : (i + 1) * chunk_size]
        batch_data = []
        
        for idx, row in chunk.iterrows():
            # Derive simulated feature outputs for historical DB entries
            # Since the model isn't predicting these right now, we infer probability and risk
            is_fraud = int(row['isFraud'])
            prob = 0.95 if is_fraud else 0.05
            risk_level = 'CRITICAL' if is_fraud else 'LOW'
            status = 'BLOCKED' if is_fraud else 'PROCESSED'
            
            # Generate a pseudo-ID using the DataFrame index plus the original step
            txn_id = f"TXN-{int(row['step'])}-{idx:06x}".upper()
            
            batch_data.append((
                txn_id,
                row['type'],
                float(row['amount']),
                float(row['oldbalanceOrg']),
                float(row['newbalanceOrig']),
                float(row['oldbalanceDest']),
                float(row['newbalanceDest']),
                is_fraud,
                prob,
                risk_level,
                status
            ))
            
        cursor.executemany(insert_sql, batch_data)
        conn.commit()
        
        if (i + 1) % 10 == 0:
            print(f"  -> Inserted {min((i + 1) * chunk_size, len(df))} / {len(df)} rows...")
            
    conn.close()
    print("[SUCCESS] PaySim dataset seeded to database successfully!")

if __name__ == '__main__':
    # Defaulting to 100,000 for realistic performance during the seed, covering all fraud cases.
    # Change to limit=None to upload the entire 6.3m dataset (which will take much longer).
    seed_database(limit=100000)
