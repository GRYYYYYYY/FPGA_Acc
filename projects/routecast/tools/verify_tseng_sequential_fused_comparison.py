"""Paired full sequential lifecycle observations with exact path/state checks."""
import json
from pathlib import Path
from pre_route_endpoints import sha
from accepted_route_state import digest
from audit_native_route import NET,NODE
from stream_native_route_audit import audit
import re
def pinned_paths(path):
 result={};net=None;parents={};previous=None;switch=None
 for line in Path(path).read_text().splitlines():
  m=NET.match(line)
  if m:net=m[2];parents={};previous=None;switch=None
  m=NODE.match(line)
  if not m:continue
  node=int(m[1]);kind=m[2]
  if kind=='SOURCE':parents[node]=((node,None),)
  elif kind=='SINK':
   pin=int(re.search(r'Net_pin_index:\s*(\d+)',line)[1]);key=(net,pin);assert key not in result;result[key]=parents[previous]+((node,switch),)
  elif node not in parents:parents[node]=parents[previous]+((node,switch),)
  previous=node;switch=int(m[3])
 return result
root=Path(__file__).resolve().parents[1];out=root/'experiments/tseng_sequential_fused_comparison_2026-10-06';out.mkdir(exist_ok=True)
names=['tseng_sequential_cached4v4','tseng_sequential_fused4'];results=[];bindings={};counts={'hit':0,'miss':0}
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
   else:
    pa=ac/'0/reload/design.route';pb=bc/'0/reload/design.route';assert pinned_paths(pa)==pinned_paths(pb) and len(pinned_paths(pa))==1234
    graph=json.loads((b/'experiments'/(name+'_2026-10-06')/'receipt.json').read_text())['results'][0]['reload_command'];graph=graph[graph.index('--read_rr_graph')+1];aa=audit(graph,pa);bb=audit(graph,pb);assert aa['node_occupancy']==bb['node_occupancy'] and aa['overflow_units']==bb['overflow_units']==0 and len(aa['connections'])==len(bb['connections'])==1234
    assert (ac/'0/reload/identity.jsonl').read_bytes()==(bc/'0/reload/identity.jsonl').read_bytes()
   receipt=json.loads((b/'experiments'/(name+'_2026-10-06')/'receipt.json').read_text());info=receipt['identity_cache'] if name=='tseng_joint_native_import' else receipt['results'][0]['identity_cache'];counts['hit' if info['hit'] else 'miss']+=1
   manifest=cached[0]/'cache'/info['key']/'receipt.json';entry=json.loads(manifest.read_text());assert digest(entry['bindings'])==info['key'] and entry['source_sha256']==cached[2]['live_sources_sha256']['native_identity_cache.py'];assert sha(manifest)==info['receipt_sha256'] and sha(manifest.parent/'identity.jsonl')==entry['table_sha256'] and sha(manifest.parent/'identity.log')==entry['log_sha256'];bindings[str(manifest)]=sha(manifest)
  else:
   ar=control[1]['rounds'][i];br=cached[1]['rounds'][i];assert all(ar[k]==br[k] for k in ('selected','candidate_cpd_ns','reference_cpd_ns','revision'))
assert counts['hit']>0 and counts['miss']>0 and sum(counts.values())==12
for i in range(4):
 sandbox=Path(results[1][2]['rounds'][i]['sandbox'])
 for prefix,source,log in [('tseng_joint_canonical_reload','tseng_joint_native_import','import.log'),('tseng_swapped_reference_canonical_reload','tseng_swapped_place_cold','run.log')]:
  source_dir=sandbox/'work'/(source+'_2026-10-06');canonical=sandbox/'experiments'/(prefix+'_2026-10-06');cr=json.loads((canonical/'receipt.json').read_text());sr=json.loads((sandbox/'experiments'/(source+'_2026-10-06')/'receipt.json').read_text());assert cr['fused_first_analysis_capture'] and cr['parent_receipt_sha256']==sha(sandbox/'experiments'/(source+'_2026-10-06')/'receipt.json')
  target=Path(cr['results'][0]['cwd'])
  for name in ('before_sync.route','after_sync.route','design.net.post_routing'):assert sha(source_dir/name)==sha(target/name)==sr['files_sha256'][str(source_dir/name)]
  assert sha(source_dir/log)==sha(target/'capture.log')
result={'evidence_sha256':bindings,'accepted_states_and_candidate_paths_exact':True,'canonical_NET_pin_paths_exact':True,'reference_print_order_may_differ':True,'identity_tables_exact':True,'updates':4,'connections_per_update':1234,'cache_counts':counts,'baseline_cached_total_wall_s':results[0][1]['total_wall_s'],'fused_cached_total_wall_s':results[1][1]['total_wall_s'],'baseline_cached_native_tail_s':results[0][3]['native_tail_including_fresh_cold_s'],'fused_cached_native_tail_s':results[1][3]['native_tail_including_fresh_cold_s'],'scope':'Prior cached four-update baseline compared with one fresh fused four-update run, cache cold costs included, complete native FULL/STA/quality/audits retained. Candidate serialization byte-exact; reference NET/pin complete physical paths and accepted states exact, while reference sibling printing may differ. No statistical speedup proof, independent family or BLIF-to-output timing claim; initial byte-comparison failure retained separately.'}
(out/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
