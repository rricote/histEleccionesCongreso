import shapefile, json, glob, os, math, sys, collections
from shapely.geometry import shape
from shapely.validation import make_valid
f=glob.glob('/tmp/w/sec23/**/*.shp',recursive=True)[0]
r=shapefile.Reader(f,encoding='utf8')
names=[x[0] for x in r.fields[1:]]
byp=collections.defaultdict(list); n=0
for sr in r.iterShapeRecords():
    d=dict(zip(names,sr.record)); g=shape(sr.shape.__geo_interface__)
    if not g.is_valid: g=make_valid(g)
    byp[d['CPRO']].append((d['CMUN'],d['CDIS']+d['CSEC'],g)); n+=1
print(n,len(byp))
OUT='/tmp/w/site/mapas'; os.makedirs(OUT,exist_ok=True)
# claves de datos
import glob as G
dat={}
for fn in G.glob('/tmp/w/site/datos/2023-07/prov_*.json'):
    d=json.load(open(fn)); dat[d['p']]={(m[0],s[0]) for m in d['m'] for s in m[6]}
tot=0;miss=[];extra=[]
def rings(g):
    if g.geom_type=='Polygon': return [g]
    if g.geom_type in('MultiPolygon','GeometryCollection'): return [x for p in g.geoms for x in rings(p)]
    return []
for p,L in sorted(byp.items()):
    allb=[g.bounds for _,_,g in L]
    x0=min(b[0] for b in allb);y1=max(b[3] for b in allb);x1=max(b[2] for b in allb);y0=min(b[1] for b in allb)
    sc=3000/max(x1-x0,y1-y0)
    keys=set();out=[]
    for m,cs,g in L:
        keys.add((m,cs))
        tol=min(60,max(4,math.sqrt(g.area)*0.02))
        gs=g.simplify(tol,preserve_topology=True)
        if gs.is_empty: gs=g
        d=''
        for poly in rings(gs):
            if poly.area*sc*sc<1.5 and len(rings(gs))>1: continue
            for ring in [poly.exterior]+list(poly.interiors):
                pts=[(round((x-x0)*sc),round((y1-y)*sc)) for x,y in ring.coords[:-1]]
                q=[pts[0]]
                for a in pts[1:]:
                    if a!=q[-1]: q.append(a)
                if len(q)<3: continue
                d+='M%d %dl'%q[0]+' '.join('%d %d'%(b[0]-a[0],b[1]-a[1]) for a,b in zip(q,q[1:]))+'z'
        out.append([m+cs,d])
    miss+=[(p,)+k for k in dat[p]-keys]; extra+=[(p,)+k for k in keys-dat[p]]
    W=round((x1-x0)*sc);H=round((y1-y0)*sc)
    js=json.dumps(dict(w=W,h=H,s=out),separators=(',',':'))
    open(f'{OUT}/sec_{p}.json','w').write(js); tot+=len(js)
print('MB',tot/1e6,'datos sin polígono',len(miss),miss[:10],'polígonos sin datos',len(extra),extra[:10])
