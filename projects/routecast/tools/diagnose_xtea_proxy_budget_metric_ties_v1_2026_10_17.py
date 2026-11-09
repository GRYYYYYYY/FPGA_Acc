"""Independent Expat replay of final metrics and fixed-selection tie bounds."""
import hashlib,json
from collections import Counter
from pathlib import Path
from xml.parsers import expat
from prediction_metrics import compare
from diagnose_neuron_complete_metric_hotspots_v1 import tie_diagnosis
R=Path(__file__).resolve().parents[1];D=R/'experiments/xtea_proxy_budget_metric_ties_v1_2026-10-17';D.mkdir(exist_ok=False)
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
p=R/'experiments/xtea_proxy_budget_full_comparison_v2_2026-10-17/verification.json';primary=json.loads(p.read_text());assert primary['metric_vectors_independently_recomputed']==8
paths={'graph':R/'experiments/freecores_rr_only_v1_2026-10-08/xtea/rr_graph.xml','native':R/'experiments/freecores_native_cold_v1_2026-10-08/xtea/physical_audit.json','control':R/'experiments/xtea_continue_primary_audit_fixture_v1_2026-10-17/model/sketch.json','proxy':R/'experiments/xtea_proxy_budget_audit_fixture_v1_2026-10-17/model/sketch.json'}
bindings={str(p):sha(p),str(Path(__file__).resolve()):sha(__file__)}
for q in paths.values():
 assert sha(q)==primary['bindings'][str(q)];bindings[str(q)]=sha(q)
for q in [R/'tools/prediction_metrics.py',R/'tools/diagnose_neuron_complete_metric_hotspots_v1.py']:bindings[str(q)]=sha(q)
truth={int(k):v for k,v in json.loads(paths['native'].read_text())['node_occupancy'].items()}
ledgers={k:{int(n):v for n,v in json.loads(paths[k].read_text())['ledger'].items()} for k in ['control','proxy']}
cp={k:{} for k in ledgers};ct={};caps=Counter();native=Counter();span={k:Counter() for k in ledgers};stack=[];node=[None]
class Finished(Exception):pass
def start(tag,a):
 parent=stack[-1] if stack else None
 if tag=='node' and parent=='rr_nodes':node[0]=dict(a)
 if parent=='node' and tag in ['loc','segment']:node[0][tag]=dict(a)
 stack.append(tag)
def end(tag):
 if tag=='node' and len(stack)>1 and stack[-2]=='rr_nodes':
  n=node[0];c=int(n['capacity']);kind=n['type'];nid=int(n['id'])
  if kind in ['CHANX','CHANY'] and c>0:
   assert nid not in ct;ct[nid]=truth.get(nid,0)/c
   for method,l in ledgers.items():cp[method][nid]=l.get(nid,0)/c
   loc=n['loc'];seg=int(n.get('segment',{}).get('segment_id',-1));layer=int(loc.get('layer','0'))
   for x in range(int(loc['xlow']),int(loc['xhigh'])+1):
    for y in range(int(loc['ylow']),int(loc['yhigh'])+1):
     key=(layer,x,y,kind,seg);caps[key]+=c;native[key]+=truth.get(nid,0)
     for method,l in ledgers.items():span[method][key]+=l.get(nid,0)
 assert stack.pop()==tag
 if tag=='rr_nodes':raise Finished()
parser=expat.ParserCreate();parser.StartElementHandler=start;parser.EndElementHandler=end
complete=False
with paths['graph'].open('rb') as f:
 try:parser.ParseFile(f)
 except Finished:complete=True
assert complete and len(ct)==primary['complete_channel_universe'] and len(caps)==primary['complete_spatial_universe']
st={k:native[k]/c for k,c in caps.items()};results={};toprows={}
for method in ledgers:
 sp={k:span[method][k]/c for k,c in caps.items()};results[method]={}
 for domain,pv,tv,k in [('concrete',cp[method],ct,max(1,len(ct)//20)),('spatial',sp,st,20)]:
  metric=compare(pv,tv,k);assert metric==primary['metrics'][method+'1_sketch'][domain]
  diag=tie_diagnosis(pv,tv,k);diag['scope']='Post-label bounds over truth-boundary ties for fixed predicted selection. Primary numeric-ID ordering and fixed k remain unchanged.';results[method][domain]=diag
 predicted=sorted(st,key=lambda k:(-sp[k],k))[:20];actual=set(sorted(st,key=lambda k:(-st[k],k))[:20])
 toprows[method]=[dict(bin=list(k),prediction=sp[k],native=st[k],frozen_native_top20=k in actual) for k in predicted]
assert all(sha(k)==h for k,h in bindings.items())
with (D/'verification.json').open('x') as f:json.dump(dict(bindings=bindings,all4_final_metric_sets_exactly_reproduced_by_independent_expat=True,complete_channels=len(ct),complete_bins=len(caps),ties=results,predicted_top20=toprows,primary_metrics_unchanged=True,heldout=False,promoted=False,scope='Known-label tie diagnostic only, not a replacement metric or native candidate QoR.'),f,indent=2);f.write('\n')
print(json.dumps(results,indent=2))
