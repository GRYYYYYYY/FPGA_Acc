"""Scope correction must not change any retained NET's initial floor/path/budget."""
import json,sys
from pathlib import Path
from collections import Counter,defaultdict
R=Path.cwd();sys.path.insert(0,str(R/'tools'))
from pre_route_endpoints import sha
from audit_native_route import NODE
from immutable_xml_prediction_audit import ImmutableXMLAudit
out=R/'experiments/aes_native_demand_estimates_v1_2026-10-08';bindings={str(Path(__file__)):sha(Path(__file__))};rows=[]
for name in ['aes_cipher','aes_inv_cipher']:
 new=out/name/'resident';old=R/f'experiments/aes_frozen_estimates_v1_2026-10-08/{name}/resident';frontend=R/f'experiments/aes_native_demand_frontend_v1_2026-10-08/{name}';files=[new/'initial.json',new/'floors.json',old/'initial.json',old/'floors.json',frontend/'endpoints.json',frontend/'scope_partition.json'];bindings.update({str(f):sha(f) for f in files});a=json.loads((old/'initial.json').read_text());b=json.loads((new/'initial.json').read_text());partition=json.loads((frontend/'scope_partition.json').read_text());mapping={x['physical_connection_id']:x['original_connection_id'] for x in partition['physical_to_original_connection_ids']};oldrecs={x['connection_id']:x for x in a['records']};oldfloors={(x['source'],x['sink']):x['minimum_integer'] for x in json.loads((old/'floors.json').read_text())};newfloors={(x['source'],x['sink']):x['minimum_integer'] for x in json.loads((new/'floors.json').read_text())}
 for rec in b['records']:assert rec=={**oldrecs[mapping[rec['connection_id']]],'connection_id':rec['connection_id']};assert newfloors[rec['source'],rec['sink']]==oldfloors[rec['source'],rec['sink']]
 ep=json.loads((frontend/'endpoints.json').read_text());graph=Path(ep['inputs']['graph']['path']);xml=ImmutableXMLAudit(graph,ep['graph_sha256']);removed=[x for cid,x in oldrecs.items() if cid not in set(mapping.values())];owned=defaultdict(set);independent=Counter()
 for x in removed:
  nodes={x['source']};nodes.update(xml.graph.edges[e].sink for e in x['answer']['physical_edge_ids']);owned[x['net_id']].update(nodes);independent.update(nodes)
 subtraction=Counter(n for nodes in owned.values() for n in nodes);expected=Counter({int(n):v for n,v in a['ledger'].items()});expected.subtract(subtraction);assert all(x>=0 for x in expected.values());assert {n:v for n,v in expected.items() if v}=={int(n):v for n,v in b['ledger'].items()}
 oldind=Counter({int(n):v for n,v in a['independent_connection_ledger'].items()});oldind.subtract(independent);assert all(x>=0 for x in oldind.values());assert {n:v for n,v in oldind.items() if v}=={int(n):v for n,v in b['independent_connection_ledger'].items()};bindings[str(graph)]=sha(graph);rows.append({'name':name,'retained_physical_queries':len(b['records']),'excluded_ignored_queries':len(removed),'all_retained_zero_price_initial_paths_floors_and_budgets_exact_parity':True,'both_initial_ledgers_exact_old_minus_ignored_contributions':True})
assert all(sha(k)==v for k,v in bindings.items());(out/'initial_scope_parity_verification.json').write_text(json.dumps({'bindings':bindings,'rows':rows},indent=2)+'\n');print(rows)
