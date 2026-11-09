"""Original-XML native post-sync and canonical path/ledger closure, both cases."""
import json
from pathlib import Path
from pre_route_endpoints import sha
from stream_native_route_audit import audit
from audit_native_route import NET,NODE
ROOT=Path(__file__).resolve().parents[1];rows=[]
def paths(file):
 result={};name=None;parents={};previous=None;switch=None
 for line in Path(file).read_text().splitlines():
  m=NET.match(line)
  if m:name=m[2];parents={};previous=None;switch=None
  m=NODE.match(line)
  if not m:continue
  node=int(m[1]);kind=m[2]
  if kind=='SOURCE':parents[node]=((node,None),)
  elif kind=='SINK':
   key=(name,node);assert key not in result;result[key]=parents[previous]+((node,switch),)
  elif node not in parents:parents[node]=parents[previous]+((node,switch),)
  previous=node;switch=int(m[3])
 return result
for n,connections in [(4,371),(8,1514),(16,5070)]:
 out=ROOT/f'experiments/bitonic_resident_staging_n{n}_canonical_2026-10-07';r=json.loads((out/'receipt.json').read_text());parent=ROOT/'experiments/bitonic_resident_staging_native_import_2026-10-07';assert r['parent_receipt_sha256']==sha(parent/'receipt.json') and r['source_sha256']==sha(ROOT/f'tools/trial_bitonic_resident_staging_n{n}_canonical.py');assert all(sha(f)==h for f,h in r['binaries_sha256'].items());x=r['results'][0];assert x['status']=='RELOADED' and not x['ambiguous_pins'] and x['exit_code']==0 and x['sync_mismatches']==x['sync_fixups']==0 and x['cpd_matches_original'];assert all(sha(f)==h for f,h in x['sha256'].items());work=Path(x['cwd']);graph=Path(x['reload_command'][x['reload_command'].index('--read_rr_graph')+1]);assert sha(graph)==r['graph_sha256'];checks={}
 for label,file in [('before',work/'before_sync.route'),('after',work/'after_sync.route'),('canonical',work/'reload/design.route')]:
  a=audit(graph,file);assert a['overflow_units']==0 and len(a['connections'])==connections;checks[label]=a
 assert paths(work/'after_sync.route')==paths(work/'reload/design.route');assert checks['after']['node_occupancy']==checks['canonical']['node_occupancy']
 before_after=paths(work/'before_sync.route')==paths(work/'after_sync.route');assert paths(parent/f'n{n}/design.route')==paths(work/'before_sync.route')
 result=dict(count=n,connections=connections,canonical_FULL_STA=True,packing_fixups=0,cpd_ns=x['cpd_ns'],before_after_named_physical_paths_unchanged=before_after,canonical_named_paths_exactly_match_native_postsync=True,receipt_sha256=sha(out/'receipt.json'),audit_source_sha256=sha(Path(__file__)),scope='Native post-sync paths/uniqueNETcapacity and zero-fixup originalcanonical FULLSTA proven. Rawimport packing corrections acknowledged. Newplacement native proof; fresh same-target cold reference pending, no freshjointgate or speedclaim.')
 (out/'verification.json').write_text(json.dumps(result,indent=2)+'\n');rows.append(result)
print(rows)
