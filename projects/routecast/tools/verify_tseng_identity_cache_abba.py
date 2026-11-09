"""Authenticate ABBA import equivalence and cache invalidation/corruption checks."""
import json,shutil,tempfile
from pathlib import Path
from pre_route_endpoints import sha
from native_identity_cache import NativeIdentityCache
from accepted_route_state import digest
root=Path(__file__).resolve().parents[1];out=root/'experiments/tseng_identity_cache_abba_2026-10-06';r=json.loads((out/'receipt.json').read_text());p=json.loads((out/'protocol.json').read_text());assert sha(out/'protocol.json')==r['protocol_sha256'] and len(r['runs'])==5
assert all(sha(root/'tools'/n)==h for n,h in p['sources_sha256'].items());receipts=[]
for row,frozen in zip(r['runs'],p['order']):
 assert all(row[k]==v for k,v in frozen.items()) and sha(out/(row['name']+'.log'))==row['log_sha256'] and sha(out/(row['name']+'_audit.log'))==row['audit_log_sha256']
 stem='tseng_identity_cache_'+row['name'];e=root/'experiments'/(stem+'_2026-10-06');q=json.loads((e/'receipt.json').read_text());v=json.loads((e/'verification.json').read_text());assert sha(e/'receipt.json')==v['receipt_sha256'] and v['native_FULL_success'] and v['serialized_paths_exactly_match_selection'] and v['complete_selected_connections']==1234
 assert all(sha(f)==h for f,h in q['files_sha256'].items());receipts.append(q)
 if row['cached']:assert q['identity_cache']['hit']==(row['name']!='warm')
workdirs=[root/'work'/('tseng_identity_cache_'+row['name']+'_2026-10-06') for row in r['runs']]
assert len({sha(w/'design.route') for w in workdirs})==1 and len({q['cpd_ns'] for q in receipts})==1
assert len({sha(w/'identity.jsonl') for w in workdirs})==1
cache=NativeIdentityCache(out/'cache');command=receipts[0]['identity_command'];key=receipts[0]['identity_cache']['key'];entry=out/'cache'/key;table=entry/'identity.jsonl';saved=table.read_bytes();rejected=False
try:
 table.write_bytes(saved+b'\n')
 try:cache.get(command,workdirs[0])
 except ValueError:rejected=True
finally:table.write_bytes(saved)
assert rejected;assert cache.get(command,workdirs[0])[1]['hit']
with tempfile.TemporaryDirectory(dir='/tmp') as d:
 cwd=Path(d)
 for name in ('design.net','design.place','design.blif'):shutil.copyfile(workdirs[0]/name,cwd/name)
 baseline=cache._bindings(command,cwd)[0];assert digest(baseline)==key
 changed=[]
 for name in ('design.net','design.place','design.blif'):
  f=cwd/name;s=f.read_bytes();f.write_bytes(s+b'\n');different=cache._bindings(command,cwd)[0];assert digest(different)!=key;changed.append(name);f.write_bytes(s)
assert set(baseline['inputs_sha256'])=={'binary','architecture','blif','net','place','graph'}
a=[row['trial_wall_s'] for row in r['runs'] if row['name'].startswith('a')];b=[row['trial_wall_s'] for row in r['runs'] if row['name'].startswith('b')]
result={'receipt_sha256':sha(out/'receipt.json'),'identity_tables_exact':True,'serialized_routes_exact':True,'connections':1234,'native_FULL_success_all':True,'cpd_ns':receipts[0]['cpd_ns'],'cold_cache_trial_wall_s':r['runs'][0]['trial_wall_s'],'uncached_import_wall_s':a,'cached_import_wall_s':b,'corrupt_cache_rejected':True,'content_change_invalidates':changed,'scope':'Single fixed tseng candidate ABBA import-stage comparison, cold population and audit costs separately retained. Binary/architecture/RR/command hashes bind identities conservatively. Not full sequential latency, quality improvement or generalization claim.'};(out/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
