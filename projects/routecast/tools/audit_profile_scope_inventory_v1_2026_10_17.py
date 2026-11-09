"""Authenticate archived profiles while preserving incompatible workload scopes."""
import json,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1]
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
paths=[
 'sha_complete_model_handoff_profile_v2_2026-10-10/receipt.json',
 'sha_complete_model_handoff_profile_v2_2026-10-10/handoff/receipt.json',
 'sha_complete_model_handoff_profile_v2_2026-10-10/function_costs.json',
 'mmc_complete_actual_old_fallback_profile_v1_2026-10-10/verification.json',
 'profile_native_owner_transactions_v4_2026-10-08/verification.json',
 'profile_incremental_owner_transactions_v1_2026-10-08/verification.json',
 'profile_native_owner_potential_buffers_paired_v1_2026-10-08/verification.json']
rows=[];bindings={str(Path(__file__).resolve()):sha(__file__)}
for name in paths:
 p=R/'experiments'/name;d=json.loads(p.read_text());checks=[]
 for section in ['bindings','files']:
  for k,h in d.get(section,{}).items():
   q=Path(k);actual=sha(q) if q.is_file() else None
   checks.append(dict(section=section,path=k,expected=h,actual=actual,passes=actual==h))
 row=dict(path=str(p),direct_binding_checks=checks,all_direct_bindings_pass=all(x['passes'] for x in checks),scalars={k:v for k,v in d.items() if not isinstance(v,(dict,list))})
 if 'functions' in d:
  row['top12_self_time_functions']=sorted(d['functions'],key=lambda x:x['self_seconds'],reverse=True)[:12]
 rows.append(row);bindings[str(p)]=sha(p)
assert all(r['all_direct_bindings_pass'] for r in rows), 'Current binding drift must be investigated before use'
handoff=next(r for r in rows if r['path'].endswith('/handoff/receipt.json'))['scalars']
assert handoff['selected_connections']==3272 and handoff['required_connections']==6273
out=dict(bindings=bindings,all_current_direct_bindings_pass=True,rows=rows,findings=[
 'The v1 model/handoff profiler output directory is absent; completed evidence is v2. Do not infer execution from a tool filename.',
 'The profiled producer selected 3272 of 6273 connections. This is not the 4028-selected live-feedback workload; component fractions cannot be imported into its complete wall clock.',
 'Native transaction and potential-buffer implementations already exist for four owners and 102 search stages, with no full-workflow timing. A new proposal must extend actual scope or change mechanism, not relabel those components as novel.',
 'The 145-call MMC fallback profile covers archived calls and frozen primary paths, not the later limited v16 fresh workload. Its instrumented 76.9-second cost is not a v16 removable cost.'
 ],next_action='Inspect the existing four-owner native transaction API and complete live-feedback transaction boundary. Specify full-schedule state ownership, exact rollback/epoch/budget parity and complete cost inclusion before a prospective native-state candidate; stop if the same full-scope implementation is already present.',scope='Direct hashes and declared scope only; not recursive proof closure, new speed measurement, paired gain, unseen-family validation or hardware evidence.')
D=R/'experiments/profile_scope_inventory_v1_2026-10-17';D.mkdir(exist_ok=False)
with (D/'verification.json').open('x') as f:json.dump(out,f,indent=2);f.write('\n')
print(json.dumps(dict(all_current_direct_bindings_pass=True,profiles=len(rows),binding_checks=sum(len(r['direct_binding_checks']) for r in rows),next_action=out['next_action']),indent=2))
