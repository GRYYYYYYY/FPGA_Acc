"""Pool channel entry objectives across segments; raw electrical delays untouched."""
import sys,json,xml.etree.ElementTree as ET
from pathlib import Path
from array import array
from collections import Counter,defaultdict
from fractions import Fraction
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from class_cached_rc_endpoint_context_v1 import load_endpoints
from buffered_rc_node_classes import read,arc_delay
D=R/'experiments/freecores_segment_delay_pool_v1_2026-10-08';D.mkdir();bindings=closure([Path(__file__)]);cases=[]
for name in ['8051','xtea']:
 ep=R/'experiments/freecores_native_demand_v1_2026-10-08'/name/'endpoints.json';proof=ep.parent/'verification.json';v=json.loads(proof.read_text());assert v['exhaustive_disjoint_partition_exact_original_queries_and_whole_NET_scope_pass'] and all(sha(k)==h for k,h in v['bindings'].items());bindings[str(ep)]=sha(ep);bindings[str(proof)]=sha(proof);cases.append(dict(name=name,endpoint=str(ep)))
(D/'protocol.json').write_text(json.dumps(dict(bindings=bindings,cases=cases,group_key=['source_resource_type','target_CHANX/CHANY','target_direction'],rule='On positive-capacity source/target arcs entering CHANX/CHANY only, replace search objective by unweighted mean original full arc delay across all segment IDs in group. Round once to original integer RC lattice, half-up, error at most half lattice unit. Preserve nonchannel/disabled objectives exactly. Every original directed arc/switch ID and raw increment unchanged. Fixed full original RC initial floors/budgets and CHAN span/dynamic prices in eventual model.',scope='Component certification of segment-associated channel entry electrical objective equalization. No graph/length/segment metadata removal; labels/metrics never used to fit means. Existing cases are development. No model/native/heldout/timing/netgain admission yet.'),indent=2)+'\n');rows=[]
for case in cases:
 graph,digest,nodes,f,rc,queries=load_endpoints(case['endpoint']);ids,classes,switches,other=read(graph);assert digest==other;group_index={};keys=[];sums=Counter();counts=Counter();segments=defaultdict(Counter);slots=array('i',[-1])*len(rc.increments);initial_raw=array('Q',rc.increments)
 for u in range(len(nodes)):
  for slot in range(f['row_offsets'][u],f['row_offsets'][u+1]):
   v=f['dest_ranks'][slot]
   if f['capacities'][u]>0 and f['capacities'][v]>0 and nodes[v].get('type') in {'CHANX','CHANY'}:
    nr,nc=classes[ids[v]];assert nr==nc==0,'Current fixture channel self-RC assumption changed; review scope first'
    key=(nodes[u].get('type'),nodes[v].get('type'),nodes[v].get('direction','NONE'))
    if key not in group_index:group_index[key]=len(keys);keys.append(key)
    gid=group_index[key];slots[slot]=gid;sums[gid]+=rc.increments[slot];counts[gid]+=1;seg=nodes[v].find('segment');segments[gid][int(seg.get('segment_id')) if seg is not None else -1]+=1
 means={gid:(2*sums[gid]+counts[gid])//(2*counts[gid]) for gid in counts};assert all(abs(Fraction(sums[g],counts[g])-means[g])<=Fraction(1,2) for g in counts);objective=array('Q',(means[g] if g>=0 else raw for g,raw in zip(slots,rc.increments)));assert all(x<(1<<64) for x in objective);inverse=array('Q',[0])*len(f['edge_ids'])
 for slot,eid in enumerate(f['edge_ids']):inverse[eid]=slot
 # Independent original XML arc order and Fraction electrical recomputation, separate group accounting.
 independent_sums=Counter();independent_counts=Counter();components={};checked=changed=unchanged_outside=0;stack=[]
 for event,e in ET.iterparse(graph,events=('start','end')):
  if event=='start':stack.append(e);continue
  if e.tag=='edge':
   slot=inverse[checked];u=int(e.get('src_node'));v=int(e.get('sink_node'));sid=int(e.get('switch_id'));assert f['edge_ids'][slot]==checked and f['dest_ranks'][slot]==v and f['switch_ids'][slot]==sid and f['row_offsets'][u]<=slot<f['row_offsets'][u+1]
   pair=(ids[v],sid)
   if pair not in components:components[pair]=rc.encode(arc_delay(classes,switches,ids[v],sid))
   raw=components[pair];assert raw==rc.increments[slot]==initial_raw[slot]
   if f['capacities'][u]>0 and f['capacities'][v]>0 and nodes[v].get('type') in {'CHANX','CHANY'}:
    key=(nodes[u].get('type'),nodes[v].get('type'),nodes[v].get('direction','NONE'));independent_sums[key]+=raw;independent_counts[key]+=1;assert objective[slot]==means[group_index[key]]
   else:assert objective[slot]==raw;unchanged_outside+=1
   changed+=objective[slot]!=raw;checked+=1
  if e.tag in {'node','edge'}:
   if len(stack)>1:stack[-2].remove(e)
   e.clear()
  stack.pop()
 assert checked==len(rc.increments) and changed>0 and list(rc.increments)==list(initial_raw)
 for key,g in group_index.items():assert independent_sums[key]==sums[g] and independent_counts[key]==counts[g] and objective.count(means[g])>0
 w=D/case['name'];w.mkdir();op=w/'objective_CSR.bin';op.write_bytes(objective.tobytes());groups=[dict(key=list(keys[g]),arcs=counts[g],segment_arc_counts=dict(segments[g]),sum_raw_integer=sums[g],mean_objective_integer=means[g],rounding_error_integer_fraction=str(Fraction(means[g])-Fraction(sums[g],counts[g]))) for g in sorted(counts)]
 local={**bindings,str(graph):sha(graph),str(op):sha(op),str(D/'protocol.json'):sha(D/'protocol.json')};proof=dict(bindings=local,all_original_XML_raw_arcs_unchanged_and_pooled_objective_exact_pass=True,original_scale=rc.scale,original_graph_sha256=digest,nodes=len(nodes),arcs=checked,changed_objective_arcs=changed,outside_scope_unchanged_arcs=unchanged_outside,physical_queries=len(queries),groups=groups,objective_path=str(op),objective_byteorder=sys.byteorder,objective_itemsize=objective.itemsize,scope='Full directed original graph and original raw delays unchanged; channel entry objective homogenized across segment-associated switch delays. Channel self R/C zero certified. Equalization still preserves source type, destination orientation/polarity and later geometry span price. Not prediction/native/budget execution or gain proof.')
 assert all(sha(k)==h for k,h in local.items());(w/'verification.json').write_text(json.dumps(proof,indent=2)+'\n');bindings[str(w/'verification.json')]=sha(w/'verification.json');rows.append(dict(name=case['name'],arcs=checked,changed_objective_arcs=changed,groups=len(groups),physical_queries=len(queries)));print(case['name'],rows[-1],flush=True)
assert all(sha(k)==h for k,h in bindings.items());(D/'receipt.json').write_text(json.dumps(dict(bindings=bindings,rows=rows),indent=2)+'\n')
