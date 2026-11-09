"""Audit all generated paths, then independently replay complete finite-set UNSAT proof."""
import json
from pathlib import Path
from fractions import Fraction
from collections import defaultdict
from pre_route_endpoints import sha
from nonzero_rc_search_context import load
from immutable_xml_prediction_audit import ImmutableXMLAudit
from buffered_rc_node_classes import read,arc_delay
root=Path(__file__).resolve().parents[1];out=root/'experiments/nonzero_rc_candidate_joint_selection_2026-10-06';r=json.loads((out/'receipt.json').read_text());assert sha(root/'tools/trial_nonzero_rc_candidate_joint_selection.py')==r['source_sha256'] and sha(out/'protocol.json')==r['protocol_sha256'];certificate=json.loads((out/'unsat_certificate.json').read_text());assert certificate['receipt_sha256']==sha(out/'receipt.json');graph,digest,nodes,f,rc,queries,_=load(root);audit=ImmutableXMLAudit(graph,r['graph_sha256']);ids,classes,switches,_=read(graph);required={(q['net_id'],q['pin_index']):q for q in queries};paths={};checked=0
for group in r['candidates']:
 key=tuple(group['key']);assert key in required and key not in paths;paths[key]=group['paths'];assert 1<=len(paths[key])<=4;q=required[key]
 for p in paths[key]:
  answer=p['answer'];assert answer['status']=='FOUND';node=q['source'];used={node};parents=[];res,cap=classes[ids[node]];delay=res*cap/2
  for eid in answer['physical_edge_ids']:e=audit.graph.edges[eid];assert e.source==node and e.sink not in used;node=e.sink;used.add(node);parents.append([node,e.source,eid]);delay+=arc_delay(classes,switches,ids[node],e.switch_id)
  assert node==q['sink'] and sorted(used)==p['nodes'] and parents==p['parents'];assert delay==Fraction(answer['delay'],r['scale'])<=Fraction(1,10**9);checked+=1
assert set(paths)==set(required);active={};states=0
def valid(key,path):
 demand=defaultdict(set);incoming=defaultdict(set)
 for k,p in [*active.items(),(key,path)]:
  for n in p['nodes']:demand[n].add(k[0])
  for n,u,eid in p['parents']:incoming[(k[0],n)].add((u,eid))
 return all(len(nets)<=audit.caps[n] for n,nets in demand.items()) and all(len(p)==1 for p in incoming.values())
def check(proof):
 global states
 states+=1;assert len(active)<len(paths)
 if 'dead_key' in proof:
  assert set(proof)=={'dead_key'};key=tuple(proof['dead_key']);assert key in paths and key not in active and not any(valid(key,p) for p in paths[key]);return
 assert set(proof)=={'key','children'};key=tuple(proof['key']);assert key in paths and key not in active;options=[i for i,p in enumerate(paths[key]) if valid(key,p)];assert options and [c['candidate'] for c in proof['children']]==options
 for child in proof['children']:
  active[key]=paths[key][child['candidate']];check(child['proof']);del active[key]
check(certificate['certificate']);assert states==certificate['states']==176 and r['status']=='CANDIDATE_SET_UNSAT';(out/'verification.json').write_text(json.dumps({'connections_with_candidates':len(paths),'candidate_paths_checked':checked,'unsat_proof_states_checked':states,'full_candidate_set_unsat_certified':True,'full_graph_unsat_claimed':False,'receipt_sha256':sha(out/'receipt.json'),'certificate_sha256':sha(out/'unsat_certificate.json'),'scope':'All original XML candidate paths and exact1ns delays independently checked; exhaustive proof covers every compatible branch under joint NET/node capacity and unique parent. Finite226-path set unsatisfiable; full graph remains feasible via independently audited native reference. No performance, generalization or predictor-completeness claim.'},indent=2)+'\n');print('verified',checked,'paths; UNSAT proof',states,'states')
