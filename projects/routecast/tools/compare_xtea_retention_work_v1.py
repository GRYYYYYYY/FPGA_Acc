"""Full initial parity and certified event work comparison on exposed XTEA."""
import json,sys
from pathlib import Path
from fractions import Fraction
sys.path.insert(0,str(Path(__file__).resolve().parent/'native_resume_prototype'))
from source_binding_v2 import closure
from pre_route_endpoints import sha
from load_initial_connection_criticalities_v1 import load as load_criticalities
R=Path(__file__).resolve().parents[1];bindings=closure([Path(__file__)])
def load(p):bindings[str(p)]=sha(p);return json.loads(p.read_text())
paths={k:R/'experiments'/v for k,v in [('control','xtea_design_scoped_full_search_control_v1_2026-10-13'),('retained','xtea_design_scoped_retained_pipeline_v1_2026-10-13')]}
for p in paths.values():
 assert load(p/'pipeline_terminal.json')['all_stages_completed']
 for name in ['initial_physical_verification.json','sketch_physical_verification.json','verification.json']:
  v=load(p/'model'/name);assert v['all_original_queries_xml_fraction_rc_budgets_singleparent_and_uniqueNET_and_independent_ledgers_pass'];assert all(sha(q)==h for q,h in v['bindings'].items());bindings.update(v['bindings'])
for name in ['initial.json','floors.json']:
 a=paths['control']/'model'/name;b=paths['retained']/'model'/name
 assert load(a)==load(b) and sha(a)==sha(b)
initial=load(paths['control']/'model/initial.json');groups={}
for q in initial['records']:groups.setdefault(q['net_id'],[]).append(q['connection_id'])
cs=load_criticalities(R/'experiments/xtea_retained_native_inputs_v1_2026-10-13/criticality')
orders={n:sorted(ids,key=lambda i:(-Fraction(cs[i]['criticality_numerator'],cs[i]['criticality_denominator']),cs[i]['local_sink_pin'],i)) for n,ids in groups.items()}
results={}
for arm,p in paths.items():
 r=load(p/'model/receipt.json');rows=[]
 for rd in r['rounds']:
  calls=retained=fallback=0
  for e in rd['events']:
   ids=e['primary_search_connection_ids'];assert len(ids)==len(set(ids))==e['primary_search_calls']
   if arm=='control':
    expected=orders[e['net_id']]
    if 'fallback' in e:
     failed=set(e['primary_failed_connection_ids']);stop=next(i for i,cid in enumerate(expected) if cid in failed);expected=expected[:stop+1]
    assert ids==expected
   calls+=len(ids);retained+=len(e.get('retained_connection_ids',[]));fallback+=int('fallback' in e)
  assert len(rd['events'])==1448
  rows.append(dict(round_index=rd['round_index'],search_calls=calls,retained_connections=retained,fallback_events=fallback,overflow_units=rd['overflow_after']))
 results[arm]=dict(rounds=rows,timing={k:v for k,v in r.items() if k.endswith('_seconds')})
assert all(sha(p)==h for p,h in bindings.items())
out=R/'experiments/retained_tree_cross_design_readiness_v1_2026-10-13/xtea_single_factor_work_v1.json'
with out.open('x') as f:json.dump(dict(bindings=bindings,entire_initial_and_floors_equal=True,results=results,control_search_order_and_early_stop_counts_recomputed=True,paired_speedup_proven=False,scope='Certified complete same-input two-round comparison; timings single sequential historical runs with concurrent MMC, not repeated paired benchmark. Search call count is not expanded-node or fallback total-work count.'),f,indent=2)
print(json.dumps(results),flush=True)
