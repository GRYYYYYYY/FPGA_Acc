"""Independent XML universe and native NET-union rebuild for every saved comparison vector."""
import json,sys,xml.etree.ElementTree as ET
from pathlib import Path
from collections import Counter,defaultdict
R=Path.cwd();sys.path.insert(0,str(R/'tools'))
from pre_route_endpoints import sha
from audit_native_route import NET,NODE
out=R/'experiments/aes_native_demand_hotspots_v1_2026-10-08';receipt=out/'comparison.json';data=json.loads(receipt.read_text());assert all(sha(k)==v for k,v in data['bindings'].items());bindings={str(receipt):sha(receipt),str(Path(__file__)):sha(Path(__file__))};rows=[]
for row in data['rows']:
 name=row['name'];file=out/name/'comparison_vectors.json';v=json.loads(file.read_text());epfile=R/f'experiments/aes_native_demand_frontend_v1_2026-10-08/{name}/endpoints.json';ep=json.loads(epfile.read_text());graph=Path(ep['inputs']['graph']['path']);route=R/f'experiments/aes_mapped_fresh_cold_v2_2026-10-08/{name}/output.route';owned={};active=None
 for line in route.read_text().splitlines():
  m=NET.match(line)
  if m:active=m[2];assert active not in owned;owned[active]=set()
  n=NODE.match(line)
  if n:assert active is not None;owned[active].add(int(n[1]))
 native=Counter(n for nodes in owned.values() for n in nodes);ledgers={};resident=R/f'experiments/aes_native_demand_estimates_v1_2026-10-08/{name}/resident'
 for frame in ['initial','sketch']:
  p=resident/(frame+'.json');c=json.loads(p.read_text());bindings[str(p)]=sha(p)
  if frame=='initial':ledgers['rc_initial']={int(n):x for n,x in c['ledger'].items()}
  else:ledgers['wire_shared']={int(n):x for n,x in c['ledger'].items()};ledgers['wire_independent']={int(n):x for n,x in c['independent_connection_ledger'].items()}
 expected={};bins=defaultdict(lambda:{'capacity':0,'native':0,'predictions':Counter()})
 for _,node in ET.iterparse(graph,events=('end',)):
  if node.tag=='node':
   if node.get('type') in {'CHANX','CHANY'} and int(node.get('capacity'))>0:
    n=int(node.get('id'));cap=int(node.get('capacity'));loc=node.find('loc');segment=node.find('segment');sid=int(segment.get('segment_id')) if segment is not None else -1;pred={m:l.get(n,0) for m,l in ledgers.items()};expected[n]={'node':n,'capacity':cap,'native':native[n],'predictions':pred}
    for x in range(int(loc.get('xlow')),int(loc.get('xhigh'))+1):
     for y in range(int(loc.get('ylow')),int(loc.get('yhigh'))+1):
      b=bins[int(loc.get('layer','0')),x,y,node.get('type'),sid];b['capacity']+=cap;b['native']+=native[n];b['predictions'].update(pred)
   node.clear()
 observed={x['node']:x for x in v['channels']};assert len(observed)==len(v['channels']) and observed==expected;spatial={tuple(x['key']):x for x in v['bins']};assert len(spatial)==len(v['bins']) and set(spatial)==set(bins)
 for k,b in bins.items():assert spatial[k]['capacity']==b['capacity'] and spatial[k]['native']==b['native'] and spatial[k]['predictions']==dict(b['predictions'])
 for p in [file,epfile,graph,route]:bindings[str(p)]=sha(p)
 rows.append({'name':name,'all_positive_capacity_original_XML_CHAN_resources_exact':True,'native_truth_independent_NET_union_exact':True,'all_concrete_and_spatial_native_capacity_and_prediction_vectors_exact':True,'concrete_resources':len(expected),'spatial_bins':len(bins)})
assert all(sha(k)==v for k,v in bindings.items());(out/'vector_verification.json').write_text(json.dumps({'bindings':bindings,'rows':rows,'scope':'Full native NET-union/resource universe/concrete and spatial vector proof, plus separate independent metric proof. Previously observed family, no heldout claim.'},indent=2)+'\n');print(rows)
