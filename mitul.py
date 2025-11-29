import subprocess
import time
import sys
import os
import signal

def run_command(command, cwd=None, background=False):
    """Run a shell command."""
    print(f"🚀 Running: {command}")
    if background:
        return subprocess.Popen(command, shell=True, cwd=cwd, preexec_fn=os.setsid)
    else:
        return subprocess.run(command, shell=True, cwd=cwd)

def main():
    print("⚡ Jarvis Crypto: God Mode Launcher ⚡")
    print("---------------------------------------")

    # 1. Verify/Fetch History (Blocking)
    print("\n[1/3] 📚 Verifying Historical Data Foundation...")
    # We use the verify script but maybe limit it or just ensure DB exists?
    # For now, let's run it. If it takes too long, user can interrupt, but it's safer to run.
    # Actually, verify_deep_history fetches 2024 data. Let's assume user ran it or we run it quickly.
    # To avoid long wait on every run, let's skip if DB exists and is large enough?
    # For simplicity and robustness, we run it.
    run_command("python scripts/verify_deep_history.py")

    # 2. Start The Brain (Background)
    print("\n[2/3] 🧠 Starting Main Brain (Autonomous Agent)...")
    brain_process = run_command("python src/main.py", background=True)
    
    # 3. Start The UI (Background/Foreground)
    print("\n[3/3] 🖥️  Launching Live Brain Scan (Dashboard)...")
    # We run streamlit in background so we can keep this script alive to monitor/kill
    ui_process = run_command("streamlit run src/dashboard/app.py", background=True)

    print("\n✅ SYSTEM ONLINE. Press Ctrl+C to Shutdown.")
    print("---------------------------------------")

    try:
        while True:
            time.sleep(1)
            # Check if processes are still alive
            if brain_process.poll() is not None:
                print("❌ Main Brain died! Shutting down...")
                break
            if ui_process.poll() is not None:
                print("❌ UI died! Shutting down...")
                break
    except KeyboardInterrupt:
        print("\n🛑 Shutting down Jarvis...")
    finally:
        # Kill processes group
        if brain_process:
            os.killpg(os.getpgid(brain_process.pid), signal.SIGTERM)
        if ui_process:
            os.killpg(os.getpgid(ui_process.pid), signal.SIGTERM)
        print("👋 Goodbye.")

if __name__ == "__main__":
    main()
