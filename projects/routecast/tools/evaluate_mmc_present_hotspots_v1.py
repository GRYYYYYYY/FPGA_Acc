"""Same authenticated frozen cold labels for both certified endogenous models."""
import ast,json,sys,math,time
import xml.etree.ElementTree as E
from pathlib import Path
from collections import Counter
R=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from prediction_metrics import compare

def main():
 start=time.perf_counter();out=R/'experiments/mmc_present_hotspots_v1_2026-10-10';out.mkdir(exist_ok=False)
 bindings=closure([Path(__file__)])
 def load(p):
  bindings[str(p)]=sha(p);return json.loads(p.read_text())
 def admit(p,flag):
  v=load(p);assert v[flag];assert all(sha(q)==h for q,h in v['bindings'].items());bindings.update(v['bindings']);return v
 new=R/'experiments/mmc_present_guard_complete_v1_2026-10-10'
 old=R/'experiments/mmc_resident_manifest_scope_seed_handoff_v1_2026-10-10/model'
 admit(new/'verification.json','complete_115572_connections_and_independent_physical_events_pass')
 admit(old/'shared_audit_receipt.json','all_three_complete_audits_pass')
 labels=R/'experiments/mmc_congestion_only_hotspots_v6_2026-10-10/mmc'
 admit(labels/'metric_verification.json','histogram_ranks_topk_mae_and_full_vector_scope_pass')
 labelproof=load(labels/'comparison.json');assert all(sha(q)==h for q,h in labelproof['bindings'].items());bindings.update(labelproof['bindings'])
 vectors=load(labels/'comparison_vectors.json');truth={x['node']:x for x in vectors['channels']};bins={tuple(x['key']):x for x in vectors['bins']}
 assert len(truth)==len(vectors['channels']) and len(bins)==len(vectors['bins'])
 ep=load(R/'experiments/ultraembedded_mmc_continuous_workflow_v6_2026-10-08/seed/demand/mmc/endpoints.json')
 lep=load(R/'experiments/ultraembedded_mmc_actual_old_linear_expat_workflow_v15_2026-10-10/seed/demand/mmc/endpoints.json')
 assert ep['graph_sha256']==lep['graph_sha256'] and ep['connections']==lep['connections'] and ep['net_names']==lep['net_names']
 ledgers={}
 for variant,model in [('original',old),('candidate',new/'model')]:
  for stage in ['initial','sketch']:
   state=load(model/(stage+'.json'));assert state['completed_connections']==state['required_connections']==115572
   ledgers[variant+'_'+stage]={int(k):v for k,v in state['ledger'].items()}
 graph=Path(ep['inputs']['graph']['path']);bindings[str(graph)]=sha(graph);assert bindings[str(graph)]==ep['graph_sha256']
 cap=Counter();native=Counter();pred={m:Counter() for m in ledgers};seen=set();stack=[]
 for event,el in E.iterparse(graph,events=('start','end')):
  if event=='start':stack.append(el);continue
  if el.tag=='node':
   if el.get('type') in {'CHANX','CHANY'} and int(el.get('capacity'))>0:
    node=int(el.get('id'));assert node in truth and node not in seen;seen.add(node)
    c=int(el.get('capacity'));assert c==truth[node]['capacity'];loc=el.find('loc').attrib;seg=el.find('segment');sid=int(seg.get('segment_id')) if seg is not None else -1
    for x in range(int(loc['xlow']),int(loc['xhigh'])+1):
     for y in range(int(loc['ylow']),int(loc['yhigh'])+1):
      key=(int(loc.get('layer','0')),x,y,el.get('type'),sid);cap[key]+=c;native[key]+=truth[node]['native']
      for m,l in ledgers.items():pred[m][key]+=l.get(node,0)
   stack[-2].remove(el);el.clear()
  if el.tag=='rr_nodes':break
  stack.pop()
 assert seen==set(truth) and set(cap)==set(bins)
 assert all(cap[k]==bins[k]['capacity'] and native[k]==bins[k]['native'] for k in cap)
 result={};global checked;checked=0
 source=R/'tools/verify_aes_native_demand_span_ablation_hotspots_v1.py';bindings[str(source)]=sha(source)
 fn=next(n for n in ast.parse(source.read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='audit_metric')
 exec(compile(ast.Module(body=[fn],type_ignores=[]),str(source),'exec'),globals())
 for m,l in ledgers.items():
  result[m]={}
  for scope,p,t,k in [('concrete',{n:l.get(n,0)/v['capacity'] for n,v in truth.items()},{n:v['native']/v['capacity'] for n,v in truth.items()},max(1,len(truth)//20)),('spatial',{key:pred[m][key]/cap[key] for key in cap},{key:native[key]/cap[key] for key in cap},20)]:
   metric=compare(p,t,k);audit_metric(p,t,metric,k);result[m][scope]=metric
 assert checked==8 and all(sha(p)==h for p,h in bindings.items())
 (out/'verification.json').write_text(json.dumps(dict(bindings=bindings,metrics=result,metric_vectors_independently_recomputed=checked,complete_channel_universe=len(truth),complete_spatial_universe=len(cap),same_graph_endpoints_and_frozen_native_labels_pass=True,heldout_family=False,local_seconds=time.perf_counter()-start,scope='Post-development initialized-base plus current occupancy snapshot comparison on exposed MMC; archived authenticated cold labels reused, complete positive CHAN and span universes independently matched to original XML. No native candidate routing, heldout, parameter fitting, causal quality or fullworkflow speed proof.'),indent=2)+'\n')
 print(json.dumps(result),flush=True)
if __name__=='__main__':main()
