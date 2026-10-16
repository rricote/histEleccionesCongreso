import sys, os, re, json, collections
import numpy as np
sys.path.insert(0, '/tmp/w/build')
import parties as P
R = '/tmp/w/raw'
OUTD = '/tmp/w/out/datos'
DIRS = {d[2:6] + '-' + d[6:8]: d for d in sorted(os.listdir(R))}
MONTHS = {'03': 'marzo', '06': 'junio', '07': 'julio', '10': 'octubre', '11': 'noviembre', '12': 'diciembre', '04': 'abril'}
DATES = {'1977-06': '15 de junio de 1977', '1979-03': '1 de marzo de 1979', '1982-10': '28 de octubre de 1982', '1986-06': '22 de junio de 1986',
 '1989-10': '29 de octubre de 1989', '1993-06': '6 de junio de 1993', '1996-03': '3 de marzo de 1996', '2000-03': '12 de marzo de 2000',
 '2004-03': '14 de marzo de 2004', '2008-03': '9 de marzo de 2008', '2011-11': '20 de noviembre de 2011', '2015-12': '20 de diciembre de 2015',
 '2016-06': '26 de junio de 2016', '2019-04': '28 de abril de 2019', '2019-11': '10 de noviembre de 2019', '2023-07': '23 de julio de 2023'}
MAPYEAR = {}
for e in DIRS:
    y = int(e[:4])
    MAPYEAR[e] = 2001 if y <= 2000 else y
def rdf(e, n):
    d = DIRS[e]; return open(f'{R}/{d}/{n}02{d[4:8]}.DAT', encoding='latin1').read().splitlines()
def fixname(nm):
    nm = nm.strip()
    m = re.match(r"^(.*), (El|La|Los|Las|A|O|Os|As|L'|Els|Les|Sa|Ses|Es|Na)$", nm)
    return (m.group(2) + ('' if m.group(2).endswith("'") else ' ') + m.group(1)) if m else nm
# nombres de provincia y ccaa de 2023 (unificados)
P23 = {}; C23 = {}
for l in rdf('2023-07', '07'):
    c, p, d = l[9:11], l[11:13], l[13]
    if p == '99' and c != '99': C23[c] = l[14:64].strip()
    if d == '9' and p != '99': P23[p] = (c, l[14:64].strip())

