"""Source-only initializer attribution, no target label reads or model search."""
import json,hashlib,xml.etree.ElementTree as ET
from pathlib import Path
from collections import defaultdict,Counter
from array import array
R=Path(__file__).resolve().parents[1];E=R/'experiments';I=E/'prospective_external_family_live_eligibility_trial_v1_2026-10-20';D=E/'source_to_warm_change_attribution_v1_2026-10-20'
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 cases=read(I/'protocol.json')['cases'];D.mkdir(exist_ok=False);bindings={str(Path(__file__)):sha(__file__)};done={}
 def admit(p):
  p=Path(p).resolve()
  if str(p) in done:return done[str(p)]
  d=read(p)
  for k,h in d['bindings'].items():
   if k in bindings:assert bindings[k]==h
   else:assert sha(k)==h;bindings[k]=h
  bindings[str(p)]=sha(p);done[str(p)]=d;return d
 meta=read(cases[0]['endpoint']);graph=Path(meta['inputs']['graph']['path']);assert sha(graph)==meta['graph_sha256'];caps={};types={};targets=array('Q');stack=[]
 for kind,el in ET.iterparse(graph,events=('start','end')):
  if kind=='start':stack.append(el);continue
  parent=stack[-2].tag if len(stack)>1 else None
  if (el.tag,parent)==('node','rr_nodes'):n=int(el.get('id'));caps[n]=int(el.get('capacity'));types[n]=el.get('type')
  if (el.tag,parent)==('edge','rr_edges'):targets.append(int(el.get('sink_node')))
  if (el.tag,parent) in [('node','rr_nodes'),('edge','rr_edges'),('switch','switches')]:stack[-2].remove(el);el.clear()
  stack.pop()
 def support(records):
  nets=defaultdict(set);inverse=defaultdict(set)
  for rec in records:nets[rec['net_id']].add(rec['source']);nets[rec['net_id']].update(targets[e] for e in rec['answer']['physical_edge_ids'])
  for net,nodes in nets.items():
   for node in nodes:inverse[node].add(net)
  return nets,inverse,Counter({node:len(owners) for node,owners in inverse.items()})
 rows=[]
 for case in cases:
  sp=admit(case['source_proof']);sourcepath=Path(case['source_frame']);assert sp['bindings'][str(sourcepath)]==sha(sourcepath);source=read(sourcepath);old={q['connection_id']:q for q in source['records']};oldnets,oldinverse,oldledger=support(source['records']);assert oldledger==Counter({int(n):v for n,v in source['ledger'].items()});assert all(v<=caps[n] for n,v in oldledger.items());current={q['connection_id']:q for q in read(case['endpoint'])['connections']};changed_endpoints={cid for cid,q in current.items() if (q['source'],q['sink'])!=(old[cid]['source'],old[cid]['sink'])};dirty={current[cid]['net_id'] for cid in changed_endpoints}
  for init in ['raw_min','native_retained']:
   folder=Path(case['warm'])/init;proof=admit(folder/'verification.json');warm=read(folder/'initial.json');assert proof['bindings'][str(folder/'initial.json')]==sha(folder/'initial.json');assert set(proof['dirty_nets'])==dirty;records={q['connection_id']:q for q in warm['records']};nets,inverse,ledger=support(warm['records']);assert ledger==Counter({int(n):v for n,v in warm['ledger'].items()});events=read(folder/'initializer_events.json');eventmap={q['net_id']:q for q in events};assert set(eventmap)==dirty if init=='native_retained' else events==[]
   counts=Counter();changed_paths=set();identical=set();pernet=[]
   for cid,new in records.items():
    prior=old[cid];same=(prior['source'],prior['sink'],prior['answer']['physical_edge_ids'])==(new['source'],new['sink'],new['answer']['physical_edge_ids']);category='endpoint_changed' if cid in changed_endpoints else 'endpoint_unchanged_in_dirty_NET' if new['net_id'] in dirty else 'outside_dirty_NET';counts[category]+=1;counts[category+('_path_unchanged' if same else '_path_changed')]+=1
    if same:identical.add(cid)
    else:changed_paths.add(cid)
    if category=='outside_dirty_NET':assert same
    if cid not in changed_endpoints:assert prior['answer']['delay']<=new['budget_integer']
   reconstructed=oldledger.copy()
   for net in dirty:
    for node in oldnets[net]-nets[net]:reconstructed[node]-=1
    reconstructed.update(nets[net]-oldnets[net])
   assert +reconstructed==ledger
   fallback=Counter();retained=[];attempted=[];repair_calls=0
   if init=='native_retained':
    for net,e in eventmap.items():
     retained.extend(e['retained_connection_ids']);attempted.extend(e['attempted_retained_connection_ids']);repair_calls+=e['repair_calls']
     if e['whole_NET_fallback']:fallback[e['fallback_reason']]+=1
     assert set(e['retained_connection_ids'])<=identical
     pernet.append(dict(net_id=net,connections=sum(q['net_id']==net for q in records.values()),endpoint_changed_CIDs=sum(current[cid]['net_id']==net for cid in changed_endpoints),retained=len(e['retained_connection_ids']),repair_calls=e['repair_calls'],fallback=e['whole_NET_fallback'],fallback_reason=e['fallback_reason'],owner_nodes_removed=len(oldnets[net]-nets[net]),owner_nodes_added=len(nets[net]-oldnets[net])))
    if not fallback:assert changed_paths==changed_endpoints and repair_calls==len(changed_endpoints)
   excess=[]
   for node,value in ledger.items():
    if value<=caps[node]:continue
    added=inverse[node]-oldinverse.get(node,set());assert added and added<=dirty
    excess.append(dict(node=node,type=types[node],capacity=caps[node],source_occupancy=oldledger.get(node,0),warm_occupancy=value,added_owner_NETs=sorted(added),warm_owner_NETs=sorted(inverse[node]),unchanged_NET_owners=sorted(inverse[node]-dirty)))
   counts['newly_overused_nodes']=len(excess);counts['newly_overused_units']=sum(x['warm_occupancy']-x['capacity'] for x in excess);counts['newly_overused_nodes_with_unchanged_NET_owner']=sum(bool(x['unchanged_NET_owners']) for x in excess);assert counts['newly_overused_units']==warm['overflow_units'];row=dict(case=case['case'],initializer=init,dirty_NETs=len(dirty),endpoint_changed_CIDs=len(changed_endpoints),counts=dict(counts),whole_NET_fallback_reasons=dict(fallback),attempted_retained_CIDs=len(attempted),retained_CIDs_in_dirty_NETs=len(retained),repair_calls=repair_calls,overused_node_types=dict(Counter(x['type'] for x in excess)),all_changes_reconstruct_by_dirty_NET_owner_replacements=True);rows.append(row);out=D/case['case']/init;out.mkdir(parents=True)
   for name,data in [('new_overuse_nodes.json',excess),('dirty_NETs.json',pernet)]:p=out/name;p.write_text(json.dumps(data,indent=2)+'\n');bindings[str(p)]=sha(p)
   print(json.dumps(row),flush=True)
 assert all(sha(k)==h for k,h in bindings.items());(D/'verification.json').write_text(json.dumps(dict(status='ALL6_SOURCE_TO_WARM_CID_OWNER_FALLBACK_AND_OVERUSE_ATTRIBUTIONS_VERIFIED',rows=rows,bindings=bindings,scope='Source and warm-only diagnosis, no target label reads. Unavoidable endpoint repair is physically necessary, not proof that predicted support or demand is correct. No new initializer or quality/net gain admission.'),indent=2)+'\n')
if __name__=='__main__':main()
