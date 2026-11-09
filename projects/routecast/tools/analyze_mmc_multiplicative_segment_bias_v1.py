"""Descriptive authenticated segment/span demand ratios; no calibration or heldout claim."""
import json,sys,xml.etree.ElementTree as E
from pathlib import Path
from collections import defaultdict
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from pre_route_endpoints import sha
proof=R/'experiments/mmc_multiplicative_hotspots_v1_2026-10-10/verification.json';v=json.loads(proof.read_text());assert v['metric_vectors_independently_recomputed']==8
bindings={str(proof):sha(proof),str(Path(__file__).resolve()):sha(Path(__file__))}
def load(p):
 assert str(p) in v['bindings'] and sha(p)==v['bindings'][str(p)]
 bindings[str(p)]=sha(p);return json.loads(p.read_text())
labels=load(R/'experiments/mmc_congestion_only_hotspots_v6_2026-10-10/mmc/comparison_vectors.json');truth={x['node']:x for x in labels['channels']}
models={'original':R/'experiments/mmc_resident_manifest_scope_seed_handoff_v1_2026-10-10/model/sketch.json','criticality':R/'experiments/mmc_full_criticality_feedback_trial_v1_2026-10-10/model/sketch.json','present':R/'experiments/mmc_present_guard_complete_v1_2026-10-10/model/sketch.json'}
models['multiplicative']=R/'experiments/mmc_multiplicative_feedback_trial_v1_2026-10-10/model/sketch.json'
ledgers={}
for name,p in models.items():
 if name in ('present','criticality'):
  bindings[str(p)]=sha(p);d=json.loads(p.read_text())
 else:d=load(p)
 assert d['completed_connections']==115572;ledgers[name]={int(k):x for k,x in d['ledger'].items()}
ep=load(R/'experiments/ultraembedded_mmc_continuous_workflow_v6_2026-10-08/seed/demand/mmc/endpoints.json');graph=Path(ep['inputs']['graph']['path']);assert sha(graph)==ep['graph_sha256'];bindings[str(graph)]=ep['graph_sha256']
groups=defaultdict(lambda:defaultdict(int));seen=set();stack=[]
for event,el in E.iterparse(graph,events=('start','end')):
 if event=='start':stack.append(el);continue
 if el.tag=='node':
  n=int(el.get('id'))
  if n in truth:
   assert n not in seen;seen.add(n);loc=el.find('loc').attrib;t=el.get('type');length=int(loc['xhigh'])-int(loc['xlow'])+1 if t=='CHANX' else int(loc['yhigh'])-int(loc['ylow'])+1
   seg=el.find('segment');key=(t,int(seg.get('segment_id')),length);g=groups[key];g['nodes']+=1;g['native_node_demand']+=truth[n]['native'];g['capacity']+=truth[n]['capacity']
   for name,l in ledgers.items():g[name+'_node_demand']+=l.get(n,0)
  stack[-2].remove(el);el.clear()
 if el.tag=='rr_nodes':break
 stack.pop()
assert seen==set(truth)
rows=[]
for key,g in sorted(groups.items()):
 row=dict(type=key[0],segment_id=key[1],span=key[2],**g)
 for name in ledgers:row[name+'_ratio_to_native']=g[name+'_node_demand']/g['native_node_demand'] if g['native_node_demand'] else None
 rows.append(row)
assert all(sha(p)==h for p,h in bindings.items())
out=R/'experiments/mmc_multiplicative_feedback_trial_v1_2026-10-10/segment_bias_v1.json';assert not out.exists();out.write_text(json.dumps(dict(bindings=bindings,complete_positive_channels=len(seen),rows=rows,scope='Descriptive exposed-MMC segment/span node demand; present and criticality states hash bound but separate prior certifications not revalidated here; no parameter fitting/native equivalence/heldout claim'),indent=2)+'\n')
print('SEGMENT BIAS COMPLETE',len(seen),len(rows),flush=True)
