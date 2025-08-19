#!/usr/bin/env python3
"""
Launch script for ReelsAutoPilot Dashboard API
"""

import sys
import os

# Add the src directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

if __name__ == "__main__":
    from api import app

    print("🚀 Starting ReelsAutoPilot Dashboard API")
    print("📊 Dashboard will be available at http://localhost:3000")
    print("🔗 API endpoints at http://localhost:5000/api/")

    app.run(host="0.0.0.0", port=5000, debug=True, threaded=True)
