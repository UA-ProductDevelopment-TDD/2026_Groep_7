"""Coop Guard simulator: local HTTP interface on http://127.0.0.1:8780. Started by app/coop_launcher.py.

/api/coop/... drives the simulation and edits the scenario; /api/hub/... is the module hub that the dashboard and
outside programs (an AI camera model, later an ESP32-S3) use to read topics, publish results and run self-tests.
"""
import json
import threading
import xml.etree.ElementTree as ET
from contextlib import asynccontextmanager

import pybullet as p
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse, Response, StreamingResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.trustedhost import TrustedHostMiddleware

from coop import config, experiments, gaits, traverse
from coop.jobs import Jobs
from coop.session import CoopSession
from engine import ASSETS, DATA, ROOT

PORT = 8780
AUTOSAVE = False  # enabled by the desktop entry point; tests use a fresh default scenario
SESSION_FILE = DATA / 'coop-session.json'
session = None
jobs = Jobs()


def autosave():
    if AUTOSAVE:
        temporary = SESSION_FILE.with_suffix('.tmp')
        temporary.write_text(json.dumps(session.scenario, indent=2), encoding='utf-8')
        temporary.replace(SESSION_FILE)


@asynccontextmanager
async def lifespan(app):
    global session
    scenario = None
    if AUTOSAVE and SESSION_FILE.is_file():
        try:
            scenario = config.validate(json.loads(SESSION_FILE.read_text(encoding='utf-8')))
        except Exception as error:
            print('Could not restore the last coop scenario:', error)
    try:
        session = CoopSession(scenario)
    except Exception as error:
        if scenario is None:
            raise
        print('The last coop scenario could not be built, starting from the default:', error)
        session = CoopSession()
    thread = threading.Thread(target=session.worker, daemon=True)
    thread.start()
    yield
    jobs.close()
    session.close()
    thread.join(2)


app = FastAPI(lifespan=lifespan)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=['127.0.0.1', 'localhost', 'testserver'])


@app.middleware('http')
async def local_only(request: Request, call_next):
    # Browsers send an Origin header: only this page may change the simulation. Local scripts send none.
    origin = request.headers.get('origin')
    if request.method not in ('GET', 'HEAD') and origin and origin != str(request.base_url).rstrip('/'):
        return JSONResponse({'detail': 'Only this local dashboard may change the simulation'}, 403)
    try:
        response = await call_next(request)
    except (ValueError, KeyError, TypeError, ET.ParseError, p.error) as error:
        return JSONResponse({'detail': str(error)}, 400)
    if request.url.path == '/' or request.url.path.startswith('/web/'):
        response.headers['Cache-Control'] = 'no-cache'
    return response


@app.get('/')
def index():
    return FileResponse(ROOT / 'web/coop/index.html')


# Simulation and scenario

@app.get('/api/coop/model')
def model():
    return session.model()


@app.get('/api/coop/state')
def state():
    return session.state()


@app.post('/api/coop/command')
def command(body: dict):
    return session.command(body)


@app.post('/api/coop/traverse-test')
def traverse_test(body: dict):
    return session.traverse_test(float(body.get('seconds', 30)))


@app.get('/api/coop/gait-preview')
def gait_preview(motion: str = 'forward'):
    """The current generated gait drawn from the side: joint angles and hip, knee and foot per frame and leg."""
    with session.lock:
        return gaits.preview(session.robot, session.scenario['robot']['gait'], motion)


@app.get('/api/coop/metrics')
def metrics():
    with session.lock:
        return {'scenario': session.scenario['name'], 'time': session.time,
                'metrics': session.metrics.summary(session.battery.used), 'battery': session.battery.reading()}


# Background jobs: traverse tests and batch experiments in worker processes

@app.post('/api/coop/jobs/traverse')
def traverse_job(body: dict):
    seconds = config.number(body.get('seconds', 30), 'traverse test length', 5, 120, unit='s')
    with session.lock:
        scenario = config.validate(session.scenario)
    runs = [(name, traverse.run_one, (scenario, name, settings, walk, seconds))
            for name, settings, walk in traverse.variants(scenario)]

    def finish(job, results):
        result = traverse.collect(scenario, seconds, [r if r is not None else {'name': run['label'], 'distance': 0.,
                                                                               'error': run.get('error', run['status'])}
                                                      for run, r in zip(job['runs'], results)])
        session.traverse_done(result)
        return result

    return {'job': jobs.submit('traverse', f'Traverse test, {seconds:.0f} s', runs, finish)}


