"""
GHANA'S AI POLICE Database Module
Supports MySQL (primary) with SQLite fallback for offline/demo use.
"""
import sqlite3
import os
import json
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), 'aifds.db')

# --- Try MySQL first, fall back to SQLite -----------------------------------
MYSQL_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '1996justy.',        # <-- change to your MySQL root password
    'database': 'aifds_mm',
    'port': 3306
}

USE_MYSQL = False
try:
    import mysql.connector
    conn_test = mysql.connector.connect(**MYSQL_CONFIG)
    conn_test.close()
    USE_MYSQL = True
    print("[DB] Connected to MySQL")
except Exception as e:
    print(f"[DB] MySQL unavailable ({e}), using SQLite")


# --- Connection factory ------------------------------------------------------
def get_connection():
    if USE_MYSQL:
        import mysql.connector
        return mysql.connector.connect(**MYSQL_CONFIG)
    else:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn


def placeholder():
    """Return the correct parameter placeholder for the active DB."""
    return '%s' if USE_MYSQL else '?'


def row_to_dict(cursor, row):
    """Convert a database row to a dictionary, supporting both SQLite and MySQL."""
    if row is None: return None
    # sqlite3.Row or similar mapping
    if hasattr(row, 'keys'):
        return dict(row)
    # MySQL tuple - use cursor.description to get column names
    if cursor.description:
        names = [col[0] for col in cursor.description]
        return dict(zip(names, row))
    return row


# --- Schema initialisation ---------------------------------------------------
SCHEMA_SQLITE = """
CREATE TABLE IF NOT EXISTS transactions (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    transaction_id  TEXT    NOT NULL,
    type            TEXT    NOT NULL,
    amount          REAL    NOT NULL,
    orig_before     REAL    NOT NULL,
    orig_after      REAL    NOT NULL,
    dest_before     REAL    NOT NULL,
    dest_after      REAL    NOT NULL,
    is_fraud        INTEGER NOT NULL,
    fraud_prob      REAL    NOT NULL,
    risk_level      TEXT    NOT NULL,
    top_features    TEXT,
    status          TEXT    DEFAULT 'PROCESSED',
    created_at      TEXT    DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS alerts (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    transaction_id  TEXT    NOT NULL,
    alert_type      TEXT    NOT NULL,
    message         TEXT,
    resolved        INTEGER DEFAULT 0,
    created_at      TEXT    DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS model_metrics (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    version     TEXT    NOT NULL,
    accuracy    REAL,
    precision   REAL,
    recall      REAL,
    f1_score    REAL,
    trained_at  TEXT    DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS users (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    username    TEXT    UNIQUE NOT NULL,
    password    TEXT    NOT NULL,
    role        TEXT    DEFAULT 'analyst',
    created_at  TEXT    DEFAULT (datetime('now'))
);
"""

