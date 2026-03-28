"""
GHANA'S AI POLICE: AI-Powered Fraud Detection System for Mobile Money Ghana
Integrated Backend — app.py
"""
from flask import Flask, request, jsonify, render_template, session
import os, datetime, uuid, random
from database import init_db, verify_user, get_stats, get_transactions, save_transaction, save_alert, get_alerts, get_latest_metrics, save_model_metrics
from model import predict_transaction, train_model

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Initialise DB on start
init_db()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.json
    if not data: return jsonify({'success': False, 'message': 'No data'}), 400
    u = data.get('username')
    p = data.get('password')
    user = verify_user(u, p)
    if user:
        session['user'] = u
        return jsonify({'success': True, 'username': u, 'role': user['role']})
    return jsonify({'success': False, 'message': 'Invalid credentials'}), 401

@app.route('/api/logout', methods=['POST'])
def api_logout():
    session.pop('user', None)
    return jsonify({'success': True})

@app.route('/api/stats', methods=['GET'])
def api_stats():
    stats = get_stats()
    return jsonify(stats)

@app.route('/api/transactions', methods=['GET'])
def api_transactions():
    limit = int(request.args.get('limit', 100))
    fraud_only = request.args.get('fraud_only', 'false').lower() == 'true'
    txns = get_transactions(limit=limit, fraud_only=fraud_only)
    return jsonify(txns)

@app.route('/api/alerts', methods=['GET'])
def api_alerts():
    limit = int(request.args.get('limit', 50))
    alerts = get_alerts(limit=limit)
    return jsonify(alerts)

@app.route('/api/predict', methods=['POST'])
def api_predict():
    data = request.json
    try:
        res = predict_transaction(data)
        txn_id = f"TXN-{uuid.uuid4().hex[:8].upper()}"
        
        # Save to DB
        save_transaction(
            txn_id, data['type'], data['amount'], 
            data['oldbalanceOrg'], data['newbalanceOrig'],
            data['oldbalanceDest'], data['newbalanceDest'],
            res['is_fraud'], res['fraud_probability'],
            res['risk_level'], res['top_features'],
            'BLOCKED' if res['is_fraud'] else 'PROCESSED'
        )
        
        if res['is_fraud']:
            save_alert(txn_id, 'FRAUD_ALERT', f"Potential fraud detected: {res['risk_level']} risk level.")
            
        res['transaction_id'] = txn_id
        res['status'] = 'BLOCKED' if res['is_fraud'] else 'PROCESSED'
        return jsonify(res)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/model/info', methods=['GET'])
def api_model_info():
    metrics = get_latest_metrics()
    return jsonify({
        'algorithm': 'HistGradientBoosting',
        'resampling': 'SMOTE (Oversampling)',
        'dataset': 'Kaggle PaySim (500k sample)',
        'metrics': metrics
    })

@app.route('/api/model/retrain', methods=['POST'])
def api_model_retrain():
    try:
        metrics = train_model()
        save_model_metrics(
            'v1.1', metrics['accuracy'], metrics['precision'], 
            metrics['recall'], metrics['f1']
        )
        return jsonify({'success': True, 'metrics': metrics})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/simulate', methods=['POST'])
def api_simulate():
    count = int(request.json.get('count', 1))
    results = []
    types = ['CASH_OUT', 'TRANSFER', 'CASH_IN', 'PAYMENT', 'DEBIT']
    
    for _ in range(count):
        # Generate random transaction
        is_fraud_sim = random.random() < 0.2 # 20% fraud for simulation
        if is_fraud_sim:
            amt = random.uniform(50000, 500000)
            orig_b = amt + random.uniform(0, 1000)
            orig_a = 0
            dest_b = 0
            dest_a = amt
            t_type = random.choice(['CASH_OUT', 'TRANSFER'])
        else:
            amt = random.uniform(10, 5000)
            orig_b = random.uniform(amt, amt * 10)
            orig_a = orig_b - amt
            dest_b = random.uniform(0, 10000)
            dest_a = dest_b + amt
            t_type = random.choice(types)
            
        payload = {
            'type': t_type, 'amount': amt,
            'oldbalanceOrg': orig_b, 'newbalanceOrig': orig_a,
            'oldbalanceDest': dest_b, 'newbalanceDest': dest_a,
            'hour': random.randint(0, 23),
            'transaction_freq': random.randint(1, 10)
        }
        
        # Predict
        res = predict_transaction(payload)
        txn_id = f"TXN-SIM-{uuid.uuid4().hex[:6].upper()}"
        save_transaction(
            txn_id, payload['type'], payload['amount'],
            payload['oldbalanceOrg'], payload['newbalanceOrig'],
            payload['oldbalanceDest'], payload['newbalanceDest'],
            res['is_fraud'], res['fraud_probability'],
            res['risk_level'], res['top_features'],
            'BLOCKED' if res['is_fraud'] else 'PROCESSED'
        )
        if res['is_fraud']:
            save_alert(txn_id, 'SIMULATED_FRAUD', f"Simulated fraud detected! Risk: {res['risk_level']}")
        
        results.append({'transaction_id': txn_id, 'is_fraud': res['is_fraud']})
        
    return jsonify({'success': True, 'simulated': count, 'results': results})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
