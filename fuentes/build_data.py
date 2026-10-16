import pandas as pd, numpy as np, json, re, os, sys, collections
OUT='/tmp/w/site/datos/2023-07'
R='/tmp/w/mesa'
mesa=pd.read_pickle('/tmp/w/build/mesa.pkl'); vot=pd.read_pickle('/tmp/w/build/vot.pkl'); cand=pd.read_pickle('/tmp/w/build/cand.pkl')
mesa=mesa[mesa.prov!='99'].copy(); vot=vot[vot.prov!='99'].copy()
nac=cand.set_index('cod').cod_nac.to_dict()
vot['nac']=vot.cod.map(nac)
assert vot.nac.notna().all()
vot['cera']=vot.mun.eq('999'); mesa['cera']=mesa.mun.eq('999')
# ---- invariantes: una lista por grupo nacional y provincia
chk=vot.groupby(['prov','nac']).cod.nunique(); assert (chk==1).all(), chk[chk>1]
# ---- partidos
tot=vot.groupby('nac').votos.sum().sort_values(ascending=False)
head=cand.set_index('cod')
STY={5:('PP','PP','#1d84ce','#4aa3e8'),2:('PSOE','PSOE','#e30613','#f0535b'),6:('VOX','Vox','#5aa31f','#7cc43a'),10:('SUMAR','Sumar','#e6007e','#f2489f'),
50:('ERC','ERC','#e8890c','#f29a2a'),57:('JUNTS','Junts','#00a99d','#2bc7ba'),71:('BILDU','EH Bildu','#8a9a0a','#adc12a'),75:('PNV','PNV','#0b6b3a','#3aa56a'),
65:('BNG','BNG','#3aa0c4','#5bbbdc'),31:('CC','CC','#d9b800','#ecc82a'),74:('UPN','UPN','#a3324a','#cf5a73'),53:('CUP','CUP','#f2c200','#f5d33d'),
32:('NC','Nueva Canarias','#e07b00','#f29a2a'),7:('PACMA','PACMA','#7fb800','#9fd32b'),23:('EXISTE','Aragón Existe','#1f9e8f','#3cc3b3'),55:('PDECAT','PDeCAT','#2a6ebb','#5b9be0'),
73:('GBAI','Geroa Bai','#d94f8a','#ee7aa9')}
EXTRA=['#7b3f98','#a0522d','#5f6caf','#c0733f','#2e8b8b','#9c9c3c','#b34a6e','#6b8e23']
parties=[];k_of={}
for i,(n,v) in enumerate(tot.items()):
    sig=head.siglas.get(n,'?'); nm=head.nombre.get(n,sig)
    if n in STY: k,name,c,d=STY[n]
    else:
        k=f'P{n}'; name=sig.title() if len(sig)>14 else sig; c=d=EXTRA[len(parties)%len(EXTRA)] if v>20000 else '#8a94a1'
        if v<=20000: c,d='#8a94a1','#7a8593'
    parties.append(dict(k=k,n=name,full=nm.title() if nm.isupper() else nm,nat=int(n),c=c,d=d)); k_of[n]=i
NP=len(parties)
print(NP,'partidos',[p['k'] for p in parties[:14]])
vot['pi']=vot.nac.map(k_of)
# ---- nombres
P07={};C07={}
for l in open(f'{R}/07022307.DAT',encoding='latin1'):
    c,p,d=l[9:11],l[11:13],l[13]
    if p=='99' and c!='99': C07[c]=l[14:64].strip()
    if d=='9' and p!='99': P07[p]=dict(ccaa=c,name=l[14:64].strip(),seats=int(l[149:155]))
M05={}
for l in open(f'{R}/05022307.DAT',encoding='latin1'):
    if l[16:18]!='99': continue
    nm=l[18:118].strip(); 
    m=re.match(r'^(.*), (El|La|Los|Las|A|O|Os|As|L\'|Els|Les|Sa|Ses|Es|Na)$',nm)
    if m: nm=(m.group(2)+(' ' if not m.group(2).endswith("'") else '')+m.group(1))
    M05[l[11:13]+l[13:16]]=dict(name=nm,pob=int(l[128:136]))
print(len(P07),len(C07),len(M05),sum(p['seats'] for p in P07.values()))
# ---- secciones
mesa['cus']=mesa.dist+mesa.sec.str[:3]
S=mesa[~mesa.cera].groupby(['prov','mun','cus']).agg(censo=('censo','sum'),bl=('blancos','sum'),nu=('nulos','sum'),vc=('vcand','sum')).reset_index()
vv=vot[~vot.cera].copy(); vv['cus']=vv.dist+vv.sec.str[:3]
SV=vv.groupby(['prov','mun','cus','pi']).votos.sum().reset_index()
# cuadre vcand
chk=SV.groupby(['prov','mun','cus']).votos.sum().rename('sv').reset_index().merge(S,on=['prov','mun','cus']); print('secciones',len(S),'descuadre vcand',(chk.sv!=chk.vc).sum())
# CERA por provincia
CE=mesa[mesa.cera].groupby('prov').agg(censo=('censo','sum'),bl=('blancos','sum'),nu=('nulos','sum'),vc=('vcand','sum'))
CV=vot[vot.cera].groupby(['prov','pi']).votos.sum().reset_index()
# ---- provincias: votos totales incl. CERA
def vec(df,col='pi'):
    a=np.zeros(NP,dtype=np.int64)
    a[df[col].values]=df.votos.values; return a
