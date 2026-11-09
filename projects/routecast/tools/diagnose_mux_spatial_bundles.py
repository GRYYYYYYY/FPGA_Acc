"""Track-identity versus same-span directional bundle diagnosis; no policy tuning."""
import json,xml.etree.ElementTree as ET
from pathlib import Path
from collections import defaultdict
from pre_route_endpoints import sha
from prediction_metrics import spearman
root=Path(__file__).resolve().parents[1];base=root/'experiments/mux_crossbar_soft_metrics_2026-10-06';p=json.loads((base/'protocol.json').read_text());r=json.loads((base/'receipt.json').read_text());v=json.loads((base/'verification.json').read_text());assert v['receipt_sha256']==sha(base/'receipt.json')
out=root/'experiments/mux_spatial_bundles_2026-10-06';out.mkdir();cases=[]
for c,row in zip(p['cases'],r['rows']):
 f=base/f"gf2_d{c['data_width']}_w{c['channels']}_vectors.json";assert sha(f)==row['vector_sha256'];cases.append({**c,'vectors':str(f),'vectors_sha256':sha(f),'original_rho':row['utilization_spearman'],'original_overuse':row['overflow_support']})
protocol={'cases':cases,'source_sha256':sha(Path(__file__)),'group_key':['type','direction','xlow','xhigh','ylow','yhigh'],'scope':'Frozen same-span directional bundles ignoring track ptc and segment identity. Sum capacity and node demand; no uniqueNET deduplication within bundle. Aggregation is diagnostic and cannot certify legal track assignment; native32 failed attempts. No parameter or policy tuning.'};(out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');rows=[]
for c in cases:
 assert all(sha(f)==h for f,h in c['bindings'].items());data=json.loads(Path(c['vectors']).read_text());byid={x['node']:x for x in data};groups=defaultdict(list)
 for event,n in ET.iterparse(c['graph'],events=['end']):
  if n.tag!='node':continue
  i=int(n.get('id'))
  if i in byid:
   loc=n.find('loc');key=(n.get('type'),n.get('direction'),*(int(loc.get(k)) for k in ['xlow','xhigh','ylow','yhigh']));groups[key].append(i)
  n.clear()
 detail=[]
 for key,ids in sorted(groups.items()):
  detail.append({'key':key,'nodes':sorted(ids),'capacity':sum(byid[i]['capacity'] for i in ids),'predicted':sum(byid[i]['predicted'] for i in ids),'native':sum(byid[i]['native'] for i in ids)})
 assert sum(len(x['nodes']) for x in detail)==len(data)
 pv=[x['predicted']/x['capacity'] for x in detail];tv=[x['native']/x['capacity'] for x in detail];ps={i for i,x in enumerate(detail) if x['predicted']>x['capacity']};ts={i for i,x in enumerate(detail) if x['native']>x['capacity']};hit=len(ps&ts)
 file=out/f"mux_w{c['data_width']}_c{c['channels']}_bundles.json";file.write_text(json.dumps(detail,indent=2)+'\n')
 row={'data_width':c['data_width'],'channels':c['channels'],'nodes':len(data),'bundles':len(detail),'node_rho':c['original_rho'],'bundle_rho':spearman(pv,tv),'bundle_MAE':sum(abs(a-b) for a,b in zip(pv,tv))/len(pv),'bundle_overuse':{'predicted':len(ps),'native':len(ts),'intersection':hit,'precision':hit/len(ps) if ps else None,'recall':hit/len(ts) if ts else None},'hidden_predicted_track_overflow':sum(max(0,x['predicted']-x['capacity']) for x in data)-sum(max(0,x['predicted']-x['capacity']) for x in detail),'hidden_native_track_overflow':sum(max(0,x['native']-x['capacity']) for x in data)-sum(max(0,x['native']-x['capacity']) for x in detail),'detail_sha256':sha(file)};rows.append(row);print(row,flush=True)
(out/'receipt.json').write_text(json.dumps({'protocol_sha256':sha(out/'protocol.json'),'rows':rows,'complete':len(rows)==9},indent=2)+'\n')
