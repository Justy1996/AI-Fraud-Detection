#!/usr/bin/env python3
"""
GHANA'S AI POLICE Quick Launcher
Run: python start.py
"""
import subprocess, sys, os, webbrowser, time

print("""
╔══════════════════════════════════════════════════════════╗
║   GHANA'S AI POLICE · Ghana Mobile Money Fraud Detection System   ║
║   University of Skills Training and Entrepreneurial Dev  ║
╚══════════════════════════════════════════════════════════╝
""")

# Check Python packages
required_packages = {
    'flask': 'flask',
    'sklearn': 'scikit-learn',
    'pandas': 'pandas',
    'numpy': 'numpy'
}
missing = []
for import_name, pip_name in required_packages.items():
    try:
        __import__(import_name)
    except ImportError:
        missing.append(pip_name)

if missing:
    print(f"[ERROR] Missing packages: {missing}")
    print(f"Install with: {sys.executable} -m pip install -r requirements.txt")
    sys.exit(1)

os.chdir(os.path.dirname(os.path.abspath(__file__)))
print("[START] Launching GHANA'S AI POLICE server...")
print("[INFO]  URL: http://localhost:5000")
print("[INFO]  Login: Justina / justy1996.")
print("[INFO]  Press Ctrl+C to stop\n")

# Open browser after delay
def open_browser():
    time.sleep(3)
    webbrowser.open('http://localhost:5000')

import threading
threading.Thread(target=open_browser, daemon=True).start()

subprocess.run([sys.executable, 'app.py'])
