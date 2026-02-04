#!/usr/bin/env python3
"""
Скрипт для запуска React frontend
"""

import subprocess
import webbrowser
import time
from pathlib import Path

def check_node_installed():
    try:
        result = subprocess.run(['node', '--version'], capture_output=True, text=True)
        return result.returncode == 0
    except FileNotFoundError:
        return False

def check_npm_installed():
    try:
        result = subprocess.run(['npm', '--version'], capture_output=True, text=True)
        return result.returncode == 0
    except FileNotFoundError:
        return False

def main():
    print("🌐 Running React Frontend...")
    print("=" * 40)

    print("📋 Checking dependencies...")

    if not check_node_installed():
        print("❌ Node.js is not installed. Install Node.js from https://nodejs.org/")
        return False

    if not check_npm_installed():
        print("❌ npm is not installed. Install npm")
        return False

    print("✅ Node.js and npm are installed")

    frontend_path = Path("frontend")
    if not frontend_path.exists():
        print("❌ frontend folder not found")
        return False

    print("\n📦 Installing frontend dependencies...")
    try:
        subprocess.run(["npm", "install"], cwd="frontend", check=True)
        print("✅ frontend dependencies installed")
    except subprocess.CalledProcessError:
        print("❌ Error installing frontend dependencies")
        return False

    print("\n🚀 Running React application...")
    print("⏳ Waiting for application to start...")

    try:
        process = subprocess.Popen(["npm", "start"], cwd="frontend")

        time.sleep(5)
        try:
            webbrowser.open("http://localhost:3000")
        except Exception:
            pass

        print("\n🎉 React application started!")
        print("=" * 40)
        print("🌐 Frontend: http://localhost:3000")
        print("🔧 Backend API: http://localhost:8000 (run separately)")
        print("⏹️ Press Ctrl+C to stop")

        process.wait()

    except KeyboardInterrupt:
        print("\n🛑 Stopping React application...")
        process.terminate()
        print("✅ Application stopped")
    except Exception as e:
        print(f"❌ Error starting: {e}")
        return False

if __name__ == "__main__":
    main()
