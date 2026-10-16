import json,re
from lxml import etree
exec(open('map1.py').read().split("F={f['id']")[0])
asg=json.load(open('asg.json'))
r=etree.parse('src.svg').getroot()
Ly=[g for g in r if g.get('id')=='layer3'][0]
D={c.get('id'):c.get('d') for c in Ly}
def rnd(d):
    d=re.sub(r'(-?\d*\.\d+)',lambda m:('%.2f'%float(m.group(1))).rstrip('0').rstrip('.') ,d)
    d=re.sub(r'(?<=\d) (?=-)','',d)
    return d
NAMES={'01':'Álava','02':'Albacete','03':'Alicante','04':'Almería','05':'Ávila','06':'Badajoz','07':'Baleares','08':'Barcelona','09':'Burgos','10':'Cáceres','11':'Cádiz','12':'Castellón','13':'Ciudad Real','14':'Córdoba','15':'La Coruña','16':'Cuenca','17':'Gerona','18':'Granada','19':'Guadalajara','20':'Guipúzcoa','21':'Huelva','22':'Huesca','23':'Jaén','24':'León','25':'Lérida','26':'La Rioja','27':'Lugo','28':'Madrid','29':'Málaga','30':'Murcia','31':'Navarra','32':'Orense','33':'Asturias','34':'Palencia','35':'Las Palmas','36':'Pontevedra','37':'Salamanca','38':'Santa Cruz de Tenerife','39':'Cantabria','40':'Segovia','41':'Sevilla','42':'Soria','43':'Tarragona','44':'Teruel','45':'Toledo','46':'Valencia','47':'Valladolid','48':'Vizcaya','49':'Zamora','50':'Zaragoza','51':'Ceuta','52':'Melilla'}
NOLAB=set()
CAN={'35','38'}
out={'vb':[0,0,536,337],'can':[361,-43.5],'prov':{},'lines':[[297.7,20.3,303.7,28.7],[328.9,22.5,321.5,32.9],[448,85.3,470,109]],
 'pie':{'c':[45.6,49.6],'r':23.2,'r2':27.6},'vot':[78.5,50.6],'ast':[275,152.5]}
for pid,pth in path.items():
    cs=[o['circ'][i] for i in asg[pid]]
    xs=[c['cx'] for c in cs]; ys=[c['cy'] for c in cs]
    lab=None
    for k,l in L.items():
        if NAME2ID.get(l['txt'])==pid: lab=[round(l['x'],2),round(l['y'],2)]
    e={'d':rnd(D[pth]),'n':NAMES[pid],'a':[round((min(xs)+max(xs))/2,2),round(min(ys),2)]}
    if pid not in NOLAB: e['l']=lab
    if pid=='38': e['lt']=['Santa Cruz','de Tenerife']
    if pid in CAN: e['can']=1
    out['prov'][pid]=e
js='(window.__J=window.__J||{})["mapas/escanos.json"]='+json.dumps(out,ensure_ascii=False,separators=(',',':'))+';\n'
open('/tmp/w/svg/escanos.json.js','w').write(js)
print(len(js))
