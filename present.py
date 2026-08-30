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

import subprocess
import sys
import time
import urllib.request
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent
URL = "http://127.0.0.1:7600/present"


def up() -> bool:
    try:
        urllib.request.urlopen(URL, timeout=1).read(1)
        return True
    except Exception:
        return False


def main() -> None:
    started_here = False
    proc = None
    if not up():
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
