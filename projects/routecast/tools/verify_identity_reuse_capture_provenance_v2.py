"""Audit fused capture source, reused bytes and final uninstrumented acceptance."""
import json,re
from pathlib import Path
from pre_route_endpoints import sha
root=Path(__file__).resolve().parents[1];out=root/'experiments/gf2_identity_reuse_continuous_two_updates_v2_2026-10-06';p=json.loads((out/'protocol.json').read_text());r=json.loads((out/'receipt.json').read_text());v=json.loads((out/'verification.json').read_text());assert v['receipt_sha256']==sha(out/'receipt.json') and r['all_cases_retained'];rows=[]
original=root.parent/'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07/build_tileplace_vpr/vpr/vpr';capture=root/'build/native_route_sync_capture_v2_2026-10-06/routecast_sync_capture_vpr'
for case in p['cases']:
 for i,rd in enumerate(case['rounds']):
  sandbox=Path(rd['sandbox']);prefix=rd['prefix'];stem=f'gf2_d{case["width"]}_{prefix}';parent=sandbox/'experiments'/(stem+'_native_import_2026-10-06');canonical=sandbox/'experiments'/(stem+'_canonical_reload_2026-10-06');a=json.loads((parent/'receipt.json').read_text());b=json.loads((canonical/'receipt.json').read_text());assert b['parent_receipt_sha256']==sha(parent/'receipt.json');assert Path(a['command'][0])==sandbox/'build/native_route_sync_capture_v2_2026-10-06/routecast_sync_capture_vpr' and sha(a['command'][0])==sha(capture)==a['binary_sha256'];assert '--analysis' in a['command'] and '--route' not in a['command'];cwd=Path(b['results'][0]['cwd']);src=sandbox/'work'/(stem+'_native_import_2026-10-06')
  for n in ['before_sync.route','after_sync.route','design.net.post_routing']:assert sha(src/n)==sha(cwd/n)
  assert sha(src/'import.log')==sha(cwd/'capture.log');row=b['results'][0];assert Path(row['reload_command'][0])==original and sha(original)==b['binaries_sha256'][str(original)];text=(cwd/'reload/reload.log').read_text()
  assert all(t in text for t in ['RouterOpts.check_route: FULL','VPR succeeded','Completed routing consistency check successfully.'])
  for pattern in [r'Found (\d+) mismatches',r'Fixed (\d+) routing traces']:assert int(re.search(pattern,text)[1])==0
  assert float(re.search(r'Final critical path delay \(least slack\):\s*([0-9.]+)',text)[1])==row['cpd_ns']
  rows.append({'width':case['width'],'round':i,'parent_receipt_sha256':sha(parent/'receipt.json'),'canonical_receipt_sha256':sha(canonical/'receipt.json'),'capture_reused_exact':True,'final_original_FULL_zero_fixups':True});print(rows[-1],flush=True)
(out/'capture_provenance_verification.json').write_text(json.dumps({'receipt_sha256':sha(out/'receipt.json'),'verifier_sha256':sha(Path(__file__)),'rows':rows,'scope':'Six instrumentedinitial captures byte-identical to canonical consumed artifacts, six final originalVPR FULL/STA zero-fixup proofs. No dynamic call trace or general production claim.'},indent=2)+'\n')
