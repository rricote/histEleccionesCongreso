import json
o=json.load(open('an.json'))
s=open('/tmp/w/out/datos/2023-07/general.json.js').read()
j=json.loads(s[s.index('={')+1:s.rindex('}')+1])
L={l['id']:l for l in o['labels']}
NAME2ID={'Vizcaya':'48','Guipúzcoa':'20','Araba':'01','Navarra':'31','Bartzelona':'08','Gerona':'17','Lérida':'25','Tarragona':'43','Castelló':'12','Teruel':'44','Valentzia':'46','Islas Baleares':'07','Madril':'28','Ceuta':'51','Melilla':'52','Santa CruzTenerifekoa':'38','Las Palmas':'35','Alacant':'03','Murtzia':'30','Almería':'04','Granada':'18','Albacete':'02','Cuenca':'16','Guadalajara':'19','Soria':'42','Errioxa':'26','Málaga':'29','Cádiz':'11','Huelva':'21','Sevilla':'41','Kordoba':'14','Jaén':'23','Badajoz':'06','Cáceres':'10','Ciudad Real':'13','Toledo':'45','Ávila':'05','Salamanca':'37','Segovia':'40','Zaragoza':'50','Burgos':'09','Kantabria':'39','Asturias':'33','León':'24','Palentzia':'34','Valladolid':'47','Zamora':'49','Lugo':'27','La Coruña':'15','Orense':'32','Pontevedra':'36','Huesca':'22'}
path={}
for k,v in o['pif'].items():
    if len(v)==1: path[NAME2ID[L[k]['txt']]]=v[0]
path.update({'48':'path2175','20':'path2180','08':'path2236','38':'path1988','35':'path1999','15':'path2223'})
assert len(path)==52 and len(set(path.values()))==52
F={f['id']:f for f in o['fills']}
import re
def hexc(c):
    m=re.findall(r'\d+',c); return '#%02x%02x%02x'%tuple(map(int,m))
rows=[]
for p in j['prov']:
    v=p['v']; tot=sum(v)+p['bl']; 
    idx=sorted(range(len(v)),key=lambda i:-v[i])
    mg=(v[idx[0]]-v[idx[1]])/tot*100
    mg2=(v[idx[0]]-v[idx[1]])/sum(v)*100
    rows.append((hexc(F[path[p['id']]]['fill']),round(mg,1),round(mg2,1),j['parties'][idx[0]]['k'],p['n']))
for r in sorted(rows): print(r)
json.dump(path,open('path.json','w'))
print('----')
rows=[]
for p in j['prov']:
    v=p['v']; tot=sum(v)+p['bl']
    idx=sorted(range(len(v)),key=lambda i:-v[i])
    rows.append((hexc(F[path[p['id']]]['fill']),round(v[idx[0]]/tot*100,1),round(v[idx[0]]/sum(v)*100,1),round((v[idx[0]]-v[idx[1]])/tot*100,1),p['es'][idx[0]],p['s'],p['n']))
for r in sorted(rows): print(r)
