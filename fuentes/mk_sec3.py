import shapefile, json, glob, os, math, sys, collections, warnings
warnings.filterwarnings('ignore')
from shapely.geometry import shape
from shapely.ops import unary_union
from shapely.validation import make_valid
Y = sys.argv[1]
OUT = '/tmp/w/out3/mapas/sec/' + Y
os.makedirs(OUT, exist_ok=True)
D = {'2001': 'sec2001', '2004': 'sec2004', '2008': 'sec2008', '2011': 'sec2011', '2015': 'sec2015', '2016': 'sec2016', '2019': 'sec2019', '2023': 'sec23'}[Y]
byp = collections.defaultdict(lambda: collections.defaultdict(list))
for f in glob.glob(f'/tmp/w/{D}/**/*.shp', recursive=True):
    r = shapefile.Reader(f, encoding='latin1'); names = [x[0] for x in r.fields[1:]]
    for sr in r.iterShapeRecords():
        d = dict(zip(names, sr.record)); g = shape(sr.shape.__geo_interface__)
        if g.is_empty: continue
        if not g.is_valid: g = make_valid(g)
        if 'CUSEC' in d: p = d['CPRO']; key = d['CMUN'] + d['CDIS'] + d['CSEC']
        else:
            pm = (d['PROVMUN'] or '').strip()
            if len(pm) != 5 or not pm.isdigit(): continue
            p = pm[:2]; key = pm[2:] + d['DISTRITO'].zfill(2) + d['SECCION'].zfill(3)
        byp[p][key].append(g)
def rings(g):
    if g.geom_type == 'Polygon': return [g]
    if g.geom_type in ('MultiPolygon', 'GeometryCollection'): return [x for p in g.geoms for x in rings(p)]
    return []
def rings(g):
    if g.geom_type == 'Polygon': return [g]
    if g.geom_type in ('MultiPolygon', 'GeometryCollection'): return [x for p in g.geoms for x in rings(p)]
    return []
import numpy as np, shapely
TOL = float(sys.argv[2]) if len(sys.argv) > 2 else 2.5
UNIT = float(sys.argv[3]) if len(sys.argv) > 3 else 2.0
ONLY = sys.argv[4].split(',') if len(sys.argv) > 4 else None
buckets = collections.defaultdict(dict); n = 0; tot = 0
for p, dd in sorted(byp.items()):
    if ONLY and p not in ONLY: continue
    keys = list(dd.keys()); geoms = []
    for key in keys:
        gs = dd[key]; g = gs[0] if len(gs) == 1 else unary_union(gs)
        if not g.is_valid: g = make_valid(g)
        geoms.append(g)
    n += len(keys)
    simp = [None] * len(geoms); bym = collections.defaultdict(list)
    for i, k in enumerate(keys): bym[k[:3]].append(i)
    for m, idx in bym.items():
        ar = sorted(geoms[i].area for i in idx); med = ar[len(ar) // 2]
        tol = min(TOL * 8, max(TOL, math.sqrt(med) * 0.02))
        try:
            r = list(shapely.coverage_simplify(np.array([geoms[i] for i in idx], dtype=object), tol))
        except Exception:
            r = [geoms[i].simplify(tol, preserve_topology=True) for i in idx]
        for i, g in zip(idx, r): simp[i] = g
    allb = [g.bounds for g in geoms]
    x0 = min(b[0] for b in allb); y1 = max(b[3] for b in allb); x1 = max(b[2] for b in allb); y0 = min(b[1] for b in allb)
    sc = 1.0 / UNIT; out = []
    for key, g0, g in zip(keys, geoms, simp):
        if g is None or g.is_empty: g = g0
        R = rings(g); d = ''
        for poly in R:
            if poly.area * sc * sc < 1.5 and len(R) > 1: continue
            for ring in [poly.exterior] + list(poly.interiors):
                pts = [(round((x - x0) * sc), round((y1 - y) * sc)) for x, y in ring.coords[:-1]]
                q = [pts[0]]
                for a in pts[1:]:
                    if a != q[-1]: q.append(a)
                if len(q) < 3: continue
                d += 'M%d %dl' % q[0] + ' '.join('%d %d' % (b[0] - a[0], b[1] - a[1]) for a, b in zip(q, q[1:])) + 'z'
        out.append([key, d])
    W = round((x1 - x0) * sc); H = round((y1 - y0) * sc)
    buckets[int(p) // 9][p] = dict(w=W, h=H, s=out)
for k, d in buckets.items():
    s = json.dumps(d, separators=(',', ':')); tot += len(s)
    rel = f'mapas/sec/{Y}/b{k}.json'
    open(f'{OUT}/b{k}.json.js', 'w').write('(window.__J=window.__J||{})[%s]=%s;' % (json.dumps(rel), s))
print(Y, 'secciones', n, 'MB', round(tot / 1e6, 2))
