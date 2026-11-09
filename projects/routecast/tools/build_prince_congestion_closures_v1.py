"""Label-free CHANNEL ownership overlap closures, two independent expansions."""
import json,xml.etree.ElementTree as ET
from pathlib import Path
from collections import defaultdict,Counter
from array import array
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'prince_congestion_closures_v1_2026-10-20'
def main():
 D.mkdir(exist_ok=False);policies={'dirty_0':('dirty',0),'dirty_1':('dirty',1),'dirty_2':('dirty',2),'dirty_fixedpoint':('dirty',None),'overuse_0':('overuse',0),'overuse_1':('overuse',1),'overuse_fixedpoint':('overuse',None)}
 protocol=dict(policies=policies,rule='Ownership graph NET<->CHANNEL resource from union of original source and native_retained target initializer node sets, positive CHANNEL capacities only. Dirty seeds from changed SOURCE/SINK pair; overuse seeds are dirty plus all owners of target initializer over-capacity CHANNELs. Synchronous overlap hops or exact connected-component closure, fixed policies no selection/tuning.',scope='Input-only developmental closure construction. Existing labels already exposed, no blindness/unseen claim. No target native route or occupancy supplied as input. No routing/forecast or original9 quality success implied.',bindings={str(Path(__file__)):sha(__file__)})
 (D/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');rows=[]
 for width in [128,160]:
  base=E/'prince_native_cohort_v1_2026-10-20'/f'w{width}';graph=base/'source/rr_graph.xml';dest=array('I')
  for event,x in ET.iterparse(graph):
   if x.tag=='edge':dest.append(int(x.get('sink_node')))
   x.clear()
  source=E/'prince_native_source_checkpoints_v1_2026-10-20'/f'w{width}'/'initial.json';sourceproof=source.parent/'independent_xml_verification_v1.json';old=json.loads(source.read_text());oldrows={x['connection_id']:x for x in old['records']};rp=E/'prince_quality_domains_v1_2026-10-20'/f'w{width}'/'resources.jsonl';caps={x['id']:x['capacity'] for x in map(json.loads,rp.open())}
  for episode in [1,2,3]:
   case=f'w{width}/episode_{episode:02d}';ep=base/f'episode_{episode:02d}'/'pre_route_endpoints.json';meta=json.loads(ep.read_text());warm=E/'prince_warm_initializers_v1_2026-10-20'/case/'native_retained';wp=warm/'verification.json';seedpath=warm/'initial.json';seed=json.loads(seedpath.read_text());bindings={str(p):sha(p) for p in [source,sourceproof,graph,rp,ep,wp,seedpath,D/'protocol.json']}
   for proof in [sourceproof,wp]:
    pv=json.loads(proof.read_text());assert all(sha(p)==h for p,h in pv['bindings'].items())
   assert meta['graph_sha256']==sha(graph)==old['graph_sha256']==seed['graph_sha256'];nets={x['net_id'] for x in seed['records']};dirty={x['net_id'] for x in meta['connections'] if (x['source'],x['sink'])!=(oldrows[x['connection_id']]['source'],oldrows[x['connection_id']]['sink'])};sets={net:set() for net in nets};seedsets={net:set() for net in nets}
   for frame,acc in [(old,sets),(seed,seedsets)]:
    for x in frame['records']:acc[x['net_id']].update(dest[eid] for eid in x['answer']['physical_edge_ids'] if dest[eid] in caps)
   counts=Counter(n for group in seedsets.values() for n in group);assert all(counts.get(n,0)==seed['ledger'].get(str(n),0) for n in caps)
   for net in nets:sets[net].update(seedsets[net])
   owners=defaultdict(set)
   for net,nodes in sets.items():
    for n in nodes:owners[n].add(net)
   over={n for n,count in counts.items() if count>caps[n]};seeds={'dirty':dirty,'overuse':dirty|{net for net,nodes in seedsets.items() if not nodes.isdisjoint(over)}};selected={};rounds={}
   for name,(origin,limit) in policies.items():
    current=set(seeds[origin]);history=[sorted(current)];step=0
    while limit is None or step<limit:
     touched={n for net in current for n in sets[net]};candidate=current|{net for n in touched for net in owners[n]}
     # Independent full NET scan against touched CHANNEL union.
     scan=current|{net for net,nodes in sets.items() if not nodes.isdisjoint(touched)};assert candidate==scan
     if candidate==current:break
     current=candidate;history.append(sorted(current));step+=1
    selected[name]=sorted(current);rounds[name]=history
   assert set(selected['dirty_0'])==dirty and set(selected['dirty_0'])<=set(selected['dirty_1'])<=set(selected['dirty_2'])<=set(selected['dirty_fixedpoint']);assert all(sha(p)==h for p,h in bindings.items());out=D/case;out.mkdir(parents=True);payload=dict(case=case,NETs=sorted(nets),dirty_NETs=sorted(dirty),overused_CHANNELs=sorted(over),policies=selected,rounds=rounds,bindings=bindings,label_inputs=False);sp=out/'selection.json';sp.write_text(json.dumps(payload,indent=2)+'\n');rows.append(dict(case=case,selection=str(sp),sha256=sha(sp)));print('CLOSURES',case,{name:len(s) for name,s in selected.items()},flush=True)
 (D/'verification.json').write_text(json.dumps(dict(rows=rows,bindings={str(D/'protocol.json'):sha(D/'protocol.json'),**{x['selection']:x['sha256'] for x in rows}},independent_owner_index_vs_full_NET_scan=True,scope=protocol['scope']),indent=2)+'\n')
if __name__=='__main__':main()
