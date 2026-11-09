"""Check unchanged-placement control vs old state and target m2 cold route."""
import json
from collections import Counter
from pathlib import Path
from pre_route_endpoints import sha
from native_route_ledger_import_compact import physical_paths
ROOT=Path(__file__).resolve().parents[1]
base=ROOT/'experiments/mux32_old_placement_cold_control_2026-10-07'
rp,pp=base/'receipt.json',base/'protocol.json';r,p=json.loads(rp.read_text()),json.loads(pp.read_text())
assert r['protocol_sha256']==sha(pp) and r['native_exit_code']==0 and r['target_endpoints_match']
assert r['canonical']['mismatches']==r['canonical']['fixups']==0
assert all(sha(f)==h for f,h in {**p['sources'],**p['inputs'],**r['files'],**r['canonical']['files']}.items())
old=ROOT/'experiments/mux_old_full_timing_graph_2026-10-06/w32/canonical/design.route'
original=ROOT/'work/mux_crossbar_channel_pressure_2026-10-06/mux_w32_c128/design.route'
control=base/'canonical/design.route'
target=ROOT/'experiments/mux_full_cohort_cold_lifecycle_2026-10-06/mux_w32_m2_0/canonical/design.route'
churn=ROOT/'experiments/unchanged_net_route_churn_2026-10-07/diagnosis.json';ch=json.loads(churn.read_text())
assert sha(original)==ch['bindings'][str(original)] and sha(target)==ch['bindings'][str(target)]
oldreceipt=ROOT/'experiments/mux_old_full_timing_graph_2026-10-06/receipt.json'
orow=next(x for x in json.loads(oldreceipt.read_text())['rows'] if x['width']==32);assert sha(old)==orow['files'][str(old)]
paths=[{name:Counter(rows) for name,rows in physical_paths(f).items() if rows} for f in (original,old,control,target)]
assert paths[0]==paths[1] and paths[1]==paths[2]
assert paths[2].keys()==paths[3].keys()
changes=[name for name in paths[2] if paths[2][name]!=paths[3][name]]
log=(base/'route.log').read_text();assert 'VPR succeeded' in log and 'Completed routing consistency check successfully.' in log
result=dict(bindings={str(f):sha(f) for f in (rp,pp,oldreceipt,original,old,control,target,churn,Path(__file__))},control_matches_original_all_named_path_multisets=True,control_matches_old_canonical_all_named_path_multisets=True,connections=sum(sum(counts.values()) for counts in paths[2].values()),target_changed_named_path_nets=len(changes),target_changed_net_names=changes,cpd_ns=r['cpd_ns'],wirelength=r['wirelength'],prepared_route_and_proof_seconds=r['external_wall_seconds'],scope='One original-placement cold control: all1929 original/oldcanonical paths exactly reproduced using current target-cohort routing protocol and explicit default seed1. Excludes workflow mismatch as explanation for this single w32/m2 comparison; not proof of cross-seed nondeterminism absence or incremental mandatory reroutes. New target cold was archived, not rerun now; no netgain or heldout.')
assert result['connections']==1929
(base/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print({k:result[k] for k in ('connections','target_changed_named_path_nets','control_matches_original_all_named_path_multisets')})
