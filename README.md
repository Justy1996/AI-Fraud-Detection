# GHANA'S AI POLICE: AI Fraud Detection System for Mobile Money
## Ghana Mobile Money Protection Platform
**Group Four Research Thesis | ITE 300E | University of Skills Training and Entrepreneurial Development**

---

## 🚀 Quick Start (3 Steps)

### Step 1 — Install Python Dependencies
```bash
pip install -r requirements.txt
```

### Step 2 — (Optional) Set Up MySQL
If you have MySQL installed:
```bash
mysql -u root -p < setup_mysql.sql
```
Then edit `database.py` and set your MySQL password:
```python
MYSQL_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'YOUR_MYSQL_PASSWORD',   # ← Change this
    'database': 'aifds_mm',
    'port': 3306
}
```
> **Note:** If MySQL is not available, the system automatically uses SQLite (no setup required).

### Step 3 — Launch the System
```bash
python start.py
```
Then open: **http://localhost:5000**

**Default Login:** `Justina` / `justy1996.`

---

## 🏗️ Project Structure
```
aifds/
├── app.py          — Flask REST API backend
├── model.py        — ML model (GradientBoosting + SMOTE)
├── database.py     — MySQL/SQLite database layer
├── setup_mysql.sql — MySQL schema creation script
├── start.py        — One-click launcher
├── fraud_model.pkl — Trained model (auto-generated)
├── scaler.pkl      — Feature scaler (auto-generated)
├── aifds.db        — SQLite database (if MySQL not used)
└── static/
    └── index.html  — Full dashboard UI
```

---

## 🤖 AI Model Details

| Property | Value |
|---|---|
| **Algorithm** | Gradient Boosting Classifier (≈ XGBoost) |
| **Resampling** | SMOTE (Synthetic Minority Oversampling) |
| **Training Data** | PaySim-style synthetic (50,000 transactions) |
| **Features** | 17 engineered features |
| **Target Precision** | ≥ 0.94 |
| **Target Recall** | ≥ 0.98 |
| **Target F1** | ≥ 0.96 |
| **Latency** | < 100ms per prediction |

### Feature Engineering
- One-hot encoded transaction type (CASH_IN, CASH_OUT, TRANSFER, PAYMENT, DEBIT)
- Balance difference: sender (orig_before − orig_after)
- Balance difference: receiver (dest_after − dest_before)
- Balance mismatch (fraud indicator)
- Log-scaled amount
- Amount-to-balance ratio
- Origin account drained flag
- Destination was empty flag
- Night-time transaction flag (22:00–04:00)
- Transaction frequency

---

## 🖥️ Dashboard Features

| Feature | Description |
|---|---|
| **Real-time Stats** | Total transactions, fraud count, blocked count, fraud volume |
| **Fraud Table** | Live list of detected fraud transactions |
| **Alert Feed** | Real-time fraud alert notifications |
| **Analyse Transaction** | Manual transaction analysis with fraud probability |
| **Simulation** | Generate 10 random transactions to test the system |
| **All Transactions** | Complete audit log with filtering |
| **Security Alerts** | Full alert history |
| **Model Metrics** | Accuracy, Precision, Recall, F1 with target comparison |
| **Model Retraining** | Retrain model with new data |

---

## 🔌 REST API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `POST /api/login` | POST | Authenticate user |
| `GET /api/stats` | GET | Dashboard statistics |
| `GET /api/transactions` | GET | List transactions |
| `POST /api/predict` | POST | Analyse a transaction |
| `POST /api/simulate` | POST | Simulate N transactions |
| `GET /api/alerts` | GET | List fraud alerts |
| `GET /api/model/info` | GET | Model information |
| `POST /api/model/retrain` | POST | Retrain the model |

### Example: Analyse a Transaction
```bash
curl -X POST http://localhost:5000/api/predict \
  -H "Content-Type: application/json" \
  -d '{
    "type": "CASH_OUT",
    "amount": 250000,
    "oldbalanceOrg": 250000,
    "newbalanceOrig": 0,
    "oldbalanceDest": 0,
    "newbalanceDest": 250000,
    "hour": 2,
    "transaction_freq": 1
  }'
```

---

## 🇬🇭 Compliance
- Bank of Ghana (BoG) fraud reporting standards
- Data Protection Act 2012
- No personal identifiers stored (nameOrig/nameDest anonymised)
- Full audit log with confidence scores and feature importance

---

## 📞 Support
Built by Group Four | ITE 300E | USTED Ghana | March 2026
