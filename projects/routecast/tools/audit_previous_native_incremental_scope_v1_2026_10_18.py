"""Bounded lineage/dirty-NET audit; no target routing labels used in closure."""
import json,hashlib
from pathlib import Path
from collections import Counter
R=Path(__file__).resolve().parents[1]
D=R/'experiments/previous_native_incremental_scope_v1_2026-10-18'
D.mkdir(exist_ok=False)
bindings={}
def load(p):
 p=Path(p);raw=p.read_bytes();bindings[str(p)]=hashlib.sha256(raw).hexdigest();return json.loads(raw)
def bind(p):
 p=Path(p);bindings[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest()
p=load(R/'experiments/owner50_retained_rr_2026-10-07_predictor/protocol.json')
v=load(R/'experiments/retained_seed_session_native_cohort_v3_2026-10-08/verification.json')
rows=[]
for c in p['cases']:
 old=load(c['old']);target=load(c['target']);budget=load(c['budget'])
 a={q['connection_id']:q for q in old['connections']};b={q['connection_id']:q for q in target['connections']}
 assert a.keys()==b.keys()
 assert old['graph_sha256']==target['graph_sha256']
 assert old['inputs']['net']['sha256']==target['inputs']['net']['sha256']
 changed={cid for cid in a if (a[cid]['source'],a[cid]['sink'])!=(b[cid]['source'],b[cid]['sink'])}
 nets={b[cid]['net_id'] for cid in changed}
 closure={cid for cid in b if b[cid]['net_id'] in nets}
 source_changed={b[cid]['net_id'] for cid in changed if a[cid]['source']!=b[cid]['source']}
 route=Path(old['inputs']['graph']['path']).with_name('design.route');bind(route)
 forest=load(R/f"experiments/retained_seed_session_cohort_v3_2026-10-08/w{c['width']}_m{c['index']}/forest.json")
 reasons=Counter(x['reason'] for x in forest['released'])
 assert {x['connection_id'] for x in forest['released'] if x['reason']=='ENDPOINT_CHANGED'}==changed
 assert str(route) in forest['bindings'] and forest['bindings'][str(route)]==bindings[str(route)]
 native=next(x for x in v['rows'] if (x['width'],x['index'])==(c['width'],c['index']))
 rows.append(dict(width=c['width'],index=c['index'],connections=len(b),direct_dirty_connections=len(changed),dirty_nets=len(nets),whole_net_dirty_connections=len(closure),source_changed_nets=len(source_changed),release_reasons=dict(reasons),retained_connections=len(forest['retained']),original_budget_admitted=native['budget_admitted'],native_budget_violations=len(native['violation_ids']),previous_route=str(route),previous_place_sha256=old['inputs']['place']['sha256'],target_place_sha256=target['inputs']['place']['sha256'],budget_keys=list(budget)))
for n in ['retained_route_session_v2.py','retained_seed_session_v1.py','trial_retained_seed_session_cohort_v3.py','trial_retained_seed_session_native_cohort_v3.py']:bind(R/'tools'/n)
bind(Path(__file__))
report=dict(bindings=bindings,rows=rows,findings=dict(previous_native_route_provenance_checked=True,direct_dirty_release_exact=True,whole_net_closure_computed_from_endpoints_only=True,existing_policy='Per-connection endpoint and original budget retention; all connections scanned on each target; independent targets share fixed initial epoch, no accepted epoch advancement.',excluded_costs=['production of initial native route','endpoint and budget production','independent physical/canonical audits','final report serialization and driver gaps'],native_original_budget_admitted_cases=sum(x['original_budget_admitted'] for x in rows)),next_requirements=['Trace original budget generation and upstream paid prior-state preparation before selecting policy.','Use identical prior native state for both arms and permit equal incumbent/context reuse.','Freeze changed endpoint, whole-NET and shared-SOURCE closure; compare against full rebuild under identical frozen cost context.','Measure a continuous clock including preparation, update, native routing and required acceptance; separately identify shared initialization.','Advance accepted route epochs only after complete physical/pin/ledger and budget-policy acceptance.'],scope='Source/endpoint/archived-forest lineage review only. No new physical route replay, no budget feasibility proof, no novel mechanism or timing gain claimed.')
with (D/'verification.json').open('x') as f:json.dump(report,f,indent=2);f.write('\n')
print(json.dumps(dict(output=str(D),cases=len(rows),budget_admitted=sum(x['original_budget_admitted'] for x in rows),dirty=[{k:r[k] for k in ['width','index','direct_dirty_connections','whole_net_dirty_connections']} for r in rows]),indent=2))