SCHEMA_MYSQL = """
CREATE TABLE IF NOT EXISTS transactions (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    transaction_id  VARCHAR(64)  NOT NULL,
    type            VARCHAR(20)  NOT NULL,
    amount          DECIMAL(18,2) NOT NULL,
    orig_before     DECIMAL(18,2) NOT NULL,
    orig_after      DECIMAL(18,2) NOT NULL,
    dest_before     DECIMAL(18,2) NOT NULL,
    dest_after      DECIMAL(18,2) NOT NULL,
    is_fraud        TINYINT      NOT NULL,
    fraud_prob      FLOAT        NOT NULL,
    risk_level      VARCHAR(10)  NOT NULL,
    top_features    TEXT,
    status          VARCHAR(20)  DEFAULT 'PROCESSED',
    created_at      TIMESTAMP    DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS alerts (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    transaction_id  VARCHAR(64) NOT NULL,
    alert_type      VARCHAR(50) NOT NULL,
    message         TEXT,
    resolved        TINYINT DEFAULT 0,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS model_metrics (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    version     VARCHAR(20) NOT NULL,
    accuracy    FLOAT,
    precision_score FLOAT,
    recall_score    FLOAT,
    f1_score    FLOAT,
    trained_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS users (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    username    VARCHAR(50) UNIQUE NOT NULL,
    password    VARCHAR(255) NOT NULL,
    role        VARCHAR(20) DEFAULT 'analyst',
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""


def init_db():
    """Initialise database schema and seed default admin user."""
    conn = get_connection()
    cursor = conn.cursor()
    
    if USE_MYSQL:
        # Create database if not exists
        try:
            import mysql.connector
            c = mysql.connector.connect(
                host=MYSQL_CONFIG['host'],
                user=MYSQL_CONFIG['user'],
                password=MYSQL_CONFIG['password'],
                port=MYSQL_CONFIG['port']
            )
            c.cursor().execute(f"CREATE DATABASE IF NOT EXISTS {MYSQL_CONFIG['database']}")
            c.close()
        except Exception:
            pass
        for stmt in SCHEMA_MYSQL.strip().split(';'):
            stmt = stmt.strip()
            if stmt:
                cursor.execute(stmt)
        conn.commit()
    else:
        conn.executescript(SCHEMA_SQLITE)
        conn.commit()
    
    # Seed default admin (password: justy1996.)
    import hashlib
    pwd = hashlib.sha256('justy1996.'.encode()).hexdigest()
    p = placeholder()
    try:
        cursor.execute(
            f"INSERT INTO users (username, password, role) VALUES ({p},{p},{p})",
            ('Justina', pwd, 'admin')
        )
        conn.commit()
    except Exception:
        pass  # Already exists
    
    conn.close()
    print("[DB] Schema initialised")


# --- Transaction CRUD --------------------------------------------------------
def save_transaction(txn_id, txn_type, amount, orig_before, orig_after,
                     dest_before, dest_after, is_fraud, fraud_prob,
                     risk_level, top_features, status):
    conn = get_connection()
    cursor = conn.cursor()
    p = placeholder()
    feats_json = json.dumps(top_features)
    cursor.execute(
        f"""INSERT INTO transactions
            (transaction_id,type,amount,orig_before,orig_after,
             dest_before,dest_after,is_fraud,fraud_prob,risk_level,top_features,status)
            VALUES ({p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p})""",
        (txn_id, txn_type, amount, orig_before, orig_after,
         dest_before, dest_after, int(is_fraud), fraud_prob,
         risk_level, feats_json, status)
    )
    conn.commit()
    conn.close()


def get_transactions(limit=100, fraud_only=False):
    conn = get_connection()
    cursor = conn.cursor()
    p = placeholder()
    if fraud_only:
        cursor.execute(
            f"SELECT * FROM transactions WHERE is_fraud={p} ORDER BY created_at DESC LIMIT {p}",
            (1, limit)
        )
    else:
        cursor.execute(
            f"SELECT * FROM transactions ORDER BY created_at DESC LIMIT {p}",
            (limit,)
        )
    rows = cursor.fetchall()
    conn.close()
    return [row_to_dict(cursor, r) for r in rows]


def get_stats():
    """Return high-level dashboard statistics."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as total FROM transactions")
    total = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) as fraud FROM transactions WHERE is_fraud=1")
    fraud = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) as blocked FROM transactions WHERE status='BLOCKED'")
    blocked = cursor.fetchone()[0]
    cursor.execute("SELECT SUM(amount) as vol FROM transactions WHERE is_fraud=1")
    row = cursor.fetchone()
    fraud_volume = float(row[0]) if row[0] else 0.0
    conn.close()
    legit = total - fraud
    detection_rate = round((fraud / total * 100), 1) if total > 0 else 0
    return {
        'total': total,
        'fraud': fraud,
        'legitimate': legit,
        'blocked': blocked,
        'fraud_volume': round(fraud_volume, 2),
        'detection_rate': detection_rate
    }


def save_alert(txn_id, alert_type, message):
    conn = get_connection()
    cursor = conn.cursor()
    p = placeholder()
    cursor.execute(
        f"INSERT INTO alerts (transaction_id,alert_type,message) VALUES ({p},{p},{p})",
        (txn_id, alert_type, message)
    )
    conn.commit()
    conn.close()


def get_alerts(limit=50):
    conn = get_connection()
    cursor = conn.cursor()
    p = placeholder()
    cursor.execute(
        f"SELECT * FROM alerts ORDER BY created_at DESC LIMIT {p}", (limit,)
    )
    rows = cursor.fetchall()
    conn.close()
    return [row_to_dict(cursor, r) for r in rows]


def save_model_metrics(version, accuracy, precision, recall, f1):
    conn = get_connection()
    cursor = conn.cursor()
    p = placeholder()
    if USE_MYSQL:
        cursor.execute(
            f"INSERT INTO model_metrics (version,accuracy,precision_score,recall_score,f1_score) VALUES ({p},{p},{p},{p},{p})",
            (version, accuracy, precision, recall, f1)
        )
    else:
        cursor.execute(
            f"INSERT INTO model_metrics (version,accuracy,precision,recall,f1_score) VALUES ({p},{p},{p},{p},{p})",
            (version, accuracy, precision, recall, f1)
        )
    conn.commit()
    conn.close()


def get_latest_metrics():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM model_metrics ORDER BY trained_at DESC LIMIT 1")
    row = cursor.fetchone()
    conn.close()
    return row_to_dict(cursor, row)


def verify_user(username, password):
    import hashlib
    pwd = hashlib.sha256(password.encode()).hexdigest()
    conn = get_connection()
    cursor = conn.cursor()
    p = placeholder()
    cursor.execute(
        f"SELECT * FROM users WHERE username={p} AND password={p}",
        (username, pwd)
    )
    row = cursor.fetchone()
    conn.close()
    return row_to_dict(cursor, row)
