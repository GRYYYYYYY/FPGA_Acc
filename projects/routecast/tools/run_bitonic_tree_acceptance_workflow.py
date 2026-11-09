"""Single-run serial prepared-input acceptance experiment, with explicit stage clocks."""
import json,time,runpy,contextlib,sys
from pathlib import Path
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[1];out=ROOT/'experiments/bitonic_tree_acceptance_workflow_2026-10-07';out.mkdir()
# Use new artifacts throughout; never combine elapsed times from old receipts.
tags=['bitonic_resident_live_staging','bitonic_resident_staging_native_import','bitonic_resident_staging_n4_canonical','bitonic_resident_staging_n8_canonical','bitonic_resident_staging_n16_canonical','bitonic_swapped_cold_n4_canonical','bitonic_swapped_cold_n8_canonical','bitonic_swapped_cold','bitonic_selected_state']
replacements=[(t,t.replace('bitonic_','bitonic_workflow_tree_',1)) for t in sorted(tags,key=len,reverse=True)]
files=['trial_bitonic_resident_live_staging.py','verify_bitonic_resident_live_staging.py','trial_bitonic_resident_staging_native_import.py',*[f'trial_bitonic_resident_staging_n{n}_canonical.py' for n in [4,8,16]],'verify_bitonic_resident_staging_canonical.py','capture_bitonic_swapped_cold.py','verify_bitonic_swapped_cold.py',*[f'trial_bitonic_swapped_cold_n{n}_canonical.py' for n in [4,8]],'verify_bitonic_swapped_cold_canonical.py','trial_bitonic_selected_state.py','verify_bitonic_selected_state.py']
paths={}
for name in files:
 text=(ROOT/'tools'/name).read_text()
 for a,b in replacements:text=text.replace(a,b)
 text=text.replace('owner_union_wire_rc_context_cached','owner_union_wire_rc_context_cached_tree')
 text=text.replace('bitonic_resident_staging_n{n}', 'bitonic_workflow_tree_resident_staging_n{n}').replace('bitonic_swapped_cold_n{n}', 'bitonic_workflow_tree_swapped_cold_n{n}')
 if name=='trial_bitonic_resident_live_staging.py':
  text=text.replace("order=['baseline','resident','resident','baseline']","order=['resident']").replace('ABBA within samecontext/seedledger','one resident staging attempt per case').replace('four ABBA','one resident')
 if name=='trial_bitonic_resident_staging_native_import.py':text=text.replace('run1_resident.json','run0_resident.json').replace("row['runs'][1]","row['runs'][0]")
 if name=='verify_bitonic_resident_live_staging.py':text=text.replace('all4_update_bytes_equal','single_update_verified').replace('all4_live_rollbacks_verified','live_rollback_verified').replace('four ABBA runs each','one resident run each')
 target=ROOT/'tools'/name.replace('bitonic_', 'bitonic_workflow_tree_',1);assert not target.exists();target.write_text(text);paths[name]=target
from freeze_priority_family import closure
protocol=dict(sources=closure([Path(__file__),*paths.values()]),scope='One resident attempt on each of three prepared swaps; fresh target frontend, context/seed import, staging, independent demand proof, candidate native/canonical validation, fresh cold oracle, cold canonical fallback, selected reload/endpoint/ledger proof. Serial stages share private same-tree/class-memo read-only RR cache; clocks include logging and proofs. Original mapped netlist/initial placement/seed routes/RR graph and tool compilation excluded. Full baseline and aggregate verification pending; not raw-input end-to-end or stable speedup.')
(out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');rows=[];tick=time.perf_counter()
def stage(name):
 p=paths[name];start=time.perf_counter()
 with (out/(name+'.log')).open('w') as f,contextlib.redirect_stdout(f),contextlib.redirect_stderr(f):runpy.run_path(str(p),run_name='__main__')
 rows.append(dict(stage=name,seconds=time.perf_counter()-start,log_sha256=sha(out/(name+'.log'))));(out/'receipt.json').write_text(json.dumps(dict(protocol_sha256=sha(out/'protocol.json'),stages=rows,complete=False,elapsed=time.perf_counter()-tick),indent=2)+'\n');print(name,rows[-1]['seconds'],flush=True)
from cached_rr_endpoint_context_tree import clear_cache
clear_cache()
for name in files:
 # canonical import needs authenticated raw import receipt, produced immediately after import.
 if name=='trial_bitonic_resident_staging_n4_canonical.py':
  p=ROOT/'experiments/bitonic_workflow_tree_resident_staging_native_import_2026-10-07';r=json.loads((p/'receipt.json').read_text());assert r['complete']
  for x in r['rows']:assert x['status']=='RAW_NATIVE_FULL_STA_SUCCESS' and all(sha(f)==h for f,h in x['files'].items())
  (p/'verification.json').write_text(json.dumps(dict(receipt_sha256=sha(p/'receipt.json'),scope='Raw import bound; canonical independent proof follows.'),indent=2)+'\n')
 stage(name)
assert all(sha(f)==h for f,h in protocol['sources'].items())
(out/'receipt.json').write_text(json.dumps(dict(protocol_sha256=sha(out/'protocol.json'),stages=rows,complete=True,workflow_seconds=time.perf_counter()-tick),indent=2)+'\n')
