"""Attach exact real repair-path/price checks to independent original event replay.

Does not independently certify omitted label frontier or cached bound values.
"""
import json,sys,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1]
source=(R/'tools/verify_external_primary_budget_repair_events_v1.py').read_text()
anchor='for index,roundrow in enumerate(r[\'rounds\']):'
setup=r'''
from array import array
bindings[str(R/'tools/verify_external_primary_budget_repair_events_v1.py')]=sha(R/'tools/verify_external_primary_budget_repair_events_v1.py')
repair_path=out/'primary_budget_repairs.json'
repairs=json.loads(repair_path.read_text());bindings[str(repair_path)]=sha(repair_path)
repair_groups=defaultdict(list)
for ri,repair in enumerate(repairs):repair_groups[repair['round_index'],repair['net_id'],repair['occupancy_snapshot_ticket']].append((ri,repair))
needed={slot for repair in repairs if repair['status']=='FOUND' for slot in repair['path_slots']}
rowsizes=[0]*len(xml.graph.nodes)
for eid in range(len(xml.graph.edges)):rowsizes[xml.graph.edges[eid].source]+=1
csr=[0]
for size in rowsizes:csr.append(csr[-1]+size)
cursor=csr[:-1].copy();slot_edges={};dest_by_slot=array('Q',[0])*len(xml.graph.edges);raw_by_slot=[0]*len(xml.graph.edges)
for eid in range(len(xml.graph.edges)):
 edge=xml.graph.edges[eid]
 slot=cursor[edge.source];cursor[edge.source]+=1;dest_by_slot[slot]=edge.sink
 raw=arc_delay(classes,switches,ids[edge.sink],edge.switch_id)*scale;assert raw.denominator==1;raw_by_slot[slot]=raw.numerator
 if slot in needed:slot_edges[slot]=(eid,edge)
assert set(slot_edges)==needed
context_hash=hashlib.sha256();context_hash.update(array('Q',csr).tobytes());context_hash.update(dest_by_slot.tobytes())
for raw in raw_by_slot:context_hash.update(raw.to_bytes(16,'little'))
context_digest=context_hash.hexdigest();repair_checked=set();repair_counts=Counter()
'''
assert source.count(anchor)==1;source=source.replace(anchor,setup+'\n'+anchor)
anchor="  eligible=[]"
checks=r'''
  for ri,repair in repair_groups.get((index,net,event['occupancy_snapshot_ticket']),[]):
   assert ri not in repair_checked;repair_checked.add(ri);repair_counts[repair['status']]+=1
   assert repair['source']==old[0]['source'] and repair['original_raw']>repair['budget'] and repair['label_limit']==10000 and 0<=repair['labels_created']<=10000
   assert repair['bound_target']==repair['target'] and repair['bound_cap']==repair['budget']+1 and repair['bound_context_sha256']==context_digest
   pnum,qden=repair['criticality_numerator'],repair['criticality_denominator'];cval=Fraction(pnum,qden)
   matching=[rec for rec in old if rec['sink']==repair['target'] and rec['budget_integer']==repair['budget'] and criticalities[rec['connection_id']]==cval];assert matching
   initial={int(node):value for node,value in repair['initial_arrivals']};assert len(initial)==len(repair['initial_arrivals']) and repair['source'] in initial
   if repair['status']=='FOUND':
    u=repair['join'];assert u in initial;raw=initial[u];seen=set(initial);used=[]
    for slot in repair['path_slots']:
     eid,edge=slot_edges[slot];assert edge.source==u and edge.sink not in seen and xml.graph.nodes[edge.sink].capacity>0;u=edge.sink;seen.add(u);raw+=raw_by_slot[slot]
     accumulated=prices.get(u,0)-span_prices.get(u,0);assert accumulated>=0
     price=node_base[u]*(1+accumulated)*(1+max(0,ledger.get(u,0)-(u in transaction_old_nodes)-xml.graph.nodes[u].capacity+1))+p['price_unit_integer']*span_prices.get(u,0);used.append([u,price])
    assert used==repair['tail_node_prices'] and u==repair['target'] and raw==repair['raw']<=repair['budget']
    assert repair['objective_denominator']==qden and repair['objective_numerator']==pnum*raw+(qden-pnum)*sum(v for n,v in used)
   elif repair['status']=='UNKNOWN_LABEL_LIMIT':assert repair['labels_created']==10000
   else:assert repair['status']=='NO_BUDGET_PATH_FOR_FIXED_TREE'
'''
assert source.count(anchor)==1;source=source.replace(anchor,checks+'\n'+anchor)
source+='''\nassert repair_checked==set(range(len(repairs)))\nPath(sys.argv[4]).resolve().write_text(json.dumps(dict(status='ALL_REAL_PRIMARY_REPAIR_CONTEXT_PATH_PRICES_RAW_BUDGETS_AND_OBJECTIVE_CHECKED',case=name,repairs=len(repairs),status_counts=dict(repair_counts),bindings=bindings,scope='Independent original XML CSR/raw hash and event owner-excluded price replay. Success tail paths/objectives and label status domains verified. Initial partial-tree seed provenance, omitted Pareto frontier optimality and cached potential Bellman inequalities not independently reconstructed here; no failure infeasibility claim.'),indent=2)+'\\n')\nprint('PRIMARY_REPAIR_TRACE_CHECKED',len(repairs),dict(repair_counts),flush=True)\n'''
# Execute retained independent full-frame/event replay plus narrow trace assertions.
exec(compile(source,str(Path(__file__).resolve()),'exec'))
