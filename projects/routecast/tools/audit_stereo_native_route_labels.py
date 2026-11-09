"""Evaluator-only original route physical/cohort verification; no predictor input."""
import json,time,sys,re,shutil
from pathlib import Path
from collections import Counter
root=Path('experiments/stereo_prospective_validation_2026-10-05');sys.path.insert(0,str((root/'source').resolve()))
from pre_route_endpoints import sha
from stream_native_route_audit import audit
out=root/'native_route_labels_audit'
if out.exists():raise ValueError('fresh audit required')
p=json.loads((root/'native_cost_binding/protocol.json').read_text());ep=root/'endpoints/endpoints.json';er=json.loads((root/'endpoints/receipt.json').read_text())
inputs={k:p['inputs'][k] for k in ('graph','placement','evaluator_route')};inputs['endpoints']={'path':str(ep.resolve()),'sha256':er['output_sha256']['endpoints.json']};assert all(sha(v['path'])==v['sha256'] for v in inputs.values())
with Path(inputs['evaluator_route']['path']).open() as f:header=f.readline()
assert re.search(r'Placement_ID:\s*SHA256:([0-9a-f]{64})',header)[1]==inputs['placement']['sha256']
source_names=['stream_native_route_audit.py','audit_native_route.py','pre_route_endpoints.py'];frozen=json.loads((root/'protocol.json').read_text())
assert all(sha(root/'source'/n)==frozen['frozen_sources'][n] for n in source_names)
out.mkdir();shutil.copyfile(__file__,out/'driver.py');protocol={'inputs':inputs,'source_sha256':{n:sha(root/'source'/n) for n in source_names},'driver_sha256':sha(__file__),'scope':'evaluator-only original native physical branches and pre-route retained cohort; not new router execution or method tuning'};(out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n')
start=time.monotonic();result=audit(inputs['graph']['path'],inputs['evaluator_route']['path']);e=json.loads(ep.read_text());retained={r['net_id'] for r in e['connections']};expected=Counter((r['net_id'],r['source'],r['sink']) for r in e['connections']);actual=Counter((r['net_id'],r['source'],r['sink']) for r in result['connections'] if r['net_id'] in retained)
missing=expected-actual;extra=actual-expected;alignment={'retained_connections':sum(expected.values()),'native_retained_occurrences':sum(actual.values()),'retained_endpoint_multiset_exact':not missing and not extra,'missing':[{'net':n,'source':s,'sink':d,'count':v} for (n,s,d),v in sorted(missing.items())],'extra':[{'net':n,'source':s,'sink':d,'count':v} for (n,s,d),v in sorted(extra.items())],'native_connections_in_other_nets':sum(r['net_id'] not in retained for r in result['connections'])}
assert all(sha(v['path'])==v['sha256'] for v in inputs.values());(out/'physical_branches.json').write_text(json.dumps(result)+'\n');(out/'alignment.json').write_text(json.dumps(alignment,indent=2)+'\n')
receipt={'physical_checks_pass':result['all_printed_branch_arc_switch_and_union_checks_pass'],'retained_endpoint_multiset_exact':alignment['retained_endpoint_multiset_exact'],'retained_connections':sum(expected.values()),'native_retained_occurrences':sum(actual.values()),'overflow_units':result['overflow_units'],'wall_s':time.monotonic()-start,'protocol_sha256':sha(out/'protocol.json'),'outputs':{n:sha(out/n) for n in ('physical_branches.json','alignment.json')},'inputs_unchanged':True,'scope':protocol['scope']};(out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt),flush=True)
