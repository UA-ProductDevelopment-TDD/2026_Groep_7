"""Local-only FastAPI app with a replaceable adapter and durable project state."""
import asyncio
import hashlib
import json
import os
import secrets
import time
from contextlib import asynccontextmanager, suppress
from pathlib import Path
from urllib.parse import urlparse
from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, Response, JSONResponse
from starlette.middleware.trustedhost import TrustedHostMiddleware
from .models import Project, SaveProject, Command, Scenario
from .storage import Store, Conflict
from .adapters.mock import MockAdapter

ROOT=Path(__file__).resolve().parents[1]
WEB=ROOT/'web'

def assets():
    groups={}
    for suffix in ('css','js','html'):
        h=hashlib.sha256()
        for f in sorted(WEB.glob('*.'+suffix)):
            h.update(f.name.encode());h.update(f.read_bytes())
        groups[suffix]=h.hexdigest()[:16]
    return groups

def create_app(db_path=None):
    seed=Project.model_validate_json((ROOT/'backend'/'seed.json').read_text(encoding='utf-8-sig')).model_dump()
    store=Store(Path(db_path or os.environ.get('BITTLE_DATA_DIR',ROOT/'.runtime')) / 'dashboard.sqlite3',seed)
    store.interrupt_pending()
    adapter=MockAdapter(store.read()['project'],store)
    token=secrets.token_urlsafe(32)
    async def ticker():
        while True:
            adapter.tick(.05)
            await asyncio.sleep(.05)
    @asynccontextmanager
    async def lifespan(app):
        task=asyncio.create_task(ticker())
        yield
        task.cancel()
        with suppress(asyncio.CancelledError):await task
        adapter.shutdown()
    app=FastAPI(title='Bittle Landlicht lokaal',version='1.0',lifespan=lifespan,docs_url=None,redoc_url=None)
    app.state.store=store;app.state.adapter=adapter
    app.add_middleware(TrustedHostMiddleware,allowed_hosts=['127.0.0.1','localhost','testserver'])

    def same_origin(origin, host):
        return origin is None or origin in ('http://'+host,'https://'+host)

    @app.middleware('http')
    async def local_guard(request,call_next):
        if request.method in ('POST','PUT','DELETE','PATCH'):
            if not same_origin(request.headers.get('origin'),request.headers.get('host','')) or request.headers.get('x-local-token')!=token:
                return JSONResponse({'detail':'Alleen het lokale dashboard mag wijzigingen sturen.'},status_code=403)
            if int(request.headers.get('content-length','0') or 0)>500000:
                return JSONResponse({'detail':'Bestand te groot.'},status_code=413)
        response=await call_next(request)
        response.headers['Cache-Control']='no-store'
        response.headers['X-Content-Type-Options']='nosniff'
        return response

    @app.get('/api/health')
    async def health():return {'app':'bittle-landlicht','status':'ok','source':'mock','hardware_enabled':False}

    @app.get('/api/bootstrap')
    async def bootstrap():return {**store.read(),'events':store.events(),'telemetry':adapter.snapshot(),'token':token,'assets':assets()}

    @app.get('/api/project')
    async def get_project():return {**store.read(),'events':store.events()}

    @app.put('/api/project')
    async def save_project(payload:SaveProject):
        project=payload.project.model_dump()
        old=store.read()['project']
        try:revision=store.save(project,payload.revision)
        except Conflict as e:raise HTTPException(409,str(e))
        terrain_changed=any(old[k]!=project[k] for k in ('objects','routes','zones'))
        if terrain_changed:
            adapter.set_project(project);store.event('Terrein opgeslagen','Lokaal')
        else:adapter.project=project
        if old['eggs']!=project['eggs']:store.event('Eieren bijgewerkt',str(project['eggs'])+' eieren · handmatig')
        return {'revision':revision,'events':store.events()}

    @app.post('/api/commands')
    async def command(payload:Command):
        try:return adapter.execute(payload.model_dump())
        except ValueError as e:raise HTTPException(409,str(e))

    @app.post('/api/simulator/scenario')
    async def scenario(payload:Scenario):
        adapter.scenario(payload.name)
        return adapter.snapshot()

    @app.get('/api/dev/revision')
    async def revision():return assets()

    @app.websocket('/api/telemetry')
    async def telemetry(ws:WebSocket):
        if not same_origin(ws.headers.get('origin'),ws.headers.get('host','')):
            await ws.close(code=1008);return
        await ws.accept()
        try:
            while True:
                await ws.send_json({'type':'telemetry','data':adapter.snapshot(),'revision':store.read()['revision'],'events':store.events()})
                await asyncio.sleep(.1)
        except (WebSocketDisconnect,RuntimeError,OSError):pass

    @app.get('/api/camera/frame')
    async def camera():
        if not adapter.camera or not adapter.connected:raise HTTPException(503,'Testbeeld niet beschikbaar.')
        x=110+int(time.monotonic()*12)%350
        stamp=time.strftime('%H:%M:%S')
        svg=f'''<svg xmlns="http://www.w3.org/2000/svg" width="640" height="360" viewBox="0 0 640 360"><defs><linearGradient id="sky" x2="0" y2="1"><stop stop-color="#d4dfc2"/><stop offset="1" stop-color="#98ad85"/></linearGradient></defs><rect width="640" height="360" fill="url(#sky)"/><path d="M0 170Q140 120 330 190T640 160V360H0" fill="#81966a"/><path d="M0 260Q280 180 640 260V360H0" fill="#617d50"/><rect x="340" y="120" width="170" height="140" fill="#c6b686"/><path d="M320 120L425 65 530 120" fill="#4e6547"/><rect x="408" y="193" width="40" height="67" fill="#687d4c"/><rect x="365" y="150" width="25" height="30" fill="#d6e2c9"/><ellipse cx="{x}" cy="290" rx="16" ry="12" fill="#ebe2c3"/><circle cx="{x+13}" cy="280" r="7" fill="#ebe2c3"/><path d="M{x+16} 276l5 4-5 2" fill="#c69353"/><rect x="16" y="16" width="144" height="27" rx="5" fill="#293d30"/><text x="28" y="34" font-family="sans-serif" font-size="12" fill="#f2efdf">SIMULATIE · TESTBEELD</text><text x="560" y="336" font-family="sans-serif" font-size="12" fill="#f2efdf">{stamp}</text></svg>'''
        return Response(svg,media_type='image/svg+xml')

    @app.get('/')
    async def index():return FileResponse(WEB/'index.html')

    @app.get('/{name}')
    async def static(name:str):
        target=(WEB/name).resolve()
        if target.parent!=WEB.resolve() or target.suffix not in ('.js','.css','.html','.svg') or not target.is_file():raise HTTPException(404)
        return FileResponse(target)
    return app