@app.post('/api/coop/jobs/experiment')
def experiment_job(body: dict):
    with session.lock:
        scenario = config.validate(session.scenario)
    planned, seconds = experiments.plan(scenario, body.get('variants'), body.get('seeds', 3), body.get('seconds', 300))
    runs = [(f"{run['variant']} · seed {run['seed'] + 1}", experiments.run_mission,
             (run['scenario'], seconds, run['variant'], run['seed'])) for run in planned]
    names = list(dict.fromkeys(run['variant'] for run in planned))
    title = config.text(body.get('title') or ' vs '.join(names), 'experiment title', 120)
    job = jobs.submit('experiment', title, runs, experiments.summarise,
                      {'variants': names, 'seeds': len(planned) // len(names), 'seconds': seconds,
                       'scenario': scenario['name'], 'changes': body.get('variants')})
    with session.lock:
        session.log(f'Experiment started: {title} ({len(runs)} runs of {seconds:.0f} s)')
    return {'job': job}


@app.get('/api/coop/jobs')
def job_list():
    return jobs.list()


@app.get('/api/coop/jobs/{job_id}')
def job(job_id: str):
    return jobs.get(job_id)


@app.delete('/api/coop/jobs/{job_id}')
def job_cancel(job_id: str):
    jobs.cancel(job_id)
    return jobs.get(job_id)


@app.get('/api/coop/jobs/{job_id}/csv')
def job_csv(job_id: str):
    job = jobs.get(job_id)
    if job['kind'] != 'experiment' or not job['result']:
        raise ValueError('Only a finished experiment has a CSV table')
    return Response(experiments.to_csv(job['result']), media_type='text/csv',
                    headers={'Content-Disposition': f'attachment; filename="experiment-{job_id}.csv"'})


@app.get('/api/coop/scenario')
def scenario():
    with session.lock:
        return session.scenario


@app.put('/api/coop/scenario')
def apply_scenario(body: dict):
    session.apply(body)
    autosave()
    return session.model()


@app.get('/api/coop/default-scenario')
def default_scenario():
    return config.default()


@app.get('/api/coop/scenarios')
def scenarios():
    return config.list_scenarios()


@app.post('/api/coop/scenarios/load')
def load_scenario(body: dict):
    session.apply(config.load_scenario(body['name']))
    autosave()
    return session.model()


@app.post('/api/coop/scenarios/save')
def save_scenario(body: dict):
    with session.lock:
        current = session.scenario
    saved = config.save_scenario(body['name'], current)
    return {'saved': saved, 'scenarios': config.list_scenarios()}


# Module hub

@app.get('/api/hub/modules')
def hub_modules():
    with session.lock:
        return session.hub.modules()


@app.post('/api/hub/modules/{module_id}/test')
def hub_test(module_id: str):
    return session.run_test(module_id)


@app.post('/api/hub/test-all')
def hub_test_all():
    return session.run_test()


@app.get('/api/hub/topics')
def hub_topics(prefix: str = ''):
    return session.hub.latest(prefix)


@app.post('/api/hub/register')
def hub_register(body: dict):
    return session.hub.register_external(body)


@app.post('/api/hub/modules/{module_id}/heartbeat')
def hub_heartbeat(module_id: str):
    return session.hub.heartbeat(module_id)


@app.delete('/api/hub/modules/{module_id}')
def hub_remove(module_id: str):
    session.hub.remove_external(module_id)
    return {'ok': True}


@app.post('/api/hub/publish')
def hub_publish(body: dict):
    return session.hub.publish_external(str(body['module']), body['topic'], body.get('value'))


@app.get('/api/hub/frame/{name}')
def hub_frame(name: str):
    frame = session.hub.frame(name.removesuffix('.png'))
    if frame is None:
        return JSONResponse({'detail': 'No image from that camera yet'}, 404)
    return Response(frame[0], media_type='image/png', headers={'Cache-Control': 'no-store'})


@app.get('/api/hub/stream')
def hub_stream(prefix: str = '', since: int = -1):
    """Server-Sent Events: every hub message whose topic starts with prefix, as it is published."""
    hub = session.hub

    def events():
        sequence = hub.sequence if since < 0 else since
        yield ': connected\n\n'
        while not session.closed:
            current = hub.wait(sequence, 5)
            if current == sequence:
                yield ': keep-alive\n\n'
                continue
            for message in hub.since(sequence, prefix):
                yield 'data: ' + json.dumps(message) + '\n\n'
            sequence = current

    return StreamingResponse(events(), media_type='text/event-stream', headers={'Cache-Control': 'no-cache'})


app.mount('/web', StaticFiles(directory=ROOT / 'web'), name='web')
app.mount('/assets', StaticFiles(directory=ASSETS), name='assets')
app.mount('/data', StaticFiles(directory=DATA), name='data')
app.mount('/vendor', StaticFiles(directory=ROOT / 'node_modules/three'), name='vendor')

if __name__ == '__main__':
    AUTOSAVE = True
    import uvicorn
    uvicorn.run(app, host='127.0.0.1', port=PORT)
