"""Start the Bittle Platform, then open it in the browser once it is ready.

    python app/platform_launcher.py [--lan]

--lan lets teammates on the same network open the page to watch (view only).
"""
import subprocess
import sys
import time
import urllib.request
import webbrowser
from pathlib import Path

url = 'http://127.0.0.1:8790'


def ready():
    try:
        with urllib.request.urlopen(url + '/api/info', timeout=1) as response:
            return response.status == 200
    except OSError:
        return False


if ready():
    webbrowser.open(url)
    print('Het Bittle Platform draait al. Het wordt opnieuw geopend.')
else:
    extra = ['--lan'] if '--lan' in sys.argv[1:] else []
    process = subprocess.Popen([sys.executable, 'platform_server.py', *extra], cwd=Path(__file__).parent)
    try:
        for _ in range(120):
            if process.poll() is not None:
                raise SystemExit('De server kon niet starten; zie de fout hierboven.')
            if ready():
                webbrowser.open(url)
                break
            time.sleep(.5)
        else:
            print('Nog bezig met starten. Open ' + url + ' zodra de server klaar is.')
        process.wait()
    except KeyboardInterrupt:
        process.terminate()
        process.wait()