def build(e):
    year = int(e[:4]); mesa_mode = DIRS[e].endswith('MESA')
    cand = {}
    for l in rdf(e, '03'):
        cand[int(l[8:14])] = (l[14:64].strip(), l[64:214].strip(), int(l[226:232]))
    # provincias (07)
    P07 = {}
    for l in rdf(e, '07'):
        c, p, d = l[9:11], l[11:13], l[13]
        if d == '9' and p != '99':
            P07[p] = dict(ccaa=c, name=l[14:64].strip(), seats=int(l[149:155]), censo=int(l[85:93]), bl=int(l[125:133]), nu=int(l[133:141]), vc=int(l[141:149]))
    if mesa_mode:
        for l in rdf(e, '10'):
            c_ = int(l[23:29])
            if c_ not in cand and int(l[29:36]) > 0: cand[999999] = ('OTRAS', 'Otras candidaturas (sin identificar en los ficheros)', 999999)
    # 08
    V08 = collections.defaultdict(int); S08 = collections.defaultdict(int)
    nat_tot = collections.Counter(); nat_sig = collections.defaultdict(set); nat_name = {}
    for l in rdf(e, '08'):
        if l[11:13] == '99': continue
        c = int(l[14:20]); n = cand[c][2]; v = int(l[20:28]); s = int(l[28:33])
        nat_tot[n] += v; nat_sig[n].add(cand[c][0]); nat_name.setdefault(n, cand[c][1])
    for c_, (a_, b_, n_) in cand.items():
        if a_ == 'OTRAS': nat_tot[n_] += 0; nat_sig[n_].add(a_); nat_name.setdefault(n_, b_)
    # claves canónicas
    key_of = {}
    for n in nat_tot:
        k = P.canon(sorted(nat_sig[n]), nat_name[n], year)
        if k and k not in P.STY: k = None
        key_of[n] = k or 'P%d' % n
    ktot = collections.Counter(); kbig = {}
    for n, v in nat_tot.items():
        ktot[key_of[n]] += v
        if key_of[n] not in kbig or nat_tot[kbig[key_of[n]]] < v: kbig[key_of[n]] = n
    order = [k for k, _ in ktot.most_common()]
    kidx = {k: i for i, k in enumerate(order)}
    cod2i = {c: kidx[key_of[cand[c][2]]] for c in cand}
    NP = len(order)
    parties = []; ex = 0
    for k in order:
        n = kbig[k]; sig = min(nat_sig[n], key=len) if False else sorted(nat_sig[n])[0]; nm = nat_name[n]
        if k in P.STY:
            dn, c, d = P.STY[k]; dn = P.disp_name(k, year, dn)
        else:
            dn = sig if len(sig) <= 14 else sig.title(); 
            if ktot[k] > 0.004 * sum(ktot.values()): c = d = P.EXTRA[ex % len(P.EXTRA)]; ex += 1
            else: c, d = '#8a94a1', '#7a8593'
        parties.append(dict(k=k, n=dn, full='Sumar' if k == 'SUMAR' else (nm.title() if nm.isupper() else nm), nat=int(n), c=c, d=d))
    # seats oficiales por provincia/partido
    OFF = collections.defaultdict(int)
    for l in rdf(e, '08'):
        if l[11:13] == '99': continue
        s = int(l[28:33])
        if s: OFF[(l[11:13], cod2i[int(l[14:20])])] += s
    # municipios (05)
    M05 = {}
    for l in rdf(e, '05'):
        if l[16:18] != '99': continue
        M05[l[11:13] + l[13:16]] = dict(name=fixname(l[18:118]), pob=int(l[128:136] or 0), censo=int(l[149:157] or 0), bl=int(l[189:197]), nu=int(l[197:205]))
    prov_ids = sorted(P07)
    PVOTES = {p: np.zeros(NP, dtype=np.int64) for p in prov_ids}
    if mesa_mode:
        sec_off = 1 if year <= 1993 else 0
        mesas = []
        for l in rdf(e, '09'):
            if l[11:13] == '99': continue
            sec = l[18:22]; s3 = sec[1:4] if year <= 1993 else sec[:3]
            mesas.append((l[11:13], l[13:16], l[16:18] + s3, int(l[30:37]), int(l[65:72]), int(l[72:79]), int(l[79:86])))
        import pandas as pd
        mesa = pd.DataFrame(mesas, columns='prov mun cus censo bl nu vc'.split())
        VV = []
        for l in rdf(e, '10'):
            if l[11:13] == '99': continue
            sec = l[18:22]; s3 = sec[1:4] if year <= 1993 else sec[:3]
            c_ = int(l[23:29]); vv_ = int(l[29:36])
            if c_ not in cod2i:
                if vv_ == 0: continue
                c_ = 999999
            VV.append((l[11:13], l[13:16], l[16:18] + s3, cod2i[c_], vv_))
        vot = pd.DataFrame(VV, columns='prov mun cus pi votos'.split())
        mesa['cera'] = mesa.mun.eq('999'); vot['cera'] = vot.mun.eq('999')
        S = mesa[~mesa.cera].groupby(['prov', 'mun', 'cus']).agg(censo=('censo', 'sum'), bl=('bl', 'sum'), nu=('nu', 'sum'), vc=('vc', 'sum')).reset_index()
        SV = vot[~vot.cera].groupby(['prov', 'mun', 'cus', 'pi']).votos.sum().reset_index()
        chk = SV.groupby(['prov', 'mun', 'cus']).votos.sum().rename('sv').reset_index().merge(S, on=['prov', 'mun', 'cus'])
        print(e, 'secciones', len(S), 'descuadre vcand', int((chk.sv != chk.vc).sum()))
        CE = mesa[mesa.cera].groupby('prov').agg(censo=('censo', 'sum'), bl=('bl', 'sum'), nu=('nu', 'sum'))
        CV = vot[vot.cera].groupby(['prov', 'pi']).votos.sum().reset_index()
    else:
        # municipios desde 06
        MV = collections.defaultdict(lambda: collections.defaultdict(int))
        for l in rdf(e, '06'):
            if l[14:16] != '99' or l[9:11] == '99': continue
            MV[l[9:11] + l[11:14]][cod2i[int(l[16:22])]] += int(l[22:30])
    provs = []
    for p in prov_ids:
        info = P07[p]
        if mesa_mode:
            v = np.zeros(NP, dtype=np.int64); cvv = np.zeros(NP, dtype=np.int64)
            for i, x in SV[SV.prov == p].groupby('pi').votos.sum().items(): v[i] += x
            for r in CV[CV.prov == p].itertuples(): v[r.pi] += r.votos; cvv[r.pi] += r.votos
            s = S[S.prov == p]; ce = CE.loc[p] if p in CE.index else None
            cb = int(ce.bl) if ce is not None else 0; cn = int(ce.nu) if ce is not None else 0; cc = int(ce.censo) if ce is not None else 0
            bl = int(s.bl.sum()) + cb; nu = int(s.nu.sum()) + cn; censo = int(s.censo.sum()) + cc
        else:
            v = np.zeros(NP, dtype=np.int64); cvv = np.zeros(NP, dtype=np.int64)
            for l in []: pass
            cb = cn = cc = 0; bl = info['bl']; nu = info['nu']; censo = info['censo']
        PVOTES[p] = v
        provs.append(dict(id=p, n=P23.get(p, (info['ccaa'], info['name']))[1], cc=P23.get(p, (info['ccaa'],))[0], s=info['seats'], censo=censo, bl=bl, nu=nu, v=v, cera=cvv, cera_bl=cb, cera_nu=cn, cera_censo=cc))
    OV = {p: np.zeros(NP, dtype=np.int64) for p in prov_ids}
    for l in rdf(e, '08'):
        p = l[11:13]
        if p == '99': continue
        OV[p][cod2i[int(l[14:20])]] += int(l[20:28])
    dev = 0
    for pr in provs:
        if mesa_mode: dev += int(np.abs(pr['v'] - OV[pr['id']]).sum())
        i = P07[pr['id']]
        pr['v'] = OV[pr['id']]
        pr['bl'] = i['bl']; pr['nu'] = i['nu']; pr['censo'] = i['censo']
    totv = sum(int(pr['v'].sum()) for pr in provs); dev = dev / totv
    print(e, 'desviación mesas vs oficial: %.3f%%' % (dev * 100))
    # escaños D'Hondt
    mism = 0
    for pr in provs:
        v = pr['v']; valid = int(v.sum()) + pr['bl']
        el = [(int(v[i]), i) for i in range(NP) if v[i] >= 0.03 * valid and v[i] > 0]
        q = sorted(((a / d, i) for a, i in el for d in range(1, pr['s'] + 1)), reverse=True)[:pr['s']]
        se = np.zeros(NP, dtype=int)
        for _, i in q: se[i] += 1
        pr['es'] = se
    mine = {(pr['id'], i): int(x) for pr in provs for i, x in enumerate(pr['es']) if x}
    ok = mine == dict(OFF)
    difs = sorted({k[0] for k in set(mine) | set(OFF) if mine.get(k, 0) != OFF.get(k, 0)})
    def dh(pr):
        v = pr['v']; valid = int(v.sum()) + pr['bl']
        el = [(int(v[i]), i) for i in range(NP) if v[i] >= 0.03 * valid and v[i] > 0]
        q = sorted(((a / d, i) for a, i in el for d in range(1, pr['s'] + 1)), reverse=True)[:pr['s']]
        se = np.zeros(NP, dtype=int)
        for _, i in q: se[i] += 1
        return se
    recalc = []
    if not mesa_mode:
        for pr in provs:
            if pr['id'] not in difs: continue
            sm = np.zeros(NP, dtype=np.int64)
            for k_, d_ in MV.items():
                if k_[:2] == pr['id']:
                    for i_, x_ in d_.items(): sm[i_] += x_
            old_v = pr['v']; pr['v'] = sm; se = dh(pr)
            off = np.zeros(NP, dtype=int)
            for (p_, i_), x_ in OFF.items():
                if p_ == pr['id']: off[i_] = x_
            if (se == off).all():
                print(e, 'prov', pr['id'], 'recalculada con la suma de municipios (08 inconsistente):', int(np.abs(sm - old_v).sum()), 'votos de diferencia'); pr['es'] = se; recalc.append(pr['id'])
                for k_ in [k for k in mine if k[0] == pr['id']]: del mine[k_]
                for i_, x_ in enumerate(se):
                    if x_: mine[(pr['id'], i_)] = int(x_)
            else: pr['v'] = old_v
        difs = sorted({k[0] for k in set(mine) | set(OFF) if mine.get(k, 0) != OFF.get(k, 0)})
        ok = mine == dict(OFF)
    for pr in provs:
        if pr['id'] in difs:
            pr['es'] = np.zeros(NP, dtype=int)
            for (p_, i_), x_ in OFF.items():
                if p_ == pr['id']: pr['es'][i_] = x_
    print(e, 'partidos', NP, 'escaños propios==oficiales:', ok, sum(mine.values()), sum(OFF.values()))
    if not ok:
        for k in sorted(set(mine) | set(OFF)):
            if mine.get(k, 0) != OFF.get(k, 0): print('   dif', k, parties[k[1]]['k'], mine.get(k, 0), OFF.get(k, 0))
    return dict(year=year, mesa_mode=mesa_mode, parties=parties, provs=provs, P07=P07, M05=M05, NP=NP, cod2i=cod2i,
                difs=difs, recalc=recalc, S=S if mesa_mode else None, SV=SV if mesa_mode else None, MV=None if mesa_mode else MV, dev=dev, OFF=dict(OFF), nmesas=len(mesa) if mesa_mode else 0)

if __name__ == '__main__':
    for e in (sys.argv[1:] or DIRS): build(e)
