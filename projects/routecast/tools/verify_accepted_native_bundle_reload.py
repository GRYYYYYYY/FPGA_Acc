import json,re
from pathlib import Path
from pre_route_endpoints import sha
root=Path(__file__).resolve().parents[1];out=root/'experiments/accepted_native_bundle_reload_2026-10-06';receipt=json.loads((out/'receipt.json').read_text());work=Path(receipt['cwd']);src=root/'work/native_candidate_move_accept_v3_2026-10-06/accept'
def sections(path):
 result={};cur=None
 for line in path.read_text().splitlines():
  m=re.match(r'^Net\s+\d+\s+\((.*?)\)',line)
  if m:cur=m[1];assert cur not in result;result[cur]=re.sub(r'^Net\s+\d+','Net ID',line).split();continue
  if cur is not None:result[cur].append(re.sub(r'Net_pin_index:\s*\d+','Net_pin_index: ID',line).split())
 return result
assert sections(src/'output.route')==sections(work/'design.route');assert receipt['exit_code']==0 and receipt['cpd_ns']==4.06376 and receipt['sync_mismatches']==receipt['sync_fixups']==0
for row in receipt['captures']:assert sha(out/(row['case']+'.jsonl'))==row['identity_sha256']
place=(work/'design.place').read_text();route=(work/'design.route').read_text();assert 'Netlist_ID: SHA256:'+sha(work/'design.net') in place;assert 'Placement_ID: SHA256:'+sha(work/'design.place') in route
files=[out/'receipt.json',out/'mapping.json',out/'reload.log',out/'physical_audit.json',src/'output.route',src/'accepted.place',src/'design.net.post_routing',work/'design.net',work/'design.place',work/'design.route',Path(receipt['command'][0]),Path(__file__)]
(out/'verification.json').write_text(json.dumps({'net_named_physical_trace_unchanged_excluding_identity_labels':True,'digest_chain_verified':True,'same_accepted_cpd_ns':4.06376,'sha256':{str(p):sha(p) for p in files},'scope':'One real moved accepted bundle serialized identity reconstruction and analysis-only replay; not new native routing search or full formal functional equivalence.'},indent=2)+'\n');print('Unchanged physical trace and packed/place/route digest chain verified')
