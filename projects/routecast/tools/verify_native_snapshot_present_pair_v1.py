"""Independent full paired path XML/Fraction/raw budget/scaled objective audit."""
import json,sys
from pathlib import Path
from fractions import Fraction
from collections import defaultdict,Counter
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from independent_fraction_arc_context_v2 import load_context,arc_delay
from exact_rc_lattice_direct_pairs_v2 import exact_scale
O=R/'experiments/mmc_native_snapshot_present_pair_v1_2026-10-10';N=R/'experiments/mmc_native_iteration_state_observer_v2_2026-10-10';T=R/'experiments/mmc_multiplicative_feedback_trial_v1_2026-10-10'
r=json.loads((O/'receipt.json').read_text());bindings={**r['bindings'],**closure([Path(__file__)]),str(O/'receipt.json'):sha(O/'receipt.json'),str(O/'events.jsonl'):r['events_sha256']};assert all(sha(p)==h for p,h in bindings.items())
ep=json.loads((R/'experiments/ultraembedded_mmc_continuous_workflow_v6_2026-10-08/seed/demand/mmc/endpoints.json').read_text());queries={q['connection_id']:q for q in ep['connections']};assert len(queries)==115572
xml,ids,classes,switches,digest=load_context(Path(ep['inputs']['graph']['path']),ep['graph_sha256']);scale,pairs=exact_scale(ids,classes,switches,xml.graph.edges)
old={x['connection_id']:x for x in json.loads((T/'model/initial.json').read_text())['records']};basefile=R/'experiments/mmc_native_node_base_mapping_v1_2026-10-10/node_base.u64'
from array import array
bases=array('Q');bases.frombytes(basefile.read_bytes());assert str(basefile) in bindings and sha(basefile)==bindings[str(basefile)]
crit=json.loads((R/'experiments/mmc_native_initial_criticality_snapshot_v2_2026-10-10/initial_connection_criticalities.json').read_text());bycid={x['connection_id']:x for x in crit}
import struct
values={cid:Fraction.from_float(struct.unpack('f',struct.pack('f',float(c['criticality_float32_text'])))[0]) for cid,c in bycid.items()}
state={};owners=defaultdict(set)
with (N/'states/round_1.tsv').open() as s:
 for line in s:
  f=line.split()
  if f[0]=='N':state[int(f[1])]=(int(f[2]),int(f[3]),Fraction(f[4]))
  elif f[0]=='T':owners[int(f[1])].add(int(f[2]))
counts={name:Counter() for name in ('unit','observed_round2')};seen=set();nets=set()
with (O/'events.jsonl').open() as s:
 for line in s:
  event=json.loads(line);net=event['net_id'];assert net not in nets;nets.add(net);order=event['order'];assert all(queries[cid]['net_id']==net for cid in order) and not seen.intersection(order);seen.update(order)
  expected=sorted(order,key=lambda cid:(-values[cid],bycid[cid]['local_sink_pin'],cid));assert order==expected
  for name,pf in [('unit',Fraction(1)),('observed_round2',Fraction(1,2))]:
   source=queries[order[0]]['source'];tree={source};parents={};assert [x['connection_id'] for x in event['modes'][name]]==order
   for rec in event['modes'][name]:
    cid=rec['connection_id'];q=queries[cid];status=rec['status'];counts[name][status]+=1
    if status=='UNREACHABLE':assert not rec['committed'] and 'physical_edge_ids' not in rec;continue
    assert status in ('COMMITTED','RETAIN_RAW_BUDGET');u=source;visited={u};a,b=classes[ids[u]];raw=a*b/2;congestion=Fraction(0);newparents={}
    for eid in rec['physical_edge_ids']:
     edge=xml.graph.edges[eid];assert edge.source==u and edge.sink not in visited and xml.graph.nodes[edge.sink].capacity>0;v=edge.sink;visited.add(v);newparents[v]=(u,eid);raw+=arc_delay(classes,switches,ids[v],edge.switch_id)
     if v not in tree:
      occ,cap,acc=state[v];other=occ-int(v in owners[net]);pressure=max(0,other-cap+1);congestion+=bases[v]*acc*(1+pressure*pf)
     else:assert parents.get(v)==(u,eid)
     u=v
    assert u==q['sink'];integer=raw*scale;assert integer.denominator==1 and rec['raw_unscaled']==int(integer) and rec['raw']==int(integer)*pf.denominator
    c=values[cid];objective=c*integer+(1-c)*congestion
    assert Fraction(rec['objective_numerator'],rec['objective_denominator']*pf.denominator)==objective
    passed=integer<=old[cid]['budget_integer'];assert rec['committed']==passed and (status=='COMMITTED')==passed
    if passed:
     for n,pair in newparents.items():assert n not in parents or parents[n]==pair;parents[n]=pair
     tree.update(visited)
assert seen==set(queries) and len(nets)==55300;assert {k:dict(v) for k,v in counts.items()}==r['counts'];assert all(sha(p)==h for p,h in bindings.items())
f=O/'verification.json';assert not f.exists();f.write_text(json.dumps({'bindings':bindings,'all115572_per_mode_XML_fraction_raw_budget_and_scaled_objectives_pass':True,'nets':len(nets),'counts':{k:dict(v) for k,v in counts.items()},'scope':'All attempted paired paths and committed local-tree parents audited. UNREACHABLE has no independent infeasibility certificate; no shortest-path proof on full graph, wholeNET fallback/atomic commit/overflow validation, native QoR or causal quality claim.'},indent=2)+'\n');print('PAIRED PATH AUDIT PASS')
