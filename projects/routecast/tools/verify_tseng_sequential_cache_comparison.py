"""Paired full sequential lifecycle observations with exact path/state checks."""
import json
from pathlib import Path
from pre_route_endpoints import sha
from accepted_route_state import digest
root=Path(__file__).resolve().parents[1];out=root/'experiments/tseng_sequential_cache_comparison_v4_2026-10-06';out.mkdir()
names=['tseng_sequential_control4','tseng_sequential_cached4v4'];results=[];bindings={};counts={'hit':0,'miss':0}
for stem in names:
 e=root/'experiments'/(stem+'_2026-10-06');r=json.loads((e/'receipt.json').read_text());p=json.loads((e/'protocol.json').read_text());v=json.loads((e/'verification.json').read_text());assert v['receipt_sha256']==sha(e/'receipt.json') and r['completed'] and len(r['rounds'])==4
 for name in ('receipt.json','protocol.json','verification.json'):bindings[str(e/name)]=sha(e/name)
 results.append((e,r,p,v))
for i in range(4):
 control,cached=results
 assert (control[0]/f'accepted{i}.json').read_bytes()==(cached[0]/f'accepted{i}.json').read_bytes()
 for name in ('tseng_joint_transfer','tseng_joint_native_import','tseng_joint_canonical_reload','tseng_swapped_reference_canonical_reload','tseng_swapped_quality_gate'):
  a=Path(control[2]['rounds'][i]['sandbox']);b=Path(cached[2]['rounds'][i]['sandbox'])
  if name=='tseng_joint_transfer':assert (a/'experiments'/(name+'_2026-10-06')/'receipt.json').read_bytes()==(b/'experiments'/(name+'_2026-10-06')/'receipt.json').read_bytes()
  elif name in ('tseng_joint_native_import','tseng_joint_canonical_reload','tseng_swapped_reference_canonical_reload'):
   ac=a/'work'/(name+'_2026-10-06');bc=b/'work'/(name+'_2026-10-06')
   if name=='tseng_joint_native_import':assert (ac/'design.route').read_bytes()==(bc/'design.route').read_bytes();assert (ac/'identity.jsonl').read_bytes()==(bc/'identity.jsonl').read_bytes()
   else:assert (ac/'0/reload/design.route').read_bytes()==(bc/'0/reload/design.route').read_bytes();assert (ac/'0/reload/identity.jsonl').read_bytes()==(bc/'0/reload/identity.jsonl').read_bytes()
   receipt=json.loads((b/'experiments'/(name+'_2026-10-06')/'receipt.json').read_text());info=receipt['identity_cache'] if name=='tseng_joint_native_import' else receipt['results'][0]['identity_cache'];counts['hit' if info['hit'] else 'miss']+=1
   manifest=cached[0]/'cache'/info['key']/'receipt.json';entry=json.loads(manifest.read_text());assert digest(entry['bindings'])==info['key'] and entry['source_sha256']==cached[2]['live_sources_sha256']['native_identity_cache.py'];assert sha(manifest)==info['receipt_sha256'] and sha(manifest.parent/'identity.jsonl')==entry['table_sha256'] and sha(manifest.parent/'identity.log')==entry['log_sha256'];bindings[str(manifest)]=sha(manifest)
  else:
   ar=control[1]['rounds'][i];br=cached[1]['rounds'][i];assert all(ar[k]==br[k] for k in ('selected','candidate_cpd_ns','reference_cpd_ns','revision'))
assert counts['hit']>0 and counts['miss']>0 and sum(counts.values())==12
result={'evidence_sha256':bindings,'accepted_states_and_candidate_paths_exact':True,'identity_tables_exact':True,'updates':4,'connections_per_update':1234,'cache_counts':counts,'uncached_total_wall_s':results[0][1]['total_wall_s'],'cached_total_wall_s':results[1][1]['total_wall_s'],'uncached_native_tail_s':results[0][3]['native_tail_including_fresh_cold_s'],'cached_native_tail_s':results[1][3]['native_tail_including_fresh_cold_s'],'scope':'One serial pair of four-update observations, cache cold costs included, complete native FULL/STA/quality/audits retained. Candidate, native serialization and accepted reference states exact. No statistical speedup proof, independent family or BLIF-to-output timing claim; previous failed cache run retained separately.'}
(out/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
