import zipfile,re,json,xml.etree.ElementTree as E
from pathlib import Path
root=Path.cwd(); results=[]
for p in [root/'shared/vorige-jaren/2025_Groep_1-main.zip',root/'shared/vorige-jaren/2025_Groep_2-main.zip',root/'shared/vorige-jaren/2026_Groep_5-main.zip']:
 with zipfile.ZipFile(p) as z:
  for n in z.namelist():
   if Path(n).suffix.lower() in ['.md','.ino','.txt','.py','.html'] and z.getinfo(n).file_size<300000:
    lines=z.read(n).decode('utf-8',errors='replace').splitlines()
    hits=[(i+1,l[:500]) for i,l in enumerate(lines) if re.search(r'Grove|Vision.AI|XIAO|OV2640|OV5647|DFR1154|gripper|grijper|camera',l,re.I)]
    if hits: results.append({'archive':p.name,'file':n,'hits':hits[:18]})
p=root/'concept/presentatie/Concept-presentatie-v2-NL.pptx'
with zipfile.ZipFile(p) as z:
 for n in z.namelist():
  if re.match(r'ppt/slides/slide\d+.xml$',n):
   t=' '.join(E.fromstring(z.read(n)).itertext())
   if re.search('camera|grove|grijper|sensor',t,re.I):results.append({'presentation':p.name,'slide':n,'text':t[:5000]})
out=root/'t3-ux-ui/lokaal/camera-broncontrole.json';out.write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
for x in results: print(json.dumps(x,ensure_ascii=True))
