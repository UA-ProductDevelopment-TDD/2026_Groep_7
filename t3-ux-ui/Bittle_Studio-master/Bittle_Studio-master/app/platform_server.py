"""Bittle Platform: http://127.0.0.1:8790. Started by app/platform_launcher.py.

One page to map the surroundings, watch the camera, drive the robot over Bluetooth with a 3D twin that moves along,
and record leg movements. The robot itself is connected in the browser (Web Bluetooth or Web Serial, Chrome or Edge);
this server keeps motions, maps and the motor layout, and reads the camera board over USB.

    python app/platform_server.py [--port 8790] [--lan]

--lan lets teammates on the same network open the page to watch; only this computer can change anything.
"""
import argparse
import ipaddress
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse, Response, StreamingResponse
from fastapi.staticfiles import StaticFiles

import skills
from bittle_platform import camera as vision
from bittle_platform import distance as distances
from bittle_platform import models
from bittle_platform.scan import Scans, summary
from bittle_platform.storage import MODELS, Store
from engine import ASSETS, ROOT

PORT = 8790
store = Store()
camera = vision.VisionCamera()


@asynccontextmanager
async def lifespan(app):
    yield
    camera.disconnect()


app = FastAPI(lifespan=lifespan)


def local(host):
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return host in ('localhost', 'testclient')


@app.middleware('http')
async def guard(request: Request, call_next):
    # Viewers on the network may look; only this computer may change motions, maps, the layout or the camera.
    if request.method not in ('GET', 'HEAD') and not local(request.client.host if request.client else ''):
        return JSONResponse({'detail': 'Alleen de computer waarop het platform draait, kan iets wijzigen'}, 403)
    try:
        response = await call_next(request)
    except ValueError as error:
        return JSONResponse({'detail': str(error)}, 400)
    except KeyError as error:
        return JSONResponse({'detail': f'Niet gevonden: {error.args[0] if error.args else ""}'}, 404)
    if request.url.path == '/' or request.url.path.startswith('/web/'):
        response.headers['Cache-Control'] = 'no-cache'
    return response


@app.get('/')
def index():
    return FileResponse(ROOT / 'web/platform/index.html')


@app.get('/api/info')
def info(request: Request):
    return {'name': 'Bittle Platform', 'can_edit': local(request.client.host if request.client else ''),
            'models': list(MODELS)}


# Robot models, motor layout and Petoi skills

@app.get('/api/models')
def robot_models():
    return models.models()


@app.get('/api/layouts')
def layouts():
    return store.layouts()


@app.put('/api/layouts/{model}')
def put_layout(model: str, body: dict):
    return store.put_layout(model, body)


@app.get('/api/skill')
def skill(command: str, model: str = 'stock'):
    """A Petoi command as joint-angle segments for the twin: {name, segments: [[seconds, {joint: degrees}]], loop_from}."""
    if model not in MODELS:
        raise ValueError('model moet een van deze zijn: ' + ', '.join(MODELS))
    plan = skills.plan(command, store.layouts()[model])
    if plan is None:
        raise KeyError(command)
    return {'name': plan['name'], 'segments': [[seconds, pose] for seconds, pose in plan['segments']],
            'loop_from': plan['loop_from'], 'ease': bool(plan.get('ease'))}


# Motions

@app.get('/api/motions')
def motion_list():
    return store.motions.list()


@app.get('/api/motions/{name}')
def motion(name: str):
    return store.motions.get(name)


@app.put('/api/motions/{name}')
def put_motion(name: str, body: dict):
    return store.motions.put(name, body)


@app.delete('/api/motions/{name}')
def delete_motion(name: str):
    store.motions.delete(name)
    return {'deleted': name}


# Maps

@app.get('/api/maps')
def map_list():
    return store.maps.list()


@app.get('/api/maps/{name}')
def get_map(name: str):
    return store.maps.get(name)


@app.put('/api/maps/{name}')
def put_map(name: str, body: dict):
    return store.maps.put(name, body)


@app.delete('/api/maps/{name}')
def delete_map(name: str):
    store.delete_map(name)
    return {'deleted': name}


@app.put('/api/maps/{name}/background')
async def put_background(name: str, request: Request):
    """The image bytes as the body, its type as Content-Type; answers the file name to put in the map's background."""
    data = await request.body()
    return {'file': store.put_background(name, request.headers.get('content-type', '').split(';')[0], data)}


@app.get('/api/backgrounds/{file}')
def background(file: str):
    return FileResponse(store.get_background(file))


# Settings and turn-and-scan

@app.get('/api/settings')
def settings():
    return {**store.settings(), 'distance_sources': distances.SOURCES}


@app.put('/api/settings')
def put_settings(body: dict):
    return store.put_settings(body)


def scans():
    return Scans(store.root / 'scans')


