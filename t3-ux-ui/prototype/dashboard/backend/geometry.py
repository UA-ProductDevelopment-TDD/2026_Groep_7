"""Small 2D mock planner; not suitable for physical robot navigation."""
import heapq
import math

def inside(p, points):
    yes = False
    j = len(points)-1
    for i, a in enumerate(points):
        b = points[j]
        if (a['y']>p['y']) != (b['y']>p['y']) and p['x'] < (b['x']-a['x'])*(p['y']-a['y'])/(b['y']-a['y'])+a['x']:
            yes = not yes
        j = i
    return yes

def blocked(p, project):
    if not (48<=p['x']<=912 and 48<=p['y']<=552):
        return True
    for o in project['objects']:
        if o['type'] in ('door', 'dock'):
            continue
        a = -o['rotation']*math.pi/180
        dx,dy = p['x']-o['x'],p['y']-o['y']
        x,y = dx*math.cos(a)-dy*math.sin(a),dx*math.sin(a)+dy*math.cos(a)
        if abs(x)<o['w']/2+12 and abs(y)<o['h']/2+12:
            return True
    return any(inside(p,z['points']) for z in project['zones'])

def clear(a,b,d):
    n = max(1, math.ceil(math.hypot(a['x']-b['x'],a['y']-b['y'])/5))
    return all(not blocked({'x':a['x']+(b['x']-a['x'])*i/n,'y':a['y']+(b['y']-a['y'])*i/n}, d) for i in range(n+1))

def plan(a,b,d):
    if blocked(a,d) or blocked(b,d): return None
    if clear(a,b,d): return [dict(x=b['x'],y=b['y'])]
    cell=lambda p:(round(p['x']/15),round(p['y']/15))
    point=lambda c:dict(x=c[0]*15,y=c[1]*15)
    start,goal=cell(a),cell(b)
    if not clear(a,point(start),d) or not clear(point(goal),b,d): return None
    queue=[(0,start)];cost={start:0};prev={};closed=set()
    while queue:
        _,u=heapq.heappop(queue)
        if u in closed: continue
        closed.add(u)
        if u==goal: break
        for dx,dy in [(1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)]:
            v=(u[0]+dx,u[1]+dy)
            if not (0<=v[0]<65 and 0<=v[1]<41) or not clear(point(u),point(v),d): continue
            value=cost[u]+math.hypot(dx,dy)
            if value<cost.get(v,math.inf):
                cost[v]=value;prev[v]=u
                heapq.heappush(queue,(value+math.dist(v,goal),v))
    if goal not in closed: return None
    path=[dict(x=b['x'],y=b['y'])];u=goal
    while u!=start:
        path.append(point(u));u=prev[u]
    path.append(point(start));path.reverse()
    result=[];i=0;origin=a
    while i<len(path):
        j=i
        while j+1<len(path) and clear(origin,path[j+1],d): j+=1
        result.append(path[j]);origin=path[j];i=j+1
    return result

def approach(o, project):
    points=[{'x':o['x'],'y':o['y']+o['h']/2+35},{'x':o['x']-o['w']/2-35,'y':o['y']},{'x':o['x']+o['w']/2+35,'y':o['y']},{'x':o['x'],'y':o['y']-o['h']/2-35}]
    return next((p for p in points if not blocked(p,project)),None)
