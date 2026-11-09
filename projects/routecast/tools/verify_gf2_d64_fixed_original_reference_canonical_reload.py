"""Verify fresh reload, digest chain, native FULL checks and unchanged physical paths."""
import json,re
from pathlib import Path
from pre_route_endpoints import sha
from audit_native_route import NODE
root=Path(__file__).resolve().parents[1];out=root/'experiments/gf2_d64_fixed_original_reference_canonical_reload_2026-10-06';r=json.loads((out/'receipt.json').read_text());assert sha(root/'tools/trial_gf2_d64_fixed_original_reference_canonical_reload.py')==r['source_sha256'];assert all(sha(p)==h for p,h in r['binaries_sha256'].items());parent=root/'experiments/gf2_d64_fixed_original_cold_2026-10-06/receipt.json';assert sha(parent)==r['parent_receipt_sha256'];original={'results':[json.loads(parent.read_text())]};rows=[]
for dirname,filename in [('native_route_sync_capture_v2_2026-10-06','routecast_sync_capture_vpr'),('native_net_identity_capture_2026-10-06','routecast_net_identity_vpr')]:
 build=root/'build'/dirname;build_receipt=json.loads((build/'receipt.json').read_text());assert sha(build/filename)==build_receipt['binary_sha256'];assert sha(build/'protocol.json')==build_receipt['protocol_sha256'];protocol=json.loads((build/'protocol.json').read_text());assert all(sha(p)==h for p,h in protocol['inputs_sha256'].items())

def physical_by_name(path):
 nets={};name=None;parents={};previous=None;switch=None
 for line in path.read_text().splitlines():
  m=re.match(r'^Net\s+\d+\s+\((.*?)\)',line)
  if m:name=m[1];assert name not in nets;nets[name]=[];parents={};previous=None;continue
  m=NODE.match(line)
  if not m:continue
  node=int(m[1]);kind=m[2]
  if kind=='SOURCE':parents[node]=[(node,None)]
  elif kind=='SINK':nets[name].append(tuple(parents[previous]+[(node,switch)]))
  elif node not in parents:parents[node]=parents[previous]+[(node,switch)]
  previous=node;switch=int(m[3])
 return {name:sorted(paths) for name,paths in nets.items()}
for row in r['results']:
 assert all(sha(p)==h for p,h in row['sha256'].items());assert row['status']=='RELOADED' and row['exit_code']==0 and not row['ambiguous_pins'] and row['remapped_sink_pins']==491 and row['cpd_matches_original'] and row['sync_mismatches']==0 and row['sync_fixups']==0;cwd=Path(row['cwd']);reload=cwd/'reload';log=(reload/'reload.log').read_text();assert 'RouterOpts.check_route: FULL' in log and 'Completed routing consistency check successfully.' in log and 'VPR succeeded' in log;assert row['reload_command'][row['reload_command'].index('--check_route')+1]=='full';graph=row['reload_command'][row['reload_command'].index('--read_rr_graph')+1];assert sha(graph)==r['graph_sha256'];assert 'Netlist_ID: SHA256:'+sha(reload/'design.net') in (reload/'design.place').read_text().splitlines()[0];assert 'Placement_ID: SHA256:'+sha(reload/'design.place') in (reload/'design.route').read_text().splitlines()[0];assert physical_by_name(root/'work/gf2_d64_fixed_original_cold_2026-10-06/design.route')==physical_by_name(cwd/'before_sync.route')==physical_by_name(cwd/'after_sync.route')==physical_by_name(reload/'design.route');assert row['cpd_ns']==original['results'][row['pair_index']]['cpd_ns'];rows.append({'pair_index':row['pair_index'],'cpd_ns':row['cpd_ns'],'physical_paths_preserved':True,'full_reload_success':True,'sync_mismatches':0,'sync_fixups':0})
(out/'verification.json').write_text(json.dumps({'verified_bundles':len(rows),'sink_pins_remapped':sum(row['remapped_sink_pins'] for row in r['results']),'results':rows,'receipt_sha256':sha(out/'receipt.json'),'verifier_sha256':sha(Path(__file__)),'scope':'Native FULL reload and post-sync STA, zero packing mismatches/fixups, exact per-NET terminal-path node/switch preservation independent of sibling print order and packed/place/route digest chain. Native captures were independently original-XML audited by trial; no production exception safety, future reroute or speedup claim.'},indent=2)+'\n');print('verified',len(rows),'consistent native bundles')
