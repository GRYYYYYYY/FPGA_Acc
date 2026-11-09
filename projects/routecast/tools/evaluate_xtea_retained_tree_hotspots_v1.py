"""Same authenticated frozen cold labels for certified exposed-XTEA models."""
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
 start=time.perf_counter();out=R/'experiments/xtea_retained_tree_hotspots_v1_2026-10-13';out.mkdir(exist_ok=False)
 bindings=closure([Path(__file__)])
 def load(p):
  bindings[str(p)]=sha(p);return json.loads(p.read_text())
 def admit(p,flag):
  v=load(p);assert v[flag];assert all(sha(q)==h for q,h in v['bindings'].items());bindings.update(v['bindings']);return v
 new=R/'experiments/xtea_design_scoped_retained_pipeline_v1_2026-10-13'
 old=R/'experiments/freecores_resident_v1_2026-10-08/xtea/resident'
 assert load(new/'pipeline_terminal.json')['all_stages_completed']
 for model in [old,new/'model']:
  for name in ['initial_physical_verification.json','sketch_physical_verification.json','verification.json']:
   admit(model/name,'all_original_queries_xml_fraction_rc_budgets_singleparent_and_uniqueNET_and_independent_ledgers_pass')
 labels=R/'experiments/freecores_hotspots_v1_2026-10-08/xtea'
 admit(labels/'metric_verification.json','histogram_ranks_topk_mae_and_full_vector_scope_pass')
 labelproof=load(labels/'comparison.json');assert all(sha(q)==h for q,h in labelproof['bindings'].items());bindings.update(labelproof['bindings'])
 vectors=load(labels/'comparison_vectors.json');truth={x['node']:x for x in vectors['channels']};bins={tuple(x['key']):x for x in vectors['bins']}
 assert len(truth)==len(vectors['channels']) and len(bins)==len(vectors['bins'])
 ep=load(R/'experiments/freecores_native_demand_v1_2026-10-08/xtea/endpoints.json')
 assert all(sha(v['path'])==v['sha256'] for v in ep['inputs'].values())
 ledgers={}
 for variant,model in [('archived_original',old),('candidate',new/'model')]:
  for stage in ['initial','sketch']:
   state=load(model/(stage+'.json'));assert state['completed_connections']==state['required_connections']==2450
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
 (out/'verification.json').write_text(json.dumps(dict(bindings=bindings,metrics=result,metric_vectors_independently_recomputed=checked,complete_channel_universe=len(truth),complete_spatial_universe=len(cap),same_graph_endpoints_and_frozen_native_labels_pass=True,heldout_family=False,local_seconds=time.perf_counter()-start,scope='Exposed XTEA portability evaluation of retained criticality full schedule versus archived original model; multi-factor historical comparison, not an isolated retention ablation; archived authenticated cold labels reused, complete positive CHAN and span universes independently matched to original XML. No native candidate routing, heldout, parameter fitting, causal quality or fullworkflow speed proof.'),indent=2)+'\n')
 print(json.dumps(result),flush=True)
if __name__=='__main__':main()
