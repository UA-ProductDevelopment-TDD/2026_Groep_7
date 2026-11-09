import copy
import json
import math
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from backend.app import create_app
from backend.geometry import plan, clear

@pytest.fixture
def client(tmp_path):
    app=create_app(tmp_path)
    with TestClient(app) as c:
        c.headers['x-local-token']=c.get('/api/bootstrap').json()['token']
        yield c

def command(c, action, id='test-command'):
    return c.post('/api/commands',json={'id':id,'action':action}).json()

def test_bootstrap_and_static_scope(client):
    b=client.get('/api/bootstrap').json()
    assert b['telemetry']['source']=='mock'
    assert b['telemetry']['servos']==[]
    assert client.get('/').status_code==200
    assert client.get('/dashboard.css').status_code==200
    assert client.get('/requirements.txt').status_code==404
    assert client.get('/.runtime/dashboard.sqlite3').status_code==404
    assert client.get('/api/health').json()['hardware_enabled'] is False

def test_persistence_and_revision(tmp_path):
    app=create_app(tmp_path)
    with TestClient(app) as c:
        b=c.get('/api/bootstrap').json();c.headers['x-local-token']=b['token']
        b['project']['eggs']=7
        saved=c.put('/api/project',json={'project':b['project'],'revision':b['revision']})
        assert saved.status_code==200
        assert c.put('/api/project',json={'project':b['project'],'revision':b['revision']}).status_code==409
    with TestClient(create_app(tmp_path)) as c:
        b=c.get('/api/bootstrap').json()
        assert b['project']['eggs']==7
        assert b['telemetry']['mode']=='paused'

def test_reject_bad_map(client):
    b=client.get('/api/bootstrap').json();p=b['project']
    p['objects'].append(copy.deepcopy(p['objects'][0]))
    assert client.put('/api/project',json={'project':p,'revision':b['revision']}).status_code==422
    p['objects'].pop();p['routes'][0]['points'][0]['x']=90000
    assert client.put('/api/project',json={'project':p,'revision':b['revision']}).status_code==422

def test_mutation_origin_and_token(client):
    payload={'id':'evil','action':'patrol'}
    assert client.post('/api/commands',json=payload,headers={'origin':'https://foreign.example'}).status_code==403
    assert client.post('/api/commands',json=payload,headers={'x-local-token':'invalid'}).status_code==403

def test_pause_resume_and_stop(client):
    assert command(client,'patrol')['status']=='accepted'
    adapter=client.app.state.adapter
    p=dict(adapter.pose);adapter.tick(.5)
    assert adapter.pose!=p
    assert command(client,'pause','pause')['status']=='completed'
    p=dict(adapter.pose);adapter.tick(.5);assert adapter.pose==p
    assert command(client,'resume','resume')['status']=='completed'
    assert adapter.moving
    assert command(client,'stop','stop')['status']=='completed'
    assert not adapter.moving
    assert adapter.snapshot()['mode']=='stopped'
    assert client.app.state.store.command('test-command')[1]['status']=='cancelled'

def test_duplicate_command_id(client):
    first=command(client,'patrol')
    assert command(client,'patrol')==first
    assert client.post('/api/commands',json={'id':'test-command','action':'dock'}).status_code==409

def test_offline_and_recovery(client):
    command(client,'patrol')
    client.post('/api/simulator/scenario',json={'name':'offline'})
    assert command(client,'stop','offline-stop')['status']=='failed'
    assert client.app.state.adapter.snapshot()['battery_percent'] is None
    assert client.get('/api/camera/frame').status_code==503
    client.post('/api/simulator/scenario',json={'name':'normal'})
    assert not client.app.state.adapter.moving
    assert client.app.state.adapter.mode=='paused'

def test_dock_moves_then_completes(client):
    assert command(client,'dock')['status']=='accepted'
    adapter=client.app.state.adapter
    assert adapter.mode=='dock'
    for _ in range(3000):
        adapter.tick(.1)
        if adapter.mode=='docked':break
    assert adapter.mode=='docked'
    assert client.app.state.store.command('test-command')[1]['status']=='completed'

def test_egg_check_does_not_invent_count(client):
    before=client.get('/api/project').json()['project']['eggs']
    assert command(client,'eggs')['status']=='accepted'
    for _ in range(3000):client.app.state.adapter.tick(.1)
    assert client.app.state.adapter.mode=='done'
    assert client.get('/api/project').json()['project']['eggs']==before

def test_unreachable_goal(client):
    adapter=client.app.state.adapter
    dock=next(o for o in adapter.project['objects'] if o['type']=='dock')
    dock['x'],dock['y']=510,290
    assert command(client,'dock')['status']=='failed'

def test_websocket_and_camera(client):
    with client.websocket_connect('/api/telemetry') as ws:
        msg=ws.receive_json()
        assert msg['type']=='telemetry'
        assert msg['data']['source']=='mock'
    response=client.get('/api/camera/frame')
    assert response.status_code==200
    assert 'TESTBEELD' in response.text

def test_frontend_reload_hashes(client):
    r=client.get('/api/dev/revision').json()
    assert set(r)=={'css','js','html'}
    assert all(len(x)==16 for x in r.values())
