import json,math
exec(open('map1.py').read().split("F={f['id']")[0])
C=o['circ']
lab={}
for k,l in L.items():
    if l['txt'] in NAME2ID: lab[NAME2ID[l['txt']]]=(l['x'],l['y'])
seats={p['id']:p['s'] for p in j['prov']}
asg={}
for i,c in enumerate(C):
    best=None
    for pid,(x,y) in lab.items():
        dy=c['cy']-y
        if dy<0: continue
        d=math.hypot((c['cx']-x)*0.6,dy-12)
        if best is None or d<best[0]: best=(d,pid)
    pid_=best[1]
    if c['cx']>=436 and 110<c['cy']<140: pid_='08'
    asg.setdefault(pid_,[]).append(i)
bad=[(p,len(asg.get(p,[])),seats[p]) for p in seats if len(asg.get(p,[]))!=seats[p]]
print(bad)
json.dump(asg,open('asg.json','w'))
