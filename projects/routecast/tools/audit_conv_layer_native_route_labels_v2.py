"""Evaluator-only original route physical/cohort verification; no predictor input."""
import json,time,sys,re,shutil
from pathlib import Path
from collections import Counter
root=Path('experiments');front=root/'conv_layer_global_frontend_v2_2026-10-06'
from pre_route_endpoints import sha
from stream_native_route_audit import audit
out=root/'conv_layer_native_route_labels_audit_v2_2026-10-06'
if out.exists():raise ValueError('fresh audit required')
p=json.loads((front/'protocol.json').read_text());ep=front/'endpoints.json';er=json.loads((front/'receipt.json').read_text())
route=Path('../persistroute/experiments/vpr9/baseline_runs/vpr_serial/koios_conv_layer_seed1_cw300/design.route')
inputs={'graph':p['inputs']['rr_graph'],'placement':p['inputs']['reference_place'],'evaluator_route':{'path':str(route.resolve()),'sha256':sha(route)},'endpoints':{'path':str(ep.resolve()),'sha256':er['outputs']['endpoints.json']}}
assert all(sha(v['path'])==v['sha256'] for v in inputs.values())
with Path(inputs['evaluator_route']['path']).open() as f:header=f.readline()
assert re.search(r'Placement_ID:\s*SHA256:([0-9a-f]{64})',header)[1]==inputs['placement']['sha256']
source_names=['stream_native_route_audit.py','audit_native_route.py','pre_route_endpoints.py']
sources={n:sha(Path('tools')/n) for n in source_names}
out.mkdir();(out/'source').mkdir()
for n in source_names:shutil.copyfile(Path('tools')/n,out/'source'/n)
shutil.copyfile(__file__,out/'driver.py')
protocol={'inputs':inputs,'source_sha256':sources,'driver_sha256':sha(__file__),'frontend_receipt_sha256':sha(front/'receipt.json'),'revision_provenance':p['revision_provenance'],'scope':'evaluator-only original native physical branches and revised retained cohort; not new router execution or method tuning'}
(out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n')
start=time.monotonic();result=audit(inputs['graph']['path'],inputs['evaluator_route']['path']);e=json.loads(ep.read_text());retained={r['net_id'] for r in e['connections']};expected=Counter((r['net_id'],r['source'],r['sink']) for r in e['connections']);actual=Counter((r['net_id'],r['source'],r['sink']) for r in result['connections'] if r['net_id'] in retained)
missing=expected-actual;extra=actual-expected;alignment={'retained_connections':sum(expected.values()),'native_retained_occurrences':sum(actual.values()),'retained_endpoint_multiset_exact':not missing and not extra,'missing':[{'net':n,'source':s,'sink':d,'count':v} for (n,s,d),v in sorted(missing.items())],'extra':[{'net':n,'source':s,'sink':d,'count':v} for (n,s,d),v in sorted(extra.items())],'native_connections_in_other_nets':sum(r['net_id'] not in retained for r in result['connections'])}
assert all(sha(v['path'])==v['sha256'] for v in inputs.values());(out/'physical_branches.json').write_text(json.dumps(result)+'\n');(out/'alignment.json').write_text(json.dumps(alignment,indent=2)+'\n')
receipt={'physical_checks_pass':result['all_printed_branch_arc_switch_and_union_checks_pass'],'retained_endpoint_multiset_exact':alignment['retained_endpoint_multiset_exact'],'retained_connections':sum(expected.values()),'native_retained_occurrences':sum(actual.values()),'overflow_units':result['overflow_units'],'wall_s':time.monotonic()-start,'protocol_sha256':sha(out/'protocol.json'),'outputs':{n:sha(out/n) for n in ('physical_branches.json','alignment.json')},'inputs_unchanged':True,'scope':protocol['scope']};(out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt),flush=True)

assert receipt['physical_checks_pass'] and receipt['retained_endpoint_multiset_exact']
assert all(sha(Path('tools')/n)==h for n,h in sources.items())
