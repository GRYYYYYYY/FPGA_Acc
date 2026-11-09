"""Authenticate first-analysis capture reuse, final FULL parity and ABBA timing."""
import json
from pathlib import Path
from pre_route_endpoints import sha
root=Path(__file__).resolve().parents[1];out=root/'experiments/tseng_fused_capture_abba_2026-10-06';r=json.loads((out/'receipt.json').read_text());p=json.loads((out/'protocol.json').read_text());assert r['protocol_sha256']==sha(out/'protocol.json') and len(r['runs'])==4 and all(sha(root/'tools'/n)==h for n,h in p['source_sha256'].items()) and sha(root/'experiments/tseng_joint_transfer_2026-10-06/receipt.json')==p['candidate_sha256']
cpds=[];raw=[];canonical=[];before=[];after=[];net=[];costs=[];evidence={}
for row,frozen in zip(r['runs'],p['runs']):
 assert all(row[k]==v for k,v in frozen.items()) and [s['tool'] for s in row['stages']]==row['tools']
 for i,s in enumerate(row['stages']):assert s['exit_code']==0 and sha(out/(row['label']+'_'+str(i)+'.log'))==s['log_sha256']
 ni=root/'experiments'/row['native_directory'];ci=root/'experiments'/row['canonical_directory'];nr=json.loads((ni/'receipt.json').read_text());nv=json.loads((ni/'verification.json').read_text());cr=json.loads((ci/'receipt.json').read_text());cv=json.loads((ci/'verification.json').read_text());assert nv['receipt_sha256']==sha(ni/'receipt.json') and nv['native_FULL_success'] and nv['serialized_paths_exactly_match_selection'] and cv['receipt_sha256']==sha(ci/'receipt.json') and cv['verified_bundles']==1 and cr['parent_receipt_sha256']==sha(ni/'receipt.json')
 for q,h in nr['files_sha256'].items():assert sha(q)==h
 x=cr['results'][0];assert x['status']=='RELOADED' and x['sync_mismatches']==x['sync_fixups']==0 and x['cpd_ns']==nr['cpd_ns']
 assert all(sha(q)==h for q,h in x['sha256'].items());cpds.append(nr['cpd_ns']);nw=root/'work'/row['native_directory'];cw=Path(x['cwd']);raw.append(sha(nw/'design.route'));canonical.append(sha(cw/'reload/design.route'));before.append(sha(cw/'before_sync.route'));after.append(sha(cw/'after_sync.route'));net.append(sha(cw/'design.net.post_routing'))
 if row['fused']:
  assert cr['fused_first_analysis_capture'] and sha(cw/'capture.log')==sha(nw/'import.log')
  for f in ('before_sync.route','after_sync.route','design.net.post_routing'):assert sha(nw/f)==sha(cw/f)==nr['files_sha256'][str(nw/f)]
  assert sha(nr['original_native_command'][0])==nr['original_binary_sha256']==cr['original_native_binary_sha256']
 for d in (ni,ci):
  for f in ('receipt.json','verification.json'):evidence[str(d/f)]=sha(d/f)
 costs.append({'label':row['label'],'fused':row['fused'],'workflow_s':sum(s['wall_s'] for s in row['stages'] if s['tool'].startswith('trial_')),'audit_s':sum(s['wall_s'] for s in row['stages'] if s['tool'].startswith('verify_'))})
assert all(len(set(values))==1 for values in (cpds,raw,canonical,before,after,net))
result={'receipt_sha256':sha(out/'receipt.json'),'evidence_sha256':evidence,'ABBA_costs':costs,'cpd_ns':cpds[0],'connections':1234,'raw_and_canonical_routes_exact':True,'sync_captures_and_postNET_exact':True,'final_original_NATIVE_FULL_zero_fixup_all':True,'scope':'Fixed tseng candidate import+canonical stage ABBA; fused evidence from actual first successful FULL/STA, native before/after/postNET byte-equivalent to separate capture control. Audits retained separately, no identity cache. No full sequential speedup, quality superiority, family or board claim.'};(out/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='evidence_sha256'},indent=2))
