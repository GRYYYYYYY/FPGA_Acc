"""Independent full-node capacity/history and per-NET union occupancy diagnostic.
Does not certify tree arcs, pin coverage, delays, or reserved OPIN reconciliation.
"""
import json,sys,math,struct,xml.etree.ElementTree as E
from pathlib import Path
from collections import Counter
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1]
O=R/'experiments/mmc_native_iteration_state_observer_v1_2026-10-10'
v=json.loads((O/'verification.json').read_text());assert v['exit_status']==0 and v['route_bytes_equal_fully_audited_cold']
assert all(sha(p)==h for p,h in v['bindings'].items())
ep=R/'experiments/ultraembedded_mmc_continuous_workflow_v6_2026-10-08/seed/demand/mmc/endpoints.json'
e=json.loads(ep.read_text());graph=Path(e['inputs']['graph']['path']);assert sha(graph)==e['graph_sha256']
cap={};types={};stack=[]
for event,el in E.iterparse(graph,events=('start','end')):
 if event=='start':stack.append(el);continue
 if el.tag=='node':
  n=int(el.get('id'));assert n not in cap;cap[n]=int(el.get('capacity'));types[n]=el.get('type');stack[-2].remove(el);el.clear()
 if el.tag=='rr_nodes':break
 stack.pop()
assert len(cap)==904438
previous={n:1.0 for n in cap};rows=[]
def f32(x):return struct.unpack('f',struct.pack('f',x))[0]
for iteration in range(1,22):
 path=O/'states'/f'round_{iteration}.tsv';assert sha(path)==v['bindings'][str(path)]
 nodes={};owners=Counter();seen=set();roots=Counter();parents_by_net={};header=None
 with path.open() as s:
  for line in s:
   fields=line.split();tag=fields[0]
   if tag=='H':
    assert header is None;header=(int(fields[1]),float(fields[2]),float(fields[3]));assert header[0]==iteration and header[1]==v['iteration_pres_factors'][str(iteration)] and header[2]==(0.0 if iteration==1 else 1.0)
   elif tag=='N':
    n,occ,c=int(fields[1]),int(fields[2]),int(fields[3]);a=float(fields[4]);assert n in cap and n not in nodes and c==cap[n] and occ>=0 and math.isfinite(a)
    expected=f32(previous[n]+max(0,occ-c)*header[2]);assert f32(a)==expected,(iteration,n,a,expected)
    nodes[n]=(occ,a);previous[n]=f32(a)
   elif tag=='T':
    net,n,parent,switch=int(fields[1]),int(fields[2]),int(fields[3]),int(fields[4]);delay=float(fields[5]);assert n in cap and math.isfinite(delay) and delay>=0
    if (net,n) not in seen:owners[n]+=1;seen.add((net,n))
    if parent==-1:roots[net]+=1
    else:assert parent in cap
    parents_by_net.setdefault(net,set()).add((n,parent))
   else:raise AssertionError(tag)
 assert set(nodes)==set(cap) and all(c==1 for c in roots.values())
 for net,pairs in parents_by_net.items():
  for n,parent in pairs:assert parent==-1 or (net,parent) in seen
 mismatch=Counter();examples=[]
 for n,(occ,a) in nodes.items():
  if occ!=owners[n]:
   mismatch[(types[n],occ-owners[n])]+=1
   if len(examples)<12:examples.append({'node':n,'type':types[n],'occupancy':occ,'tree_NET_owners':owners[n]})
 rows.append({'iteration':iteration,'nodes':len(nodes),'tree_union_pairs':len(seen),'overflow_units':sum(max(0,occ-cap[n]) for n,(occ,a) in nodes.items()),'occupancy_owner_difference_groups':[{'type':t,'difference':diff,'nodes':count} for (t,diff),count in sorted(mismatch.items())],'examples':examples})
 print('STATE NODE AUDIT',iteration,len(nodes),sum(mismatch.values()),flush=True)
assert all(sha(p)==h for p,h in v['bindings'].items())
out={'bindings':{**v['bindings'],str(O/'verification.json'):sha(O/'verification.json'),str(graph):sha(graph),str(ep):sha(ep),str(Path(__file__).resolve()):sha(Path(__file__))},'all21rounds_full_XML_capacity_and_float32_history_recurrence_pass':True,'rows':rows,'scope':'Full RR capacity/history recurrence and tree parent presence/union diagnostic only. Tree edge/switch/RC/pin semantics not certified. Occupancy discrepancies explicitly reported, local OPIN reservations not reconciled. No native-equivalence/quality/heldout/speed proof.'}
f=O/'state_node_audit_v1.json';assert not f.exists();f.write_text(json.dumps(out,indent=2)+'\n')
