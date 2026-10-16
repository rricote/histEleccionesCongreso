import pandas as pd, numpy as np, sys, os
R=sys.argv[1]; YM=sys.argv[2]  # dir, '2307'
def rd(n): return open(f'{R}/{n}{"02"}{YM}.DAT'.replace('0202','02') if False else f'{R}/{n}02{YM}.DAT',encoding='latin1').read().splitlines()
# 03 candidaturas
cand=[]
for l in rd('03'):
    cand.append(dict(cod=int(l[8:14]),siglas=l[14:64].strip(),nombre=l[64:214].strip(),cod_prov=int(l[214:220]),cod_ccaa=int(l[220:226]),cod_nac=int(l[226:232])))
cand=pd.DataFrame(cand)
# 09 mesas
M=[]
for l in rd('09'):
    M.append((l[9:11],l[11:13],l[13:16],l[16:18],l[18:22],l[22],int(l[23:30]),int(l[30:37]),int(l[65:72]),int(l[72:79]),int(l[79:86]),l[100]))
mesa=pd.DataFrame(M,columns='ccaa prov mun dist sec mesa censo_ine censo blancos nulos vcand oficial'.split())
V=[]
for l in rd('10'):
    V.append((l[9:11],l[11:13],l[13:16],l[16:18],l[18:22],l[22],int(l[23:29]),int(l[29:36])))
vot=pd.DataFrame(V,columns='ccaa prov mun dist sec mesa cod votos'.split())
mesa.to_pickle('/tmp/w/build/mesa.pkl'); vot.to_pickle('/tmp/w/build/vot.pkl'); cand.to_pickle('/tmp/w/build/cand.pkl')
print(len(mesa),len(vot),cand.shape)
print(mesa.mun.eq('999').sum(), mesa.sec.str[3].value_counts().head(8).to_dict())
print(mesa.oficial.value_counts().to_dict())
