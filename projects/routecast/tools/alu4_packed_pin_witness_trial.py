"""Full real frontend nominal packed-pin/sketch witness audit."""
import json,time
from pathlib import Path
from pre_route_endpoints import sha
from rr_graph import read_rr_graph
from packed_pin_witness import join
out=Path('experiments/alu4_packed_pin_witness_2026-10-05');epath=Path('experiments/alu4_validation_capture_2026-10-05/endpoints.json');mfile=epath.with_name('pin_mapping.json');pfile=Path('experiments/alu4_transfer_2026-10-05/prediction.json')
if out.exists():raise ValueError('fresh output required')
e=json.loads(epath.read_text());inputs={str(f):sha(f) for f in (epath,mfile,pfile)};inputs.update({v['path']:v['sha256'] for v in e['inputs'].values()});assert all(sha(p)==h for p,h in inputs.items());start=time.monotonic();g=read_rr_graph(e['inputs']['graph']['path']);rows=join(g,e,json.loads(mfile.read_text()),json.loads(pfile.read_text()));assert len(rows)==2331;assert all(sha(p)==h for p,h in inputs.items());out.mkdir();(out/'rows.json').write_text(json.dumps(rows)+'\n');(out/'source').mkdir()
for name in ('alu4_packed_pin_witness_trial.py','packed_pin_witness.py','pin_choice_catalog.py','pin_pools.py'):(out/'source'/name).write_text(Path('tools',name).read_text())
r={'input_sha256':inputs,'source_sha256':{f.name:sha(f) for f in (out/'source').glob('*.py')},'rows_sha256':sha(out/'rows.json'),'connections':len(rows),'nominal_source_ptc_mismatches':sum(not x['selected_opin_matches_nominal_ptc'] for x in rows),'nominal_sink_ptc_mismatches':sum(not x['selected_ipin_matches_nominal_ptc'] for x in rows),'wall_s':time.monotonic()-start,'limitations':['nominal ptc mismatch not necessarily illegal: equivalent-pin permutation can be allowed','does not solve native packed-pin assignment or timing','CID join uses deterministic original frontend traversal ordering']};(out/'receipt.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({k:v for k,v in r.items() if k not in ('input_sha256','source_sha256')}))
