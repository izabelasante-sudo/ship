"""Run the two Flask apps and MCP server; Ctrl+C stops all three."""

import signal
import subprocess
import sys
import time
from pathlib import Path

BASE = Path(__file__).resolve().parent


def main():
    def stop(signum, frame):
        raise KeyboardInterrupt

    signal.signal(signal.SIGTERM, stop)
    children = []
    try:
        for name in ("mongo_api.py", "redis_api.py", "mcp_server.py"):
            children.append(subprocess.Popen([sys.executable, "-u", str(BASE / name)], cwd=BASE))
        print("Flask: 5001 and 5002; MCP: http://127.0.0.1:5000/mcp", flush=True)
        print("Press Ctrl+C to stop all three services.", flush=True)
        while True:
            for child in children:
                if child.poll() is not None:
                    raise RuntimeError(f"A service exited with code {child.returncode}")
            time.sleep(0.5)
    except KeyboardInterrupt:
        pass
    finally:
        for child in children:
            if child.poll() is None:
                child.terminate()
        for child in children:
            try:
                child.wait(timeout=5)
            except subprocess.TimeoutExpired:
                child.kill()
                child.wait()


if __name__ == "__main__":
    main()
