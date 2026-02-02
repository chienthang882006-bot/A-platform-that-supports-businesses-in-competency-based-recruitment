import os, time, signal, subprocess, sys
import pytest
import requests
from pathlib import Path

BASE_URL = "http://127.0.0.1:8001"

def wait_up(url, timeout=20):
    start = time.time()
    while time.time() - start < timeout:
        try:
            requests.get(url, timeout=1)
            return True
        except Exception:
            time.sleep(0.5)
    return False

@pytest.fixture(scope="session", autouse=True)
def run_server():
    root = Path(__file__).resolve().parents[2]  # .../project_recruitment
    env = os.environ.copy()

    # phòng trường hợp .env thiếu -> app.py sẽ raise RuntimeError
    env.setdefault("FLASK_SECRET_KEY", "test-flask-secret")
    env.setdefault("JWT_SECRET_KEY", "test-jwt-secret")

    proc = subprocess.Popen(
        [sys.executable, "app.py"],
        cwd=str(root),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
    )

    if not wait_up(BASE_URL):
        out, err = proc.communicate(timeout=2)
        proc.terminate()
        raise AssertionError(
            f"Server không lên được ở {BASE_URL}\n=== STDOUT ===\n{out}\n=== STDERR ===\n{err}"
        )

    yield

    proc.send_signal(signal.CTRL_BREAK_EVENT)
    proc.terminate()
