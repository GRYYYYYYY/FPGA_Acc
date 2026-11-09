import json,sys,xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from pre_route_endpoints import sha
from prediction_metrics import compare
out=R/'experiments/aes_native_demand_uniform_channel_v1_2026-10-08';prior=R/'experiments/aes_feedback_round_ablation_v1_2026-10-08';bindings={str(Path(__file__)):sha(Path(__file__))};rows=[]
for p in [prior/'vector_verification.json',prior/'metric_verification.json',out/'control_verification.json']:
 d=json.loads(p.read_text());assert all(sha(k)==v for k,v in d['bindings'].items());bindings[str(p)]=sha(p)
for name in ['aes_cipher','aes_inv_cipher']:
 resident=out/name/'resident';p=resident/'verification.json';proof=json.loads(p.read_text());assert proof['complete_atomic_NET_replay_epochs_affected_schedule_priceupdates_and_full_rebuild_pass'] and all(sha(k)==v for k,v in proof['bindings'].items());bindings[str(p)]=sha(p)
 p=resident/'sketch.json';sketch=json.loads(p.read_text());ledger={int(k):v for k,v in sketch['ledger'].items()};bindings[str(p)]=sha(p);p=prior/name/'comparison_vectors.json';vectors=json.loads(p.read_text());bindings[str(p)]=sha(p);epfile=R/'experiments/aes_native_demand_frontend_v1_2026-10-08'/name/'endpoints.json';ep=json.loads(epfile.read_text());graph=Path(ep['inputs']['graph']['path']);assert sha(graph)==ep['graph_sha256'];spatial=Counter();stack=[];observed=set()
 for event,el in ET.iterparse(graph,events=('start','end')):
  if event=='start':stack.append(el);continue
  if el.tag=='node' and el.get('type') in {'CHANX','CHANY'} and int(el.get('capacity'))>0:
   node=int(el.get('id'));observed.add(node);loc=el.find('loc');seg=el.find('segment');sid=int(seg.get('segment_id')) if seg is not None else -1
   for x in range(int(loc.get('xlow')),int(loc.get('xhigh'))+1):
    for y in range(int(loc.get('ylow')),int(loc.get('yhigh'))+1):spatial[int(loc.get('layer','0')),x,y,el.get('type'),sid]+=ledger.get(node,0)
  if el.tag in {'node','edge'}:
   if len(stack)>1:stack[-2].remove(el)
   el.clear()
  stack.pop()
 assert observed=={c['node'] for c in vectors['channels']} and set(spatial)=={tuple(b['key']) for b in vectors['bins']}
 for c in vectors['channels']:c['predictions']['uniform_shared']=ledger.get(c['node'],0)
 for b in vectors['bins']:b['predictions']['uniform_shared']=spatial[tuple(b['key'])]
 concrete=compare({c['node']:c['predictions']['uniform_shared']/c['capacity'] for c in vectors['channels']},{c['node']:c['native']/c['capacity'] for c in vectors['channels']},len(observed)//20)
 spatial_metric=compare({tuple(b['key']):b['predictions']['uniform_shared']/b['capacity'] for b in vectors['bins']},{tuple(b['key']):b['native']/b['capacity'] for b in vectors['bins']},20)
 p=out/name/'comparison_vectors.json';p.write_text(json.dumps(vectors)+'\n');bindings[str(p)]=sha(p)
 for p in [epfile,graph]:bindings[str(p)]=sha(p)
 rows.append(dict(name=name,required=sketch['required_connections'],completed=sketch['completed_connections'],overflow_units=sketch['overflow_units'],uniform_shared=dict(concrete=concrete,spatial=spatial_metric)));print(name,spatial_metric,flush=True)
assert all(sha(k)==v for k,v in bindings.items())
(out/'prediction_comparison.json').write_text(json.dumps(dict(bindings=bindings,rows=rows,scope='Uniform50ps channel cost intervention on complete previously observed candidates, original budgets/two rounds preserved, same frozen native labels and full resource universe. Descriptive ablation only; no parameter selection, heldout or native QoR/time claim.'),indent=2)+'\n')
