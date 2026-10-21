"""
Financial News Intelligence Platform — Single Entry Point.

Starts both the FastAPI backend and the Streamlit dashboard
with a single command: `python run.py`

Press Ctrl+C to stop both processes gracefully.
"""

import subprocess
import sys
import os
import signal
import time

# Ensure project root is the working directory
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(PROJECT_ROOT)

# Add to PYTHONPATH so imports work
env = os.environ.copy()
existing_pythonpath = env.get("PYTHONPATH", "")
env["PYTHONPATH"] = PROJECT_ROOT + (os.pathsep + existing_pythonpath if existing_pythonpath else "")


def main():
    print("=" * 60)
    print("  Financial News Intelligence Platform")
    print("=" * 60)
    print()
    print("  Starting services...")
    print()

    processes = []

    try:
        # 1. Start FastAPI backend
        print("  [1/2] Starting FastAPI backend on http://127.0.0.1:8000")
        fastapi_cmd = [
            sys.executable, "-m", "uvicorn",
            "backend.main:app",
            "--host", "127.0.0.1",
            "--port", "8000",
            "--log-level", "info",
        ]
        fastapi_proc = subprocess.Popen(
            fastapi_cmd,
            env=env,
            cwd=PROJECT_ROOT,
        )
        processes.append(("FastAPI", fastapi_proc))

        # Give FastAPI a moment to start
        time.sleep(3)

        # 2. Start Streamlit dashboard
        print("  [2/2] Starting Streamlit dashboard on http://localhost:8501")
        streamlit_cmd = [
            sys.executable, "-m", "streamlit", "run",
            os.path.join("dashboard", "app.py"),
            "--server.port", "8501",
            "--server.headless", "true",
            "--browser.gatherUsageStats", "false",
        ]
        streamlit_proc = subprocess.Popen(
            streamlit_cmd,
            env=env,
            cwd=PROJECT_ROOT,
        )
        processes.append(("Streamlit", streamlit_proc))

        print()
        print("  [OK] All services started successfully!")
        print()
        print("  Dashboard:  http://localhost:8501")
        print("  API:        http://127.0.0.1:8000")
        print("  API Docs:   http://127.0.0.1:8000/docs")
        print()
        print("  Press Ctrl+C to stop all services.")
        print("=" * 60)

        # Wait for either process to exit
        while True:
            for name, proc in processes:
                retcode = proc.poll()
                if retcode is not None:
                    print(f"\n  [!] {name} exited with code {retcode}")
                    raise KeyboardInterrupt
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n  Shutting down...")

        for name, proc in processes:
            if proc.poll() is None:
                print(f"  Stopping {name}...")
                proc.terminate()
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait()

        print("  [OK] All services stopped.")
        print()


if __name__ == "__main__":
    main()
