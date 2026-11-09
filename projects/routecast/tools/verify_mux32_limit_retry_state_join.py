"""Join stable candidate endpoints/ledger to canonical native NET-name paths."""
import json
from collections import Counter,defaultdict
from pathlib import Path
from pre_route_endpoints import sha
from immutable_xml_prediction_audit import ImmutableXMLAudit
from native_route_ledger_import_compact import physical_paths
ROOT=Path(__file__).resolve().parents[1];candidate_base=ROOT/'experiments/mux32_limit_retry_tree_2026-10-07';canonical_base=ROOT/'experiments/mux32_limit_retry_canonical_2026-10-07';cp=candidate_base/'candidate.json';cv=candidate_base/'verification.json';nv=canonical_base/'verification.json';rp=canonical_base/'receipt.json';ep=ROOT/'experiments/mux_budget_move_cohort_2026-10-06/w32_m2/target_endpoints.json'
c=json.loads(cp.read_text());v=json.loads(cv.read_text());n=json.loads(nv.read_text());r=json.loads(rp.read_text());endpoints=json.loads(ep.read_text());assert v['candidate_sha256']==sha(cp) and n['receipt_sha256']==sha(rp);assert n['zero_fixups'] and n['joint_nonregression'];assert all(sha(f)==h for f,h in r['reload']['files'].items())
route=next(Path(f) for f in r['reload']['files'] if f.endswith('/design.route'));assert sha(route)==n['canonical_route_sha256'];graph=Path(endpoints['inputs']['graph']['path']);a=ImmutableXMLAudit(graph,endpoints['graph_sha256']);actual=physical_paths(route);expected=defaultdict(list);unions=defaultdict(set);queries={q['connection_id']:q for q in endpoints['connections']};assert len(c['records'])==len(queries)==1929
for record in c['records']:
 cid=record['connection_id'];q=queries[cid];assert (q['net_id'],q['source'],q['sink'])==(record['net_id'],record['source'],record['sink']);node=q['source'];path=[(node,None)]
 for eid in record['answer']['physical_edge_ids']:
  edge=a.graph.edges[eid];assert edge.source==node;node=edge.sink;path.append((node,edge.switch_id))
 assert node==q['sink'];name=endpoints['net_names'][str(q['net_id'])];expected[name].append(tuple(path));unions[q['net_id']].update(n for n,s in path)
assert {name:Counter(paths) for name,paths in expected.items()}=={name:Counter(tuple(p) for p in paths) for name,paths in actual.items() if paths}
ledger=Counter(node for used in unions.values() for node in used);assert dict(ledger)=={int(k):value for k,value in c['ledger'].items()};assert all(v<=a.caps[node] for node,v in ledger.items())
result=dict(source_sha256=sha(Path(__file__)),bindings={str(p):sha(p) for p in (cp,cv,nv,rp,ep,graph,route)},stable_connection_endpoints_joined=1929,canonical_name_path_multiplicities_match=True,canonical_ledger_matches_candidate=True,scope='Static canonical bundle joins exact original physical edge paths to every stable target connection and complete NET-union ledger. No live publication/concurrent transaction, prospective result or full-loop gain.')
(canonical_base/'state_join_verification.json').write_text(json.dumps(result,indent=2)+'\n');print('1929 stable endpoints and canonical ledger joined')