@app.get('/api/scans')
def scan_list(map: str = ''):
    return scans().list(map or None)


@app.post('/api/scans')
def scan_start(body: dict):
    """Start a scan where the robot stands on a map: {map, x, y, heading}."""
    current = store.settings()
    return summary(scans().create(str(body.get('map') or ''), body, current['camera'], current['distance']))


@app.post('/api/scans/{scan_id}/step')
def scan_step(scan_id: str, body: dict):
    """One step, taken once the robot stands still: a fresh camera frame (if the camera runs), what its model saw,
    the distance sensor, and the turn: {commanded: degrees the body was asked to turn, gyro: degrees measured by the
    robot, neck: the neck angle}."""
    start = time.monotonic()
    jpeg, detections = None, []
    if camera.status()['state'] == 'streaming':
        # The second new frame: the first one may have been taken while the head or body still moved (the board
        # needs a frame's time to take, recognise and send it).
        _, number = camera.latest()
        jpeg, number = camera.wait_frame(number, 2.)
        if jpeg:
            jpeg = camera.wait_frame(number, 2.)[0] or jpeg
        detections = camera.status()['detections'] if jpeg else []
    store_scans = scans()
    scan = store_scans.load(scan_id)
    # The SRF05 on the camera: the readings made meanwhile (about 3), more if they are slow to come.
    samples = camera.distance_since(start) if scan['sensor']['source'] == 'camera' else None
    map_doc = None
    if scan['map']:
        try:
            map_doc = store.maps.get(scan['map'])
        except (KeyError, ValueError):
            map_doc = None
    number_or_none = lambda value: float(value) if isinstance(value, (int, float)) and not isinstance(value, bool) else None
    return store_scans.step(scan_id, jpeg, detections, number_or_none(body.get('commanded')),
                            number_or_none(body.get('gyro')), map_doc, samples, number_or_none(body.get('neck')))


@app.post('/api/scans/{scan_id}/finish')
def scan_finish(scan_id: str):
    return scans().finish(scan_id)


@app.get('/api/scans/{scan_id}')
def scan(scan_id: str):
    return summary(scans().load(scan_id))


@app.get('/api/scans/{scan_id}/files/{name}')
def scan_file(scan_id: str, name: str):
    return FileResponse(scans().file(scan_id, name), headers={'Cache-Control': 'no-cache'})


@app.delete('/api/scans/{scan_id}')
def scan_delete(scan_id: str):
    scans().delete(scan_id)
    return {'deleted': scan_id}


# Camera (Grove Vision AI V2 over USB, or over wifi through the XIAO: port 'wifi://host')

@app.get('/api/camera/ports')
def camera_ports():
    return vision.ports()


@app.get('/api/camera/status')
def camera_status():
    return camera.status()


@app.post('/api/camera/connect')
def camera_connect(body: dict):
    port = str(body.get('port') or '')
    if not port:
        raise ValueError('Kies de poort van het camerabordje')
    camera.connect(port, str(body.get('resolution', '240')))
    return camera.status()


@app.post('/api/camera/disconnect')
def camera_disconnect():
    camera.disconnect()
    return camera.status()


@app.get('/api/camera/frame.jpg')
def camera_frame():
    jpeg, number = camera.latest()
    if jpeg is None:
        raise KeyError('nog geen camerabeeld')
    return Response(jpeg, media_type='image/jpeg', headers={'Cache-Control': 'no-store', 'X-Frame': str(number)})


@app.get('/api/camera/stream')
def camera_stream():
    """Motion JPEG: an <img> shows it as live video. Ends when the camera is disconnected."""
    def frames():
        number = 0
        while camera.port:
            jpeg, number = camera.wait_frame(number, 2.)
            if jpeg is not None:
                yield b'--frame\r\nContent-Type: image/jpeg\r\nContent-Length: ' + str(len(jpeg)).encode() + b'\r\n\r\n'
                yield jpeg + b'\r\n'
    return StreamingResponse(frames(), media_type='multipart/x-mixed-replace; boundary=frame',
                             headers={'Cache-Control': 'no-store'})


app.mount('/web', StaticFiles(directory=ROOT / 'web'), name='web')
app.mount('/assets', StaticFiles(directory=ASSETS), name='assets')
app.mount('/vendor', StaticFiles(directory=ROOT / 'node_modules/three'), name='vendor')


def main():
    parser = argparse.ArgumentParser(description='Serve the Bittle Platform.')
    parser.add_argument('--port', type=int, default=PORT)
    parser.add_argument('--lan', action='store_true', help='let computers on this network open the page (view only)')
    args = parser.parse_args()
    import uvicorn
    uvicorn.run(app, host='0.0.0.0' if args.lan else '127.0.0.1', port=args.port)


if __name__ == '__main__':
    main()
