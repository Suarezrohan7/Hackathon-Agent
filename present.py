"""One command for the whole video.

    python present.py

Starts the dashboard server, opens the full presentation in your browser, and
holds. The presentation auto-plays: the cinematic intro -> what the project is ->
what has been done -> then the LIVE dashboard, which validates a look-ahead fraud
and a real edge on its own, no clicks.

Record: press F11 for fullscreen, press  r  to restart from the top, then screen-
record. ~4.5 min. Ctrl+C in this terminal when you're done to stop the server.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PORT = 7600
URL = f"http://127.0.0.1:{PORT}/present"


def up() -> bool:
    try:
        urllib.request.urlopen(URL, timeout=1).read(1)
        return True
    except urllib.error.HTTPError:
        return False           # something is answering, but not our route -> stale
    except Exception:
        return False


def free_port() -> None:
    """Kill anything already sitting on the port (usually a stale server without the route)."""
    if os.name != "nt":
        subprocess.run(["bash", "-lc", f"fuser -k {PORT}/tcp"], capture_output=True)
        return
    out = subprocess.run(["netstat", "-ano"], capture_output=True, text=True).stdout
    pids = {m.group(1) for ln in out.splitlines() if f":{PORT} " in ln
            for m in [re.search(r"(\d+)\s*$", ln)] if m}
    for pid in pids:
        subprocess.run(["taskkill", "/F", "/PID", pid], capture_output=True)
    if pids:
        time.sleep(1)


def main() -> None:
    started_here = False
    proc = None
    if up():
        print("dashboard already serving the presentation.")
    else:
        free_port()
        print("starting the dashboard server …")
        proc = subprocess.Popen([sys.executable, str(ROOT / "app.py")], cwd=ROOT,
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        started_here = True
        for _ in range(60):
            if up():
                break
            time.sleep(0.5)
        else:
            print("server did not come up on :7600 — run  python app.py  in another terminal and retry.")
            return

    print()
    print("  presentation:  " + URL)
    print("  F11 fullscreen  ·  press  r  to restart from the top  ·  it auto-plays (~4.5 min)")
    print("  record the browser window; Ctrl+C here when done.")
    print()
    webbrowser.open(URL)

    if not started_here:
        return
    try:
        proc.wait()
    except KeyboardInterrupt:
        print("\nstopping server …")
        proc.terminate()


if __name__ == "__main__":
    main()
