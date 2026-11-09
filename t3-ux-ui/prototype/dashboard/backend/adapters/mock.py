"""Mock robot. No serial, Bluetooth, camera network or firmware access."""
import math
import time
from ..geometry import plan, approach, blocked

class MockAdapter:
    source='mock'
    def __init__(self, project, store):
        self.project=project;self.store=store
        self.pose={'x':300.,'y':420.,'heading':0.}
        self.mode='paused';self.path=[];self.moving=False;self.connected=True
        self.battery=78;self.door='closed';self.camera=True
        self.route=None;self.route_index=0;self.active=None;self.resume_mode=None;self.check_left=0
        self.telemetry_at=int(time.time()*1000)
        self.set_project(project)

    def set_project(self, project):
        self.cancel('Kaart gewijzigd.')
        self.project=project;self.mode='paused';self.path=[];self.resume_mode=None
        if blocked(self.pose,project):
            free=next(({'x':x,'y':y} for x in range(75,900,30) for y in range(75,540,30) if not blocked({'x':x,'y':y},project)),None)
            if free: self.pose.update(free)
            else: self.mode='blocked'

    def result(self, command, status, message):
        result={'id':command['id'],'action':command['action'],'status':status,'message':message,'source':self.source,'time':int(time.time()*1000)}
        self.store.save_command(command,result)
        return result

    def cancel(self, why):
        self.moving=False
        if self.active:
            self.result(self.active,'cancelled',why)
            self.active=None

    def finish(self, message):
        self.moving=False
        if self.active:
            self.result(self.active,'completed',message)
            self.store.event(message,'Simulator')
            self.active=None

    def execute(self, command):
        existing=self.store.command(command['id'])
        if existing:
            if existing[0]!=command: raise ValueError('Opdracht-ID al gebruikt voor een andere actie.')
            return existing[1]
        action=command['action']
        if not self.connected:
            return self.result(command,'failed','Geen verbinding met de simulator; actie niet bevestigd.')
        if action=='stop':
            self.cancel('Onderbroken door stop.');self.mode='stopped';self.path=[];self.resume_mode=None
            self.store.event('Bittle gestopt','Simulator')
            return self.result(command,'completed','Stop bevestigd door simulator.')
        if action=='pause':
            self.resume_mode=self.mode if self.moving else self.resume_mode
            self.moving=False
            if self.mode!='checking': self.mode='paused'
            return self.result(command,'completed','Pauze bevestigd door simulator.')
        if action=='resume':
            if not self.path or not self.resume_mode: return self.result(command,'failed','Geen gepauzeerde route om te hervatten.')
            self.mode=self.resume_mode;self.moving=True
            return self.result(command,'completed','Patrouille hervat.')
        if action=='patrol':
            route=next((r for r in self.project['routes'] if r['id']==command.get('route_id')),None)
            if route is None: route=next(iter(self.project['routes']),None)
            if not route: return self.result(command,'failed','Teken eerst een route.')
            target=route['points'][0]
        else:
            kind={'dock':'dock','eggs':'nest','water':'water'}[action]
            obj=next((o for o in self.project['objects'] if o['type']==kind),None)
            if not obj: return self.result(command,'failed','Onderdeel ontbreekt op de kaart.')
            target=obj if action=='dock' else approach(obj,self.project)
        path=plan(self.pose,target,self.project) if target else None
        if not path: return self.result(command,'failed','Geen vrije route naar het doel.')
        self.cancel('Vervangen door een nieuwe opdracht.')
        self.path=path;self.mode=action;self.moving=True;self.active=command;self.resume_mode=action
        if action=='patrol': self.route=route;self.route_index=0
        self.store.event({'patrol':'Patrouille gestart','dock':'Terug naar dock','eggs':'Eiercontrole gestart','water':'Watercontrole gestart'}[action],'Simulator')
        return self.result(command,'accepted','Opdracht geaccepteerd; uitvoering gestart.')

    def tick(self, seconds):
        if not self.connected: return
        self.telemetry_at=int(time.time()*1000)
        if self.mode=='checking':
            self.check_left-=seconds
            if self.check_left<=0:
                self.mode='done';self.finish('Controlebezoek afgerond (geen sensorcontrole)')
            return
        if not self.moving or not self.path: return
        q=self.path[0];dx=q['x']-self.pose['x'];dy=q['y']-self.pose['y'];distance=math.hypot(dx,dy)
        step=min(distance,38*seconds)
        if distance>0:
            self.pose['x']+=dx/distance*step;self.pose['y']+=dy/distance*step
            desired=math.atan2(dy,dx);delta=(desired-self.pose['heading']+math.pi)%(2*math.pi)-math.pi
            self.pose['heading']+=delta*min(1,seconds*9)
        if distance<=1:
            self.path.pop(0)
            if self.path: return
            if self.mode=='patrol':
                self.route_index+=1
                if self.route_index>=len(self.route['points']):
                    if not self.route['closed']:
                        self.mode='done';self.finish('Patrouille afgerond');return
                    self.route_index=0
                path=plan(self.pose,self.route['points'][self.route_index],self.project)
                if path is None:
                    if self.active:self.result(self.active,'failed','Volgend routepunt is niet bereikbaar.')
                    self.active=None;self.moving=False;self.mode='blocked'
                else:self.path=path
            elif self.mode=='dock':self.mode='docked';self.finish('Bittle bij het dock')
            else:self.mode='checking';self.moving=False;self.check_left=2.5

    def scenario(self, name):
        if name=='offline':
            self.cancel('Verbinding verloren in simulator.');self.path=[];self.connected=False;self.mode='offline'
        elif name=='normal':
            self.connected=True;self.battery=78;self.door='closed';self.camera=True
            if self.mode=='offline':self.mode='paused'
            self.telemetry_at=int(time.time()*1000)
        elif name=='low-battery':self.battery=12
        elif name=='door-open':self.door='open'
        elif name=='camera-off':self.camera=False
        elif name=='fox':self.store.event('Vos gedetecteerd','Testscenario · geen echte detectie')
        self.store.event('Testscenario gewijzigd',name)

    def snapshot(self):
        return {'schema_version':1,'source':self.source,'connected':self.connected,'observed_at':self.telemetry_at,
                'pose':dict(self.pose) if self.connected else None,'coordinates':'canvas-units','mode':self.mode,
                'moving':self.moving,'can_resume':bool(self.path and self.resume_mode),'route_name':self.route['name'] if self.route else None,
                'battery_percent':self.battery if self.connected else None,'door':self.door if self.connected else None,
                'camera':{'status':'test' if self.camera and self.connected else 'unavailable','frame_url':'/api/camera/frame' if self.camera and self.connected else None},
                'servos':[],'capabilities':{'navigation':True,'camera':'generated-test-image','servo_read':False,'servo_write':False},
                'commands':self.store.recent_commands()}

    def shutdown(self):self.cancel('Lokale server gestopt.')
