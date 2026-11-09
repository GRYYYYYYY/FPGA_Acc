"""One fixed local batch; release witness owners, failed query first, reinsert all."""
import json,sys,time
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from nonzero_rc_endpoint_context import load_endpoints
from source_binding_v2 import closure
from tree_floor_predictor_seed_v2 import predict
base=R/'experiments/mcnc_prospective_v1_2026-10-07';dev=R/'experiments/mcnc_tree_floor_development_v1_2026-10-07';diag=R/'experiments/mcnc_floor_budget_failure_diagnosis_v1_2026-10-07';out=R/'experiments/mcnc_owner_reinsert_batch_v1_2026-10-07';out.mkdir();d=json.loads((diag/'receipt.json').read_text());inputs={str(diag/'receipt.json'):sha(diag/'receipt.json')};sources=closure([Path(__file__)])
for row in d['rows']:
 name=row['name'];ep=base/name/'endpoints.json';meta=json.loads(ep.read_text());inputs[str(ep)]=sha(ep);inputs.update({v['path']:v['sha256'] for v in meta['inputs'].values()})
 for file in (dev/f'{name}_tree1_floor1.json',dev/f'{name}_floors.json'):inputs[str(file)]=sha(file)
protocol=dict(inputs=inputs,sources=sources,selection='All exact owner NETs on archived first failed unrestricted minimum witness; fixed by prior diagnosis, no native labels',batch='Retain every other record and its parents, release whole owner NETs, route failed query first then all removed queries in NET/CID order; same input-floor budgets and tree minimum-delay objective. Commit only if every batch query succeeds; on failure published accepted state is original complete partial snapshot.',scope='One post-outcome development local batch each design. Not continuing whole uncompleted cohort or native proof. Partial working state archived for diagnosis but cannot replace original accepted state on failure.')
(out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');rows=[]
for row in d['rows']:
 name=row['name'];c=json.loads((dev/f'{name}_tree1_floor1.json').read_text());before=json.dumps(c,sort_keys=True);released=set(row['owner_release']['net_ids']);kept=[rec for rec in c['records'] if rec['net_id'] not in released];removed=[rec for rec in c['records'] if rec['net_id'] in released];queries=[row['query']]+[{k:rec[k] for k in ('connection_id','net_id','source','sink')} for rec in sorted(removed,key=lambda r:(r['net_id'],r['connection_id']))];tick=time.perf_counter();graph,digest,nodes,f,rc,_=load_endpoints(base/name/'endpoints.json');construction=time.perf_counter()-tick;floors={(q['source'],q['sink']):q['minimum_integer'] for q in json.loads((dev/f'{name}_floors.json').read_text())};tick=time.perf_counter();candidate=predict(f,rc,queries,floors,seed_records=kept);candidate.update(graph_sha256=digest,scale=rc.scale);search=time.perf_counter()-tick;commit=candidate['failure'] is None
 assert json.dumps(c,sort_keys=True)==before
 accepted=candidate if commit else c
 if commit:assert {r['connection_id'] for r in accepted['records']}=={r['connection_id'] for r in c['records']}|{row['query']['connection_id']}
 work=out/name;work.mkdir();(work/'working.json').write_text(json.dumps(candidate)+'\n');(work/'accepted.json').write_text(json.dumps(accepted)+'\n')
 rows.append(dict(name=name,released_net_ids=sorted(released),released_connections=len(removed),batch_queries=queries,committed=commit,failure=candidate['failure'],original_completed=c['completed_connections'],working_completed=candidate['completed_connections'],accepted_completed=accepted['completed_connections'],context_seconds=construction,search_seconds=search,files={str(p):sha(p) for p in work.iterdir() if p.is_file()}));print(name,commit,candidate['failure'],flush=True)
assert all(sha(p)==h for p,h in {**inputs,**sources}.items());(out/'receipt.json').write_text(json.dumps(dict(protocol_sha256=sha(out/'protocol.json'),rows=rows),indent=2)+'\n')
