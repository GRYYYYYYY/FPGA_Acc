"""Source-only physical track/segment/channel-width features; no RR ID feature."""
import json,xml.etree.ElementTree as ET
from pathlib import Path
from exact_factor_elimination_v1 import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'wbuart_track_attributes_v1_2026-10-20'
def read(p):return json.loads(Path(p).read_text())
def main():
 D.mkdir(exist_ok=False);H=E/'wbuart_preroute_heterograph_v1_2026-10-20';source=H/'verification.json';proof=H/'independent_verification_v1.json';assert all(sha(p)==h for p,h in read(proof)['bindings'].items());bindings={str(p):sha(p) for p in [source,proof,Path(__file__)]};rows=[]
 for g in read(source)['graphs']:
  for _,element in ET.iterparse(g['graph']):
   if element.tag=='channels':
    widths={int(q.get('info')) for q in element if q.tag in ['x_list','y_list']};maximum=int(element.find('channel').get('chan_width_max'));assert widths=={maximum};break
  else:raise ValueError('missing declared channel widths')
  nodes=[json.loads(x) for x in Path(g['directory'],'RR_nodes.jsonl').read_text().splitlines()];channels=[n for n in nodes if n['type'] in ['CHANX','CHANY']];assert {n['segment_id'] for n in channels}=={0,1};out=D/Path(g['directory']).name;out.mkdir();p=out/'track_attributes.jsonl'
  with p.open('x') as f:
   for n in sorted(channels,key=lambda n:n['id']):
    ptc=n['loc']['ptc'];assert type(ptc) is int and 0<=ptc<maximum;record={'RR':n['id'],'ptc':ptc,'width':maximum,'relative_ptc_numerator':ptc,'relative_ptc_denominator':maximum-1,'segment_id':n['segment_id'],'features':[ptc,ptc/(maximum-1),maximum,int(n['segment_id']==0),int(n['segment_id']==1)]};f.write(json.dumps(record,separators=(',',':'))+'\n')
  bindings[str(p)]=sha(p);bindings[g['graph']]=sha(g['graph']);rows.append({'graph':g['graph'],'graph_sha256':Path(g['directory']).name,'attributes':str(p),'resources':len(channels),'channel_width':maximum});print('TRACK_ATTRIBUTES',maximum,len(channels),flush=True)
 (D/'verification.json').write_text(json.dumps({'status':'ALL3_ARCHITECTURE_TRACK_ATTRIBUTES_SOURCE_ONLY','rows':rows,'columns':['physical_ptc','relative_ptc','declared_channel_width','segment_0','segment_1'],'bindings':bindings,'target_labels_read':False,'scope':'Physical RR channel track and segment identities, not raw RR ID. Uniform widths/segment0,1 explicitly checked for current fixtures; no claim for nonuniform or other architectures. No new learned model or quality gain.'},indent=2)+'\n')
if __name__=='__main__':main()
