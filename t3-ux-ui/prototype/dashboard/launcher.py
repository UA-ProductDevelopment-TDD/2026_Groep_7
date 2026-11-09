"""One entry point: isolated installation, local server, automatic browser."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import threading
import time
from urllib.request import urlopen
import webbrowser

ROOT=Path(__file__).resolve().parent
VENV=ROOT/'.venv'
PYTHON=VENV/('Scripts/python.exe' if os.name=='nt' else 'bin/python')

def healthy(port):
    try:
        with urlopen(f'http://127.0.0.1:{port}/api/health',timeout=.5) as response:
            return json.load(response).get('app')=='bittle-landlicht'
    except (OSError,ValueError):return False

def prepare():
    if sys.version_info<(3,10):raise RuntimeError('Python 3.10 of nieuwer nodig; Python 3.12 aanbevolen.')
    if not PYTHON.exists():subprocess.run([sys.executable,'-m','venv',str(VENV)],check=True)
    requirements=ROOT/'requirements.txt'
    fingerprint=hashlib.sha256(requirements.read_bytes()).hexdigest()
    stamp=VENV/'.requirements-hash'
    if not stamp.exists() or stamp.read_text()!=fingerprint:
        print('Eenmalige installatie van de lokale dashboardomgeving...',flush=True)
        subprocess.run([str(PYTHON),'-m','pip','install','-r',str(requirements)],check=True)
        stamp.write_text(fingerprint)

def main():
    parser=argparse.ArgumentParser(description='Start het lokale Bittle-dashboard.')
    parser.add_argument('--port',type=int,default=8766)
    parser.add_argument('--no-browser',action='store_true')
    parser.add_argument('--no-reload',action='store_true')
    parser.add_argument('--setup-only',action='store_true')
    args=parser.parse_args()
    if not 1024<=args.port<=65535:raise RuntimeError('Kies een poort tussen 1024 en 65535.')
    prepare()
    if args.setup_only:return
    url=f'http://127.0.0.1:{args.port}'
    if healthy(args.port):
        print('Dashboard draait al: '+url)
        if not args.no_browser:webbrowser.open(url)
        return
    with socket.socket() as probe:
        try:probe.bind(('127.0.0.1',args.port))
        except OSError:raise RuntimeError(f'Poort {args.port} is bezet. Sluit de andere app of kies --port 8767.')
    command=[str(PYTHON),'-m','uvicorn','backend.app:create_app','--factory','--host','127.0.0.1','--port',str(args.port),'--log-level','warning']
    if not args.no_reload:command+=['--reload','--reload-dir',str(ROOT/'backend')]
    print(f'\nBITTLE LANDLICHT\n{url}\nModus: simulatie, geen robot gekoppeld.\nLaat dit venster open. Stop met Ctrl+C.\n',flush=True)
    child=subprocess.Popen(command,cwd=ROOT)
    def open_when_ready():
        for _ in range(80):
            if child.poll() is not None:return
            if healthy(args.port):
                if not args.no_browser:webbrowser.open(url)
                return
            time.sleep(.25)
        print('Start duurt langer dan verwacht. Controleer de meldingen hierboven.',flush=True)
    threading.Thread(target=open_when_ready,daemon=True).start()
    try:return child.wait()
    except KeyboardInterrupt:
        try:child.wait(timeout=6)
        except subprocess.TimeoutExpired:child.terminate();child.wait(timeout=6)
        return 0

if __name__=='__main__':
    try:sys.exit(main())
    except (RuntimeError,subprocess.CalledProcessError,OSError) as e:
        print(f'\nStarten lukt niet: {e}\nZie README.md bij Problemen oplossen.',file=sys.stderr)
        sys.exit(1)
