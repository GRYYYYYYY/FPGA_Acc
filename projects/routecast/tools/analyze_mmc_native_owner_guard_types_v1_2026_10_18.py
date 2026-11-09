"""Resource-type summaries after all-six independent trace replay; no new routing."""
import json,sys,xml.etree.ElementTree as E
from pathlib import Path
from collections import Counter,defaultdict
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from versioned_digest_cache_v1 import Cache
D=R/'experiments/mmc_native_owner_trace_replay_v2_2026-10-18';cp=D/'cohort_verification.json';C=json.loads(cp.read_text());assert C['all6_streamed_NET_ownership_checkpoints_final_unions_and_exact_counters_pass'];bindings={**C['bindings'],str(cp):sha(cp),**closure([Path(__file__)])}
cache=Cache()
with cache.installed():assert all(sha(p)==h for p,h in bindings.items())
epfile=R/'experiments/mmc_multiplacement_inputs_v1_2026-10-18/case_01/demand/endpoints.json';ep=json.loads(epfile.read_text());graph=Path(ep['inputs']['graph']['path']);assert sha(graph)==ep['graph_sha256'];codes={};kind_ids=bytearray();stack=[]
for event,e in E.iterparse(graph,events=('start','end')):
 if event=='start':stack.append(e);continue
 parent=stack[-2].tag if len(stack)>1 else None
 if e.tag=='node' and parent=='rr_nodes':
  assert int(e.get('id'))==len(kind_ids);name=e.get('type');code=codes.setdefault(name,len(codes));assert code<256;kind_ids.append(code);stack[-2].remove(e);e.clear()
 if e.tag=='rr_nodes':break
 stack.pop()
labels={v:k for k,v in codes.items()};rows=[]
for case in ['case_01','case_02','case_03']:
 for arm in ['off','on']:
  proof=D/case/(arm+'.json');V=json.loads(proof.read_text());assert V['status']=='pass';bindings[str(proof)]=sha(proof)
  trace=R/'experiments/mmc_native_owner_cascade_trace_v1_2026-10-18'/case/arm/'owner_trace.tsv';assert V['bindings'][str(trace)]==sha(trace)
  reasons=Counter();guard_types=Counter();guard_resources=defaultdict(set);per_iteration={};checkpoint=None;cp_nodes={};cp_types=Counter()
  for line in trace.open():
   tag=line.partition(' ')[0].rstrip()
   if tag=='Q':
    w=line.split();reason=w[4];it=int(w[2]);reasons[reason]+=1
    if reason=='overuse':
     node=int(w[5]);kind=labels[kind_ids[node]];guard_types[kind]+=1;guard_resources[kind].add(node)
   elif tag=='CP':
    w=line.split();checkpoint=(w[1],int(w[2]));cp_nodes={};cp_types=Counter()
   elif tag in ['B','E']:checkpoint=None
   elif tag=='V' and checkpoint:
    _,n,occ,cap=line.split();n=int(n);kind=labels[kind_ids[n]];assert n not in cp_nodes;cp_nodes[n]=(int(occ),int(cap));cp_types[kind]+=1
   elif tag=='CE' and checkpoint:
    name,it=checkpoint
    if name=='iteration_end_after_local_opins':
     expected=V['iteration_stats'][it-1];old_work=json.loads((R/'experiments/mmc_native_owner_cascade_trace_v1_2026-10-18'/case/arm/'equivalence.json').read_text())['row']['native_work']['rows'][it-1]
     assert len(cp_nodes)==old_work['overused_RR_nodes']
     per_iteration[str(it)]=dict(overused_RR_nodes=len(cp_nodes),overused_RR_types=dict(cp_types),single_overused_RR_node=next(iter(cp_nodes)) if len(cp_nodes)==1 else None,heap_pushes=expected['heap_pushes'],NET_operations=expected['NET_operations'])
    checkpoint=None
  assert dict(reasons)==V['first_true_native_guards'] and sum(guard_types.values())==reasons['overuse'] and len(per_iteration)==len(V['iteration_stats'])
  rows.append(dict(case=case,arm=arm,first_true_native_guards=dict(reasons),first_overuse_guard_RR_types=dict(guard_types),distinct_first_guard_RRs_by_type={k:len(x) for k,x in guard_resources.items()},iterations=per_iteration));print('NATIVE GUARD TYPES',case,arm,dict(guard_types),flush=True)
with cache.installed():assert all(sha(p)==h for p,h in bindings.items())
with (D/'guard_resource_type_diagnostic_v1.json').open('x') as f:json.dump(dict(status='pass',bindings=bindings,rows=rows,scope='Retrospective type of first-true overuse guard and all globally overused RR nodes at iteration-end checkpoints. First guard depends on native traversal order; no unique counterfactual cause or statement that masked force flags are absent. Single-node count does not imply the RR identity stays fixed. No new routing, candidate promotion or full-flow gain.'),f,indent=2)
print('ALL6GUARD RESOURCE TYPE DIAGNOSTICS CLOSED',flush=True)
