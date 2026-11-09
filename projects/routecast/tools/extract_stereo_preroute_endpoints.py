"""Extract frozen stereo endpoints without opening a native route."""
import json,time,sys,shutil
from pathlib import Path
root=Path('experiments/stereo_prospective_validation_2026-10-05')
sys.path.insert(0,str((root/'source').resolve()))
from pre_route_constants import extract_with_constants
from pre_route_endpoints import sha
p=json.loads((root/'protocol.json').read_text());inputs=p['inputs']
out=root/'endpoints'
if out.exists():raise ValueError('fresh endpoint output required')
assert json.loads((root/'graph_readiness.json').read_text())['buffered_zero_internal_preconditions']
for name in ('pre_route_endpoints.py','pre_route_constants.py','blif_constants.py'):
 assert sha(root/'source'/name)==p['frozen_sources'][name]
assert all(sha(v['path'])==v['sha256'] for v in inputs.values())
out.mkdir();shutil.copyfile(__file__,out/'driver.py');start=time.monotonic()
(out/'protocol.json').write_text(json.dumps({'parent_protocol_sha256':sha(root/'protocol.json'),'inputs':inputs,'constant_net_method':'global','clock_policy':'exclude_root_clocks','native_route_input':False,'frozen_frontend_sources':{n:p['frozen_sources'][n] for n in ('pre_route_endpoints.py','pre_route_constants.py','blif_constants.py')},'driver_sha256':sha(out/'driver.py')},indent=2)+'\n')
try:
 e,m=extract_with_constants(inputs['packed_netlist']['path'],inputs['placement']['path'],inputs['graph']['path'],inputs['circuit']['path'],'global')
 for name,data in [('endpoints.json',e),('mapping.json',m)]: (out/name).write_text(json.dumps(data)+'\n')
 assert all(sha(v['path'])==v['sha256'] for v in inputs.values())
 result={'status':'completed','connections':len(e['connections']),'excluded_nets':e['excluded_nets'],'wall_s':time.monotonic()-start,'input_hashes_unchanged':True,'output_sha256':{n:sha(out/n) for n in ('endpoints.json','mapping.json')},'scope':'frozen packed net/place/graph/BLIF endpoint mapping only; no native route labels, graph cost binding or prediction quality'}
 (out/'receipt.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)
except BaseException as error:
 (out/'failure.json').write_text(json.dumps({'error':repr(error),'wall_s':time.monotonic()-start,'scope':'preserve unsupported mapping; do not substitute route-derived endpoints'},indent=2)+'\n');raise
