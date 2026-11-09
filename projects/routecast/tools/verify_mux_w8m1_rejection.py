"""Independent full-node recurrence and direct native cold evidence checks."""
import json
from fractions import Fraction as F
from pathlib import Path
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[1];out=ROOT/'experiments/mux_w8m1_rejection_diagnosis_2026-10-06';file=out/'receipt.json';d=json.loads(file.read_text());assert all(sha(f)==h for f,h in d['bindings'].items());a=json.loads((ROOT/'experiments/mux_allfanin_budgets_2026-10-06/w8_m1.json').read_text());tg=json.loads((ROOT/'experiments/mux_old_full_timing_graph_2026-10-06/w8_timing_graph.json').read_text());mapping=json.loads((ROOT/'experiments/mux_full_timing_rr_2026-10-06/w8.json').read_text());coldroot=ROOT/'experiments/mux_full_cohort_cold_lifecycle_2026-10-06';cr=json.loads((coldroot/'receipt.json').read_text());cv=json.loads((coldroot/'verification.json').read_text());assert cv['receipt_sha256']==sha(coldroot/'receipt.json');native=next(r for r in cr['rows'] if (r['width'],r['index'])==(8,1));assert native['complete'] and native['error'] is None;rr=native['rounds'][0];assert rr['reload']['mismatches']==rr['reload']['fixups']==0 and rr['reload']['cpd_ns']==rr['native']['cpd_ns'];affected=set(map(str,a['affected']['affected_complete_net_connection_ids']));floor={cid:F(v) for cid,v in a['floor_ns'].items()};snapshot=json.loads((coldroot/'mux_w8_m1_0/accepted_state.json').read_text());actual={str(r['connection_id']):F(r['answer']['delay']*10**9,snapshot['scale']) for r in snapshot['records']};vectors=d['vectors_ns'];assert {cid:F(v) for cid,v in vectors['original_floor'].items()}==floor and {cid:F(v) for cid,v in vectors['cold_all'].items()}==actual
for name in ('floor_affected_cold_retained','cold_affected_old_retained'):
 expected={cid:(floor[cid] if cid in affected else actual[cid]) if name.startswith('floor') else (actual[cid] if cid in affected else floor[cid]) for cid in floor};assert expected=={cid:F(v) for cid,v in vectors[name].items()}
incoming={int(n):[] for n in tg['nodes']}
for eid,e in tg['edges'].items():
 if not e['disabled']:incoming[e['sink']].append((e['source'],eid))
for name,vector in vectors.items():
 b={cid:F(v) for cid,v in vector.items()};r=d['results'][name];arrival={int(n):F(v) for n,v in r['arrival_ns'].items()};assert set(arrival)==set(incoming)
 for n,edges in incoming.items():
  value=max([F(0)]+[arrival[u]+(b[str(a['edge_connection_ids'][eid])]+F(mapping['external_edges'][eid]['old_local_offset_seconds'])*10**9 if eid in a['edge_connection_ids'] else F(tg['edges'][eid]['max_delay_seconds'])*10**9) for u,eid in edges]);assert arrival[n]==value
 assert F(r['cpd_ns'])==max(arrival[int(n)] for n,kind in tg['nodes'].items() if kind=='SINK')
 assert arrival[r['worst_sink']]==F(r['cpd_ns'])
old=F(d['results']['original_floor']['cpd_ns']);transferred=F(d['results']['cold_all']['cpd_ns']);native_cpd=F(str(rr['native']['cpd_ns']));assert abs(transferred-native_cpd)<=F(1,100000)
assert old>F(d['target_ns']) and transferred<=F(d['target_ns']) and F(d['results']['floor_affected_cold_retained']['cpd_ns'])<=F(d['target_ns'])
changed={cid for cid in floor if cid not in affected and floor[cid]!=actual[cid]};assert changed=={str(r['connection_id']) for r in d['changed_retained_connections']};assert not d['cold_affected_below_diagnostic_floor'] and all(actual[cid]>=floor[cid] for cid in affected)
(out/'verification.json').write_text(json.dumps(dict(receipt_sha256=sha(file),verifier_sha256=sha(Path(__file__)),cold_verification_sha256=sha(coldroot/'verification.json'),native_cpd_ns=str(native_cpd),cold_transfer_cpd_ns=str(transferred),changed_retained_connections=len(changed),nodes_checked=len(incoming)*4,scope='Independent all-node incoming max recurrence, exact hybrid construction, native accepted CPD/zero fixup/source evidence. Retained-freeze scope explains observed mismatch; no independently certified minimum for original diagnostic affected floors or universal offset invariance.'),indent=2)+'\n');print('verified four transfers; retained scope difference,115 changed paths; native parity')
