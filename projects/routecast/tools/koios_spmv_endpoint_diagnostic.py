"""Freeze pre-route Koios endpoint extraction without reading native routes."""
import json,time,shutil
from pathlib import Path
from pre_route_endpoints import sha
from pre_route_constants import extract_with_constants
import pre_route_endpoints,pickle

out=Path('experiments/koios_spmv_endpoints_diagnostic_2026-10-04')
if out.exists():raise ValueError('fresh output required')
parent=Path('experiments/koios_spmv_cost_binding_2026-10-04');p=json.loads((parent/'protocol.json').read_text());r=json.loads((parent/'receipt.json').read_text());assert r['exit_code']==0
inputs={k:p['inputs'][k] for k in ('net','place','blif')};inputs['graph']={'path':str((parent/'rr_graph.xml').resolve()),'sha256':r['outputs']['rr_graph.xml']};assert all(sha(v['path'])==v['sha256'] for v in inputs.values());out.mkdir();(out/'source').mkdir()
for f in Path(__file__).parent.glob('*.py'):shutil.copyfile(f,out/'source'/f.name)
original_maps=pre_route_endpoints.physical_maps
def cached_maps(path):
 result=original_maps(path)
 with (out/'physical_maps.pkl').open('wb') as f:pickle.dump(result,f,protocol=4)
 return result
pre_route_endpoints.physical_maps=cached_maps
protocol={'inputs':inputs,'constant_net_method':'global','clock_policy':'exclude_root_clocks','scope':'packed-net/place/RR/BLIF only; native route excluded','source_sha256':{f.name:sha(f) for f in (out/'source').glob('*.py')}};(out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');start=time.monotonic()
try:
 endpoints,mapping=extract_with_constants(inputs['net']['path'],inputs['place']['path'],inputs['graph']['path'],inputs['blif']['path'],'global')
except Exception as e:
 (out/'failure.json').write_text(json.dumps({'error_type':type(e).__name__,'error':str(e),'elapsed_s':time.monotonic()-start},indent=2)+'\n');raise
for n,d in [('endpoints.json',endpoints),('mapping.json',mapping)]: (out/n).write_text(json.dumps(d)+'\n')
assert all(sha(v['path'])==v['sha256'] for v in inputs.values());receipt={'protocol_sha256':sha(out/'protocol.json'),'connections':len(endpoints['connections']),'excluded_nets':endpoints['excluded_nets'],'wall_s':time.monotonic()-start,'inputs_unchanged':True,'outputs':{n:sha(out/n) for n in ('endpoints.json','mapping.json')}};(out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt),flush=True)
