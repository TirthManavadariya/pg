"""
app.py
Root entrypoint delegating to backend/app.py
"""
import os
import sys

backend_dir = os.path.join(os.path.dirname(__file__), 'backend')
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from backend.app import app

if __name__ == '__main__':
    print("Starting Roomee Discovery Engine from root entrypoint on http://localhost:5000 ...")
    app.run(host='0.0.0.0', port=5000, debug=False)
