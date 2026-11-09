"""Start the Coop Guard simulator, then open its dashboard once it is ready."""
import subprocess
import sys
import time
import urllib.request
import webbrowser
from pathlib import Path

url = 'http://127.0.0.1:8780'


def ready():
    try:
        with urllib.request.urlopen(url + '/api/coop/state', timeout=1) as response:
            return response.status == 200
    except OSError:
        return False


if ready():
    webbrowser.open(url)
    print('The Coop simulator is already running. Reusing it.')
else:
    process = subprocess.Popen([sys.executable, 'coop_server.py'], cwd=Path(__file__).parent)
    try:
        for _ in range(120):
            if process.poll() is not None:
                raise SystemExit('Server could not start; see the error above.')
            if ready():
                webbrowser.open(url)
                break
            time.sleep(.5)
        else:
            print('Still starting. Open ' + url + ' once the server is ready.')
        process.wait()
    except KeyboardInterrupt:
        process.terminate()
        process.wait()
