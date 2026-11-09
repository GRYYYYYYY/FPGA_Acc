"""Independent physical audit of all saved branch states, including failures."""
import sys,json
from pathlib import Path
from collections import Counter,defaultdict
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from nonzero_rc_endpoint_context import load_endpoints
from immutable_xml_prediction_audit import ImmutableXMLAudit
out=R/'experiments/misex_window_witness_guided_joint_v1_2026-10-07';r=json.loads((out/'receipt.json').read_text());bindings={**r['bindings'],**r['files'],**closure([Path(__file__)]),str(out/'receipt.json'):sha(out/'receipt.json')};receipt=dict(rows=[dict(name='misex3')]);eventfile=out/'event.json';event=json.loads(eventfile.read_text());results=r['attempts']
assert all(sha(k)==v for k,v in bindings.items());(out/'branch_verification_dedup_protocol.json').write_text(json.dumps(dict(bindings=bindings))+'\n');rows=[]
for row in receipt['rows']:
 name=row['name'];base=R/'experiments/mcnc_prospective_v1_2026-10-07'/name;graph,digest,nodes,f,rc,queries=load_endpoints(base/'endpoints.json');ep=json.loads((base/'endpoints.json').read_text());audit=ImmutableXMLAudit(graph,digest);querymap={q['connection_id']:q for q in queries};slots={e:s for s,e in enumerate(f['edge_ids'])};count=0;proof_memo={};unique_states=0
 for directory in sorted(out.glob('attempt*_branch*')):
  index=int(directory.name.split('_')[0][7:]);meta=json.loads((directory/'branch.json').read_text());assert meta['released_net_ids']==results[index]['release'];assert meta['branch']==results[index]['branches'][meta['branch']['index']];release=set(meta['released_net_ids']);assert results[index]['removed_connection_ids']==[rec['connection_id'] for rec in event['before_records'] if rec['net_id'] in release];kept={r['connection_id']:r for r in event['before_records'] if r['net_id'] not in release};allowed={r['connection_id'] for r in event['before_records']}|set(event['selection']['requested_connection_ids'])
  for file in sorted(directory.glob('net*.json'))+sorted(directory.glob('joint_candidate.json')):
   file_digest=sha(file)
   assert file_digest==r['files'][str(file)]
   if file_digest in proof_memo:
    records,used_by_net=proof_memo[file_digest];assert set(records)<=allowed and all(records[cid]==rec for cid,rec in kept.items())
    for net,node in meta['branch']['constraints']:assert node not in used_by_net.get(net,set())
    if file.name=='joint_candidate.json':assert set(records)==allowed
    count+=1;continue
   unique_states+=1
   state=json.loads(file.read_text());records={r['connection_id']:r for r in state['records']};assert len(records)==len(state['records']) and set(records)<=allowed and all(records[cid]==r for cid,r in kept.items());parents=defaultdict(dict)
   for rec in records.values():
    q=querymap[rec['connection_id']];assert all(q[k]==rec[k] for k in ('net_id','source','sink'));edges=rec['answer']['physical_edge_ids'];assert rc.path(rec['source'],rec['sink'],edges)==rec['answer']['delay']<=rec['budget_integer'];u=rec['source']
    for e in edges:
     arc=audit.graph.edges[e];assert arc.source==u;incoming=(u,e);u=arc.sink;assert u not in parents[rec['net_id']] or parents[rec['net_id']][u]==incoming;parents[rec['net_id']][u]=incoming
    forbidden={node for net,node in meta['branch']['constraints'] if net==rec['net_id']};used={rec['source']}|{f['dest_ranks'][slots[e]] for e in edges};assert not forbidden.intersection(used)
   connections=[dict(q,method='searched' if q['connection_id'] in records else 'failed',physical_edge_ids=records[q['connection_id']]['answer']['physical_edge_ids'] if q['connection_id'] in records else None) for q in queries];adapted=dict(connections=connections,physical_graph_sha256=digest,node_occupancy={str(k):v for k,v in state['ledger'].items()},methods=dict(Counter(q['method'] for q in connections)),completed=len(records),requested=len(queries));proof=audit.verify(ep,adapted);assert proof['all_physical_and_union_checks_passed'] and proof['all_type_overuse_units']==0
   if file.name=='joint_candidate.json':assert set(records)==allowed
   used_by_net=defaultdict(set)
   for rec in records.values():used_by_net[rec['net_id']].add(rec['source']);used_by_net[rec['net_id']].update(f['dest_ranks'][slots[e]] for e in rec['answer']['physical_edge_ids'])
   proof_memo[file_digest]=(records,used_by_net)
   count+=1
 rows.append(dict(name=name,states=count,unique_physical_state_audits=unique_states,all_xml_rc_parents_capacity_constraints_and_unaffected_checks_pass=True));print('PASS branches',name,count,flush=True)
assert all(sha(k)==v for k,v in bindings.items());(out/'branch_verification_dedup.json').write_text(json.dumps(dict(bindings=bindings,rows=rows,scope='All archived low-level states and merged candidates, including failed branches; no native proof.'),indent=2)+'\n')
