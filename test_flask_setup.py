#!/usr/bin/env python3
"""
Test Flask installation and imports
"""

import sys
from pathlib import Path

def test_imports():
    """Test all required imports"""
    print("🧪 Testing Flask Installation and Imports")
    print("=" * 45)
    
    # Test basic Python imports
    try:
        import os
        import logging
        import json
        from typing import Dict, Any
        print("✅ Basic Python imports: OK")
    except ImportError as e:
        print(f"❌ Basic Python imports failed: {e}")
        return False
    
    # Test Flask
    try:
        from flask import Flask, render_template, jsonify, request
        print("✅ Flask core imports: OK")
    except ImportError as e:
        print(f"❌ Flask import failed: {e}")
        print("💡 Install Flask: pip install Flask>=2.3.0")
        return False
    
    # Test Flask-CORS (optional)
    try:
        from flask_cors import CORS
        print("✅ Flask-CORS import: OK")
    except ImportError:
        print("⚠️  Flask-CORS not available (optional)")
        print("💡 Install Flask-CORS: pip install Flask-CORS>=4.0.0")
    
    # Test project imports
    project_root = Path(__file__).parent
    sys.path.insert(0, str(project_root))
    sys.path.insert(0, str(project_root / "src"))
    
    try:
        import project_config
        print("✅ Project config import: OK")
    except ImportError as e:
        print(f"⚠️  Project config import failed: {e}")
        print("💡 This is normal if project_config.py doesn't exist yet")
    
    # Test KitchenRadio daemon
    try:
        from kitchen_radio import KitchenRadio
        print("✅ KitchenRadio daemon import: OK")
    except ImportError as e:
        print(f"❌ KitchenRadio daemon import failed: {e}")
        print("💡 Make sure kitchen_radio.py exists in the project root")
        return False
    
    # Test creating a simple Flask app
    try:
        app = Flask(__name__)
        print("✅ Flask app creation: OK")
    except Exception as e:
        print(f"❌ Flask app creation failed: {e}")
        return False
    
    return True

def test_file_structure():
    """Test required file structure"""
    print("\n📁 Testing File Structure")
    print("=" * 25)
    
    project_root = Path(__file__).parent
    required_files = [
        "kitchen_radio.py",
        "requirements.txt",
        "web/kitchen_radio_web.py",
        "web/templates/index.html",
        "web/static/css/style.css",
        "web/static/js/app.js"
    ]
    
    all_exist = True
    for file_path in required_files:
        full_path = project_root / file_path
        if full_path.exists():
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} - Missing!")
            all_exist = False
    
    return all_exist

def main():
    """Run all tests"""
    imports_ok = test_imports()
    files_ok = test_file_structure()
    
    print("\n" + "=" * 45)
    if imports_ok and files_ok:
        print("🎉 All tests passed! Flask debug should work.")
        print("💡 Try running: python debug_flask.py")
    else:
        print("❌ Some tests failed. Fix the issues above before debugging.")
        if not imports_ok:
            print("📦 Install missing packages: pip install -r requirements.txt")
        if not files_ok:
            print("📁 Make sure all required files exist")
    
    return 0 if (imports_ok and files_ok) else 1

if __name__ == "__main__":
    sys.exit(main())
