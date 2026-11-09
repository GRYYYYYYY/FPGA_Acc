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
 start=time.perf_counter();out=R/'experiments/xtea_raw_floor_full_comparison_v1_2026-10-17';out.mkdir(exist_ok=False)
 bindings=closure([Path(__file__),R/'tools/evaluate_xtea_quotient_astar_full_comparison_v1.py'])
 def load(p):
  bindings[str(p)]=sha(p);return json.loads(p.read_text())
 def admit(p,flag):
  v=load(p);assert v[flag];assert all(sha(q)==h for q,h in v['bindings'].items());bindings.update(v['bindings']);return v
 models={'control1':R/'experiments/xtea_proxy_budget_audit_fixture_v1_2026-10-17/model','proxy1':R/'experiments/xtea_raw_floor_proxy_budget_fixture_v1_2026-10-17/model'}
 for variant,model in models.items():
  assert load(model.parent/'pipeline_terminal.json')['all_stages_completed']
  protocol=load(model/'protocol.json');assert protocol['present_factor']==int(variant[-1])
  for name in ['initial_physical_verification.json','sketch_physical_verification.json','verification.json']:
   proof=admit(model/name,'all_original_queries_xml_fraction_rc_budgets_singleparent_and_uniqueNET_and_independent_ledgers_pass')
   if name=='verification.json':assert proof['present_factor']==int(variant[-1]) and proof['independent_owner_sets_scaled_polynomial']
 closed=admit(models['proxy1'].parent/'closed_admission_v1.json','all_pass')
 assert closed['all_initial_nonpath_record_fields_equal_including_floors_budgets_and_delays']
 native_root=R/'experiments/freecores_native_cold_v1_2026-10-08/xtea'
 nativeproof=admit(native_root/'verification.json','all_physical_endpoints_original_XML_arcs_and_node_NET_capacity_pass')
 assert nativeproof['original_native_FULL_check_pass'] and nativeproof['overflow_units']==0
 physical=load(native_root/'physical_audit.json')
 assert physical['all_printed_branch_arc_switch_and_union_checks_pass'] and physical['overflow_units']==0
 physical_paths={'graph':R/'experiments/freecores_rr_only_v1_2026-10-08/xtea/rr_graph.xml','route':native_root/'output.route'}
 assert set(physical['inputs_sha256'])==set(physical_paths)
 assert all(sha(physical_paths[k])==h and nativeproof['bindings'][str(physical_paths[k])]==h for k,h in physical['inputs_sha256'].items())
 labels=R/'experiments/freecores_hotspots_v1_2026-10-08/xtea'
 admit(labels/'metric_verification.json','histogram_ranks_topk_mae_and_full_vector_scope_pass')
 labelproof=load(labels/'comparison.json');assert all(sha(q)==h for q,h in labelproof['bindings'].items());bindings.update(labelproof['bindings'])
 vectors=load(labels/'comparison_vectors.json');truth={x['node']:x for x in vectors['channels']};bins={tuple(x['key']):x for x in vectors['bins']}
 assert len(truth)==len(vectors['channels']) and len(bins)==len(vectors['bins'])
 assert all(v['native']==physical['node_occupancy'].get(str(n),0) for n,v in truth.items())
 ep=load(R/'experiments/freecores_native_demand_v1_2026-10-08/xtea/endpoints.json')
 assert all(sha(v['path'])==v['sha256'] for v in ep['inputs'].values())
 ledgers={}
 for variant,model in models.items():
  for stage in ['initial','sketch']:
   state=load(model/(stage+'.json'));assert state['completed_connections']==state['required_connections']==2450
   ledgers[variant+'_'+stage]={int(k):v for k,v in state['ledger'].items()}
 initial_ledgers_equal=ledgers['control1_initial']==ledgers['proxy1_initial']
 bridge=admit(R/'experiments/xtea_frozen_label_canonical_bridge_v1_2026-10-17/verification.json','all_original_frozen_occupancies_connections_and_NET_node_type_switch_sequences_identical')
 assert bridge['current_cold_canonical_ignored_only_semantic_gate_pass'] and not bridge['original_zero_counter_gate_pass']
 (out/'protocol.json').open('x').write(json.dumps(dict(bindings=bindings,
  methods=['control1','proxy1'],frames=['initial','sketch'],heldout=False,promoted=False,
  metrics='All8 sets: Spearman, precision/recall, MAE; original positive-capacity channels incl zero occupancy and full layer/direction/segment spans.',
  tie_rule='Existing XTEA numeric node IDs and numeric spatial tuples; descending value then ascending ID. Concrete k=max(1,N//20); spatial k=20. Deliberately preserve XTEA archived policy, do not mix with neuron lexical/ceil policy.',
  native_label_limit='Frozen physical labels exactly match newly canonical-audited cold route under ignored-pin semantic gate. Original zero-counter gate remains false. No new candidate native QoR claim.',
  comparison='Same exact floors, budget law, criticalities and feedback code. Initial equal-cost paths and ledgers may differ and change the full trajectory. No isolated direct causal recovery or unexposed design claim.'),indent=2)+'\n')
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
 (out/'verification.json').write_text(json.dumps(dict(bindings=bindings,metrics=result,initial_ledgers_equal=initial_ledgers_equal,metric_vectors_independently_recomputed=checked,complete_channel_universe=len(truth),complete_spatial_universe=len(cap),same_graph_endpoints_and_frozen_native_labels_pass=True,heldout_family=False,local_seconds=time.perf_counter()-start,methods=['control1','proxy1'],present_factor=1,quality_policy='Report both fixedfactor1 methods; no default promotion or metric selection.',scope='Known-label XTEA hybrid initial floors versus raw-only A* initial floors under the same proxy allowance at fixedfactor1 with same initial and fixed final round, unchanged full original channel/span domains and archived tie rule. Independent complete XML capacity/native aggregation and metric checks; frozen labels exactly bridge to current canonical ignored-pin semantic validation, original zero-counter gate remains false. No native candidate rerouting, heldout or paired/full-workflow speed proof.'),indent=2)+'\n')
 print(json.dumps(result),flush=True)
if __name__=='__main__':main()
