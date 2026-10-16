import sys, os, json, shutil, collections
import numpy as np
sys.path.insert(0, '/tmp/w/build')
import build_elec as B
from groups_cfg import groups_for
OUT = '/tmp/w/out'
M23 = {k: v['name'] for k, v in {}.items()}
# nombres de municipio de 2023 (unificados)
_M23 = {}
for l in B.rdf('2023-07', '05'):
    if l[16:18] == '99': _M23[l[11:13] + l[13:16]] = B.fixname(l[18:118])
def js(path, obj):
    os.makedirs(os.path.dirname(f'{OUT}/{path}'), exist_ok=True)
    s = json.dumps(obj, ensure_ascii=False, separators=(',', ':'))
    open(f'{OUT}/{path}.js', 'w', encoding='utf8').write('(window.__J=window.__J||{})[%s]=%s;' % (json.dumps(path), s))
    return len(s)
def bucket(pid): return int(pid) // 9

def write(e):
    r = B.build(e); NP = r['NP']; parties = r['parties']; provs = r['provs']; mm = r['mesa_mode']; P07 = r['P07']; M05 = r['M05']
    year = r['year']
    totals = {'censo': 0, 'bl': 0, 'nu': 0}
    nat_v = np.zeros(NP, dtype=np.int64); nat_es = np.zeros(NP, dtype=np.int64)
    for pr in provs:
        nat_v += pr['v']; nat_es += pr['es']
        for k in totals: totals[k] += pr[k]
    notas = []
    if mm and r['dev'] > 0.0005:
        notas.append('Los resultados de municipios y secciones proceden de los ficheros de mesa del Ministerio del Interior, que difieren un %s %% del escrutinio oficial; provincias, escaños y totales son los oficiales.' % (('%.1f' % (r['dev'] * 100)).replace('.', ',') if r['dev'] >= 0.001 else ('%.2f' % (r['dev'] * 100)).replace('.', ',')))
    if r.get('recalc'):
        notas.append('En %s los votos provinciales se han obtenido sumando los municipios: el fichero provincial del Ministerio es inconsistente con el resto de sus datos, y con la suma municipal el reparto coincide con el oficial.' % ', '.join(next(p['n'] for p in provs if p['id'] == d) for d in r['recalc']))
    if r['difs']:
        notas.append('En %s el reparto oficial de escaños no coincide con un D\'Hondt estricto sobre los votos publicados; se muestra el reparto oficial.' % ', '.join(next(p['n'] for p in provs if p['id'] == d) for d in r['difs']))
    ccaa = [dict(id=c, n=n) for c, n in sorted(B.C23.items())]
    gen = dict(id=e, title='Elecciones generales', date=B.DATES[e], year=year, sections=bool(mm), mapyear=B.MAPYEAR[e] if mm else None, parties=parties, ccaa=ccaa,
        prov=[dict(id=p['id'], n=p['n'], cc=p['cc'], s=p['s'], censo=int(p['censo']), bl=int(p['bl']), nu=int(p['nu']), v=[int(x) for x in p['v']], cera=[int(x) for x in p['cera']],
                   cera_bl=int(p['cera_bl']), cera_nu=int(p['cera_nu']), cera_censo=int(p['cera_censo']), es=[int(x) for x in p['es']]) for p in provs],
        nat=dict(censo=int(totals['censo']), bl=int(totals['bl']), nu=int(totals['nu']), v=[int(x) for x in nat_v], es=[int(x) for x in nat_es]),
        notas=notas, mesas=r['nmesas'], groups=groups_for(e, parties))
    sz = js(f'datos/{e}/general.json', gen)
    # municipios + ficheros por provincia
    buckets = collections.defaultdict(dict); mlist = []
    S = r['S']; SV = r['SV']
    if mm:
        Sg = {p: g for p, g in S.groupby('prov')}; SVg = {p: g for p, g in SV.groupby('prov')}
    for pr in provs:
        p = pr['id']; used = None; muns = []
        if mm:
            s = Sg.get(p); sv = SVg.get(p)
            if s is None: buckets[bucket(p)][p] = dict(p=p, parties=[], m=[]); continue
            used = sorted(sv.pi.unique()); loc = {g: j for j, g in enumerate(used)}
            secv = {}
            for (m, c), g in sv.groupby(['mun', 'cus']):
                a = [0] * len(used)
                for i, x in zip(g.pi, g.votos): a[loc[i]] = int(x)
                secv[(m, c)] = a
            for m, g in s.groupby('mun'):
                secs = []; mv = [0] * len(used)
                for rr in g.sort_values('cus').itertuples():
                    a = secv.get((m, rr.cus), [0] * len(used)); secs.append([rr.cus, int(rr.censo), int(rr.bl), int(rr.nu)] + a)
                    for j, x in enumerate(a): mv[j] += x
                info = M05.get(p + m, dict(name=p + m, pob=0))
                nm = _M23.get(p + m, info['name'])
                muns.append([m, nm, int(g.censo.sum()), int(g.bl.sum()), int(g.nu.sum()), mv, secs, info['pob']])
        else:
            cods = sorted(c for c in M05 if c[:2] == p)
            usedset = set()
            for c in cods:
                usedset |= set(r['MV'].get(c, {}).keys())
            used = sorted(usedset); loc = {g: j for j, g in enumerate(used)}
            for c in cods:
                if c not in r['MV']: continue
                mv = [0] * len(used)
                for i, x in r['MV'][c].items(): mv[loc[i]] = int(x)
                info = M05[c]
                muns.append([c[2:], _M23.get(c, info['name']), info['censo'], info['bl'], info['nu'], mv, [], info['pob']])
        for m in muns: mlist.append([p + m[0], m[1], m[7], m[2]])
        buckets[bucket(p)][p] = dict(p=p, parties=[int(u) for u in used], m=muns)
    tot = sz
    for k, d in sorted(buckets.items()): tot += js(f'datos/{e}/prov_b{k}.json', d)
    tot += js(f'datos/{e}/municipios.json', mlist)
    print(e, 'MB', round(tot / 1e6, 2), 'municipios', len(mlist), 'grupos', [(g['label'], int(sum(nat_es[B_i] for B_i, p in enumerate(parties) if p['k'] in g['keys']))) for g in gen['groups']][:3])
    return gen

if __name__ == '__main__':
    shutil.rmtree(f'{OUT}/datos', ignore_errors=True)
    els = sys.argv[1:] or sorted(B.DIRS, reverse=True)
    for e in els: write(e)
    EL = [dict(id=e, label='Elecciones al Congreso %d' % int(e[:4]) + ((' (abril)' if e[5:] == '04' else ' (noviembre)') if e[:4] == '2019' else ''), kind='Congreso') for e in sorted(B.DIRS, reverse=True)]
    js('datos/elecciones.json', EL); print([x['label'] for x in EL])
