import subprocess
import time
import sys
import os
import signal
import webbrowser

def stream_process(process, prefix):
    """Pipe output from subprocess to stdout with a prefix."""
    for line in iter(process.stdout.readline, ""):
        print(f"[{prefix}] {line.strip()}")

def main():
    print("🚀 INITIALIZING JARVIS GOD MODE...")
    
    # 1. Environment Check
    if not os.path.exists(".env"):
        print("❌ CRITICAL: .env file missing! Please copy .env.example to .env")
        return

    # 2. Database Migration (Auto-Upgrade to Postgres)
    print("🛠️  Checking Database Connections...")
    
    # Check if Postgres is installed
    try:
        subprocess.run(["psql", "--version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print("✅ PostgreSQL is installed.")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("⚠️ PostgreSQL not found. Attempting to install via Homebrew...")
        try:
            subprocess.run(["brew", "install", "postgresql"], check=True)
            subprocess.run(["brew", "services", "start", "postgresql"], check=True)
            print("✅ PostgreSQL installed and started.")
            # Create extension
            subprocess.run(["psql", "postgres", "-c", "CREATE EXTENSION IF NOT EXISTS vector;"], check=False)
        except Exception as e:
            print(f"❌ Failed to auto-install Postgres: {e}")
            print("👉 Please run: brew install postgresql && brew services start postgresql")
            # We continue anyway, as db_manager has a fallback
            
    # Create extension if installed but not set up
    try:
        subprocess.run(["psql", "postgres", "-c", "CREATE EXTENSION IF NOT EXISTS vector;"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except:
        pass
    
    # 3. Launch The Brain (JarvisScanner)
    print("🧠 Starting Main Brain (Scanner & Trader)...")
    env = os.environ.copy()
    env["PYTHONPATH"] = os.getcwd()
    env["PYTHONUNBUFFERED"] = "1"
    
    brain_process = subprocess.Popen(
        [sys.executable, "src/main.py"],
        stdout=sys.stdout,
        stderr=sys.stderr,
        env=env
    )

    # 4. Launch The UI (Streamlit)
    print("📊 Starting Neural Dashboard...")
    ui_process = subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", "src/dashboard/app.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    # 5. Open Browser Automatically
    time.sleep(3) # Wait for UI to boot
    webbrowser.open("http://localhost:8501")
    print("✅ SYSTEM ONLINE: http://localhost:8501")
    print("--- Press Ctrl+C to Shutdown ---")

    try:
        while True:
            time.sleep(1)
            # Check if brain died
            if brain_process.poll() is not None:
                print("❌ Brain died! Restarting...")
                brain_process = subprocess.Popen(
                    [sys.executable, "src/main.py"],
                    stdout=sys.stdout,
                    stderr=sys.stderr,
                    env=env
                )
    except KeyboardInterrupt:
        print("\n🛑 SHUTTING DOWN JARVIS...")
        brain_process.terminate()
        ui_process.terminate()
        print("👋 Goodbye.")

if __name__ == "__main__":
    main()