provs=[]
for p,info in sorted(P07.items()):
    sv=SV[SV.prov==p].groupby('pi').votos.sum(); cv=CV[CV.prov==p].set_index('pi').votos
    v=np.zeros(NP,dtype=np.int64); cvv=np.zeros(NP,dtype=np.int64)
    for i,x in sv.items(): v[i]+=x
    for i,x in cv.items(): v[i]+=x; cvv[i]+=x
    s=S[S.prov==p]; ce=CE.loc[p]
    bl=int(s.bl.sum()+ce.bl); nu=int(s.nu.sum()+ce.nu); censo=int(s.censo.sum()+ce.censo)
    # escaños D'Hondt
    valid=int(v.sum())+bl; el=[(v[i],i) for i in range(NP) if v[i]>=0.03*valid]
    q=sorted(((v_/d,i) for v_,i in el for d in range(1,info['seats']+1)),reverse=True)[:info['seats']]
    se=np.zeros(NP,dtype=int)
    for _,i in q: se[i]+=1
    provs.append(dict(id=p,n=info['name'],cc=info['ccaa'],s=info['seats'],censo=censo,bl=bl,nu=nu,v=[int(x) for x in v],cera=[int(x) for x in cvv],cera_bl=int(ce.bl),cera_nu=int(ce.nu),cera_censo=int(ce.censo),es=[int(x) for x in se]))
# verifica con oficial 08
O={}
for l in open(f'{R}/08022307.DAT',encoding='latin1'):
    if l[11:13]!='99': 
        o=int(l[28:33]); 
        if o: O[(l[11:13],int(l[14:20]))]=o
mine={}
for pr in provs:
    for i,e in enumerate(pr['es']):
        if e: mine[(pr['id'],parties[i]['nat'])]=mine.get((pr['id'],parties[i]['nat']),0)+e
off={}
for (p,cod),e in O.items(): off[(p,nac[cod])]=off.get((p,nac[cod]),0)+e
print('escaños propios == oficiales:',mine==off, sum(mine.values()))
natv=np.sum([p['v'] for p in provs],axis=0); natse=np.sum([p['es'] for p in provs],axis=0)
print([(parties[i]['k'],int(natse[i])) for i in range(NP) if natse[i]])
ccaa=[dict(id=c,n=n) for c,n in sorted(C07.items())]
gen=dict(id='2023-07',title='Elecciones generales',date='23 de julio de 2023',year=2023,parties=parties,ccaa=ccaa,prov=provs,
  nat=dict(censo=sum(p['censo'] for p in provs),bl=sum(p['bl'] for p in provs),nu=sum(p['nu'] for p in provs),v=[int(x) for x in natv],es=[int(x) for x in natse]),
  notas=['Datos de mesa del Ministerio del Interior. En Toledo y Cantabria la suma de mesas difiere en unos cientos de votos del escrutinio general oficial; el reparto de escaños no cambia.'])
json.dump(gen,open(f'{OUT}/general.json','w'),ensure_ascii=False,separators=(',',':'))
# ---- ficheros por provincia
tot_sec=0;sizes=[]
for p in sorted(P07):
    s=S[S.prov==p]; sv=SV[SV.prov==p]
    used=sorted(sv.pi.unique()); loc={g:j for j,g in enumerate(used)}
    secv={}
    for (m,c),g in sv.groupby(['mun','cus']): 
        a=[0]*len(used)
        for i,x in zip(g.pi,g.votos): a[loc[i]]=int(x)
        secv[(m,c)]=a
    muns=[]
    for m,g in s.groupby('mun'):
        secs=[];mv=[0]*len(used)
        for r in g.sort_values('cus').itertuples():
            a=secv.get((m,r.cus),[0]*len(used)); secs.append([r.cus,int(r.censo),int(r.bl),int(r.nu)]+a)
            for j,x in enumerate(a): mv[j]+=x
        info=M05.get(p+m,dict(name=p+m,pob=0))
        muns.append([m,info['name'],int(g.censo.sum()),int(g.bl.sum()),int(g.nu.sum()),mv,secs,info['pob']])
    tot_sec+=len(s)
    js=json.dumps(dict(p=p,parties=[int(u) for u in used],m=muns),ensure_ascii=False,separators=(',',':'))
    open(f'{OUT}/prov_{p}.json','w').write(js); sizes.append((len(js),p))
print('secciones',tot_sec,'municipios',sum(len(json.load(open(f"{OUT}/prov_{p}.json"))['m']) for p in P07),'ficheros',len(sizes),'max',max(sizes),'total MB',sum(a for a,_ in sizes)/1e6)
# cuadre municipios con fichero oficial 06 (no CERA)
OFF={}
for l in open(f'{R}/06022307.DAT',encoding='latin1'):
    if l[14:16]=='99': OFF[(l[9:11]+l[11:14],nac[int(l[16:22])])]=OFF.get((l[9:11]+l[11:14],nac[int(l[16:22])]),0)+int(l[22:30])
mine={}
for r in SV.itertuples(): 
    key=(r.prov+r.mun,parties[r.pi]['nat']); mine[key]=mine.get(key,0)+r.votos
diff=[(k,mine.get(k,0),OFF.get(k,0)) for k in set(mine)|set(OFF) if mine.get(k,0)!=OFF.get(k,0)]
print('municipio×partido con diferencia frente a fichero 06:',len(diff),diff[:6], 'de',len(OFF))
