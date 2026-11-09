"""Recheck actual warm trial artifacts and bind existing identical physical routes."""
import json,shutil
from pathlib import Path
from pre_route_endpoints import sha,placements

base=Path('experiments');trial=base/'native_pressure_live_incremental_swap_2026-10-06';work=Path('work/native_pressure_live_incremental_swap_2026-10-06')
r=json.loads((trial/'receipt.json').read_text());p=json.loads((trial/'protocol.json').read_text());assert r['protocol_sha256']==sha(trial/'protocol.json')
assert [v['mode'] for v in r['results']]==p['sequence']==['off','on','on','off']*2
assert all(sha(path)==digest for path,digest in p['bindings_sha256'].items())
for source in (trial/'source').glob('*.py'):assert sha(source)==p['bindings_sha256'][str(Path('tools')/source.name)]
moved=base/'adder_tree_2L032_moved_incremental_search_2026-10-06';mr=json.loads((moved/'receipt.json').read_text());assert sha(moved/'prediction.json')==mr['prediction_sha256']
reference=json.loads((moved/'prediction.json').read_text());expected=sorted(reference['connections'],key=lambda v:v['connection_id'])
prior=base/'native_pressure_real_swap_trial_2026-10-06';pr=json.loads((prior/'receipt.json').read_text());assert pr['protocol_sha256']==sha(prior/'protocol.json')
bindings={str(trial/'receipt.json'):sha(trial/'receipt.json'),str(prior/'receipt.json'):sha(prior/'receipt.json'),str(moved/'receipt.json'):sha(moved/'receipt.json')}
means={}
for mode in ('off','on'):
 group=[v for v in r['results'] if v['mode']==mode];previous=next(v for v in pr['results'] if v['mode']==mode)
 physical_path=prior/f"{previous['run']:02d}_{mode}_physical.json";physical=json.loads(physical_path.read_text())
 assert physical['overflow_units']==0 and physical['all_printed_branch_arc_switch_and_union_checks_pass']
 assert len(physical['connections'])==516
 bindings[str(physical_path)]=sha(physical_path)
 previous_route=Path('work/native_pressure_real_swap_trial_2026-10-06')/f"{previous['run']:02d}_{mode}"/'design.route';assert sha(previous_route)==previous['route_sha256'];bindings[str(previous_route)]=sha(previous_route)
 for row in group:
  tag=f"{row['run']:02d}_{mode}";route=work/tag/'design.route';log=trial/(tag+'.log');assert sha(route)==row['route_sha256']==previous['route_sha256'];assert sha(log)==row['log_sha256']
  assert row['warm_pipeline_s']>=sum(row['phases'].values())
  assert row['cpd_ns']==previous['cpd_ns'] and row['wirelength']==previous['wirelength']
  assert placements(work/tag/'design.place',p['inputs']['packed_netlist']['sha256'])==placements(base/'adder_tree_2L032_placement_swap_2026-10-06'/'swapped.place',p['inputs']['packed_netlist']['sha256'])
  bindings[str(route)]=sha(route);bindings[str(log)]=sha(log)
  if mode=='on':
   paths=trial/(tag+'_connections.json');payload=trial/(tag+'.pressure');assert json.loads(paths.read_text())==expected
   assert sha(payload)==pr['pressure_payload_sha256'];assert 'RouteCast pressure applied: 100 channel nodes' in log.read_text()
   bindings[str(paths)]=sha(paths);bindings[str(payload)]=sha(payload)
 means[mode]=sum(v['warm_pipeline_s'] for v in group)/4
assert means==r['mean_warm_pipeline_s'] and means['on']/means['off']==r['on_over_off']
assert all(sha(path)==digest for path,digest in bindings.items())
out=base/'native_pressure_live_incremental_swap_verification_2026-10-06';out.mkdir();shutil.copyfile(__file__,out/'source.py')
report={'bindings_sha256':bindings,'all_checks_pass':True,'mean_warm_pipeline_s':means,'on_over_off':r['on_over_off'],'source_sha256':sha(__file__),'scope':'Actual eight live trial routes/paths/payloads/timings and input coordinates; physical legality reused only for byte-identical prior independently audited routes. Single swap, warm initialization and initial baseline production not amortized.'}
(out/'report.json').write_text(json.dumps(report,indent=2)+'\n');(out/'receipt.json').write_text(json.dumps({'report_sha256':sha(out/'report.json'),'all_checks_pass':True},indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='bindings_sha256'}))
