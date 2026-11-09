"""Authenticate full common-NET crossover and unchanged physical universe."""
import json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from pre_route_endpoints import sha
D=R/'experiments/freecores_common_NET_native_v1_2026-10-08';S=R/'experiments/freecores_common_NET_seed_v1_2026-10-08';bindings={str(Path(__file__)):sha(Path(__file__))}
def read(path):
 bindings[str(path)]=sha(path);data=json.loads(path.read_text())
 for group in ['bindings','files']:
  assert all(sha(k)==h for k,h in data.get(group,{}).items());bindings.update(data.get(group,{}))
 return data
r=read(D/'receipt.json');p=read(D/'protocol.json');s=read(S/'receipt.json');assert r['all_complete_native_physical_canonical_and_ignored_pass'] and len(r['rows'])==4 and [(x['name'],x['tree_mode']) for x in r['rows']]==[(n,m) for n in ['8051','xtea'] for m in ['baseline','no_ipin']];assert all(x['exit_code']==0 for x in r['ignored']);rows=[]
for mode in p['tree_modes']:
 ip=read(D/mode/'canonical/ignored_pin_verification_v1.json');assert len(ip['rows'])==2 and all(x['every_mismatch_matches_native_ignored_sink_pin'] and x['post_reload_packed_netlist_byte_identical'] and not x['strict_zero_counter_gate_pass'] for x in ip['rows'])
for name in p['cases']:
 arms={};identitysets={};ep=read(R/'experiments/freecores_native_demand_v1_2026-10-08'/name/'endpoints.json');allids={q['connection_id'] for q in ep['connections']};source=next(x for x in s['rows'] if x['name']==name)
 for mode in p['tree_modes']:
  row=next(x for x in r['rows'] if x['name']==name and x['tree_mode']==mode);assert row['exit_code']==0 and row['complete_native_FULL_and_physical_audit_pass'] and row['all_required_connections']==len(allids);assert all(sha(k)==h for k,h in row['files'].items());bindings.update(row['files']);cr=row['canonical'];assert cr['semantic_consistency_gate_pass'] and cr['exit_code']==0 and not cr['original_zero_counter_gate_pass'] and all(sha(k)==h for k,h in cr['files'].items());bindings.update(cr['files']);payload=read(S/name/mode/'subset.json');retained={x['connection_id'] for x in payload['records']};pending=set(payload['pending']);assert len(retained)==len(payload['records']) and retained.isdisjoint(pending) and retained|pending==allids and len(retained)==source['common_scope']['retained_connections'];identitysets[mode]=(retained,pending,set(payload['common_NETs']));
  for f in ['seed.route','design.blif','design.net','design.place']:assert sha(D/mode/name/f)==sha(S/name/mode/f)
  physical=read(D/mode/name/'physical_audit.json');assert physical['all_printed_branch_arc_switch_and_union_checks_pass'] and physical['overflow_units']==0 and len(physical['connections'])==len(allids)
  arms[mode]={k:row[k] for k in ['iterations','wirelength','diagnostic_cpd_ns','native_seconds','all_required_connections']}
 assert identitysets['baseline']==identitysets['no_ipin'];rows.append(dict(name=name,common_NET_count=source['common_NET_count'],common_changed_tree_NET_count=source['common_tree_changed_NET_count'],retained_connections=source['common_scope']['retained_connections'],pending_connections=source['common_scope']['pending_connections'],arms=arms))
assert all(sha(k)==h for k,h in bindings.items());(D/'verification.json').write_text(json.dumps(dict(bindings=bindings,all_same_complete_NET_and_CID_sets_physical_native_canonical_ignored_pin_pass=True,rows=rows,scope='Development tree-path crossover conditioned on intersection of both price-arm admissions; smaller identical seed sets, all pending physical work still routed. Historical broad seed arms not interchangeable with this conditioned experiment. Single fixed-seed diagnostic, no broad causal/generalization/stability/HDL/characterized async timing/fullworkflow gain claim; original nonzero ignored counters explicit.'),indent=2)+'\n');print(json.dumps(rows,indent=2))
