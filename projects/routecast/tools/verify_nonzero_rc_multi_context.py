"""Audit all generated paths, then independently replay complete finite-set UNSAT proof."""
import json
from pathlib import Path
from fractions import Fraction
from collections import defaultdict
from pre_route_endpoints import sha
from nonzero_rc_search_context import load
from immutable_xml_prediction_audit import ImmutableXMLAudit
from buffered_rc_node_classes import read,arc_delay
root=Path(__file__).resolve().parents[1];out=root/'experiments/nonzero_rc_multi_context_2026-10-06';r=json.loads((out/'receipt.json').read_text());assert sha(root/'tools/trial_nonzero_rc_multi_context.py')==r['source_sha256'] and sha(out/'protocol.json')==r['protocol_sha256'];graph,digest,nodes,f,rc,queries,_=load(root);audit=ImmutableXMLAudit(graph,r['graph_sha256']);ids,classes,switches,_=read(graph);required={(q['net_id'],q['pin_index']):q for q in queries};paths={};checked=0
for group in r['candidates']:
 key=tuple(group['key']);assert key in required and key not in paths;paths[key]=group['paths'];assert 1<=len(paths[key])<=36;q=required[key]
 for p in paths[key]:
  answer=p['answer'];assert answer['status']=='FOUND';node=q['source'];used={node};parents=[];res,cap=classes[ids[node]];delay=res*cap/2
  for eid in answer['physical_edge_ids']:e=audit.graph.edges[eid];assert e.source==node and e.sink not in used;node=e.sink;used.add(node);parents.append([node,e.source,eid]);delay+=arc_delay(classes,switches,ids[node],e.switch_id)
  assert node==q['sink'] and sorted(used)==p['nodes'] and parents==p['parents'];assert delay==Fraction(answer['delay'],r['scale'])<=Fraction(1,10**9);checked+=1
prior_dir=root/'experiments/nonzero_rc_pair_support_2026-10-06'
prior=json.loads((prior_dir/'receipt.json').read_text());assert r['pool_sha256']==sha(prior_dir/'receipt.json');old={tuple(g['key']):g['paths'] for g in prior['candidates']};context_found=0
for attempt in r['attempts']:
 key=tuple(attempt['key']);owners=defaultdict(set);parents=defaultdict(set);nets=set()
 for selected in attempt['selected']:
  support=tuple(selected['key']);assert key[0]!=support[0];nets.add(support[0]);p=old[support][selected['candidate']]
  for n in p['nodes']:owners[n].add(support[0])
  for n,u,eid in p['parents']:parents[(support[0],n)].add((u,eid))
 assert len(nets)>=2 and all(len(v)<=audit.caps[n] for n,v in owners.items()) and all(len(v)==1 for v in parents.values())
 other={n:len(v) for n,v in owners.items()};answer=attempt['answer']
 if answer['status']!='FOUND':continue
 q=required[key];node=q['source'];used={node};res,cap=classes[ids[node]];delay=res*cap/2;cost=0;assert other.get(node,0)<audit.caps[node]
 for eid in answer['physical_edge_ids']:
  e=audit.graph.edges[eid];assert e.source==node and e.sink not in used;node=e.sink;used.add(node);assert other.get(node,0)<audit.caps[node]
  increment=arc_delay(classes,switches,ids[node],e.switch_id);delay+=increment;cost+=increment*r['scale']*(1+other.get(node,0))
 assert node==q['sink'] and delay==Fraction(answer['delay'],r['scale'])<=Fraction(1,10**9) and cost==answer['cost'];context_found+=1
assert set(paths)==set(required)
assert r['status']=='GENERATED_NOT_SELECTED'
(out/'verification.json').write_text(json.dumps({'context_attempts_checked':len(r['attempts']),'context_found_witnesses_checked':context_found,'connections_with_candidates':len(paths),'candidate_paths_checked':checked,'selection_status':r['status'],'unsat_claimed':False,'complete_solution_claimed':False,'receipt_sha256':sha(out/'receipt.json'),'scope':'Independent original XML simple-path/exact1ns audit, reconstruction of other-NET occupancy and successful context query cost/capacity checks. Candidate generation only; selection and native FULL/STA remain unproven.'},indent=2)+'\n')
print('verified',checked,'paths,',len(r['attempts']),'contexts,',context_found,'successful context queries; generation only, no solution claim')
