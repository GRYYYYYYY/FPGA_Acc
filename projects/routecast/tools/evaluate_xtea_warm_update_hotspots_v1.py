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
 start=time.perf_counter();out=R/'experiments/xtea_warm_update_hotspots_v1_2026-10-13';out.mkdir(exist_ok=False)
 bindings=closure([Path(__file__)])
 def load(p):
  bindings[str(p)]=sha(p);return json.loads(p.read_text())
 def admit(p,flag):
  v=load(p);assert v[flag];assert all(sha(q)==h for q,h in v['bindings'].items());bindings.update(v['bindings']);return v
 native_dir=R/'experiments/xtea_warm_native_comparison_v1_2026-10-13'
 admit(native_dir/'verification.json','all_three_native_physical_and_canonical_pass')
 paths={'warm_all':R/'experiments/xtea_warm_update_pair_v1_2026-10-13/all','warm_local':R/'experiments/xtea_warm_update_pair_v1_2026-10-13/local','fresh_full':R/'experiments/xtea_swap_fixed_epoch_full_pipeline_v1_2026-10-13'}
 ledgers={}
 for variant,d in paths.items():
  assert load(d/'pipeline_terminal.json')['all_stages_completed']
  for name in ['initial_physical_verification.json','sketch_physical_verification.json','verification.json']:
   admit(d/'model'/name,'all_original_queries_xml_fraction_rc_budgets_singleparent_and_uniqueNET_and_independent_ledgers_pass')
  for stage in ['initial','sketch']:
   state=load(d/'model'/(stage+'.json'));assert state['completed_connections']==state['required_connections']==2450
   ledgers[variant+'_'+stage]={int(n):v for n,v in state['ledger'].items()}
 assert ledgers['warm_all_initial']==ledgers['warm_local_initial']
 ep=load(R/'experiments/xtea_swap_native_demand_v1_2026-10-13/endpoints.json')
 assert all(sha(v['path'])==v['sha256'] for v in ep['inputs'].values())
 from audit_native_route import NET,NODE
 route=native_dir/'cold/output.route';bindings[str(route)]=sha(route);used={};net=None
 for line in route.read_text().splitlines():
  if m:=NET.match(line):
   net=int(m[1]);assert net not in used;used[net]=set()
  elif m:=NODE.match(line):
   assert net is not None;used[net].add(int(m[1]))
 native_counts=Counter(node for nodes in used.values() for node in nodes)
 proof=load(native_dir/'cold/physical_audit.json');assert dict(native_counts)=={int(n):v for n,v in proof['node_occupancy'].items()}
 truth={};bin_caps=Counter();bin_native=Counter();stack=[]
 for event,el in E.iterparse(ep['inputs']['graph']['path'],events=('start','end')):
  if event=='start':stack.append(el);continue
  if el.tag=='node':
   if el.get('type') in {'CHANX','CHANY'} and int(el.get('capacity'))>0:
    node=int(el.get('id'));assert node not in truth;capacity=int(el.get('capacity'));truth[node]=dict(capacity=capacity,native=native_counts[node]);loc=el.find('loc').attrib;seg=el.find('segment');sid=int(seg.get('segment_id')) if seg is not None else -1
    for x in range(int(loc['xlow']),int(loc['xhigh'])+1):
     for y in range(int(loc['ylow']),int(loc['yhigh'])+1):
      key=(int(loc.get('layer','0')),x,y,el.get('type'),sid);bin_caps[key]+=capacity;bin_native[key]+=native_counts[node]
   stack[-2].remove(el);el.clear()
  if el.tag=='rr_nodes':break
  stack.pop()
 bins={key:dict(capacity=value,native=bin_native[key]) for key,value in bin_caps.items()}
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
 assert checked==12 and all(sha(p)==h for p,h in bindings.items())
 (out/'verification.json').write_text(json.dumps(dict(bindings=bindings,metrics=result,metric_vectors_independently_recomputed=checked,complete_channel_universe=len(truth),complete_spatial_universe=len(cap),same_graph_endpoints_and_frozen_native_labels_pass=True,heldout_family=False,local_seconds=time.perf_counter()-start,scope='Swapped exposed XTEA cold-route labels only, complete positive CHAN and spatial span universes; fixed pre-move timing epoch for all three models. Warm all/local share full initial state and inherited history; fresh full is a separate starting-state comparator. No label-based fitting, heldout or native total-cost gain claim.'),indent=2)+'\n')
 print(json.dumps(result),flush=True)
if __name__=='__main__':main()
