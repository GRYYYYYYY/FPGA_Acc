"""Real graph pin membership and selected sketch witness trial."""
import json,time
from pathlib import Path
from pre_route_endpoints import sha
from rr_graph import read_rr_graph
from pin_choice_catalog import PinChoiceCatalog
out=Path('experiments/frisc_pin_choice_catalog_2026-10-05');epath=Path('experiments/frisc_endpoints_2026-10-05/endpoints.json');pfile=Path('experiments/frisc_timing_backgrounds_v2_2026-10-05/baseline_prediction.json')
if out.exists():raise ValueError('fresh output required')
e=json.loads(epath.read_text());inputs={str(epath):sha(epath),str(pfile):sha(pfile),e['inputs']['graph']['path']:e['inputs']['graph']['sha256']};assert all(sha(p)==h for p,h in inputs.items());start=time.monotonic();g=read_rr_graph(e['inputs']['graph']['path']);catalog=PinChoiceCatalog(g);prediction=json.loads(pfile.read_text());assert prediction['physical_graph_sha256']==g.sha256
rows=[{'connection_id':r['connection_id'],'net_id':r['net_id'],**catalog.witness(r['source'],r['sink'],r['physical_edge_ids'])} for r in prediction['connections']];assert len(rows)==5767
assert all(sha(p)==h for p,h in inputs.items());out.mkdir();(out/'witnesses.json').write_text(json.dumps(rows)+'\n');(out/'source').mkdir()
for name in ('frisc_pin_choice_catalog_trial.py','pin_choice_catalog.py','pin_pools.py'):(out/'source'/name).write_text(Path('tools',name).read_text())
receipt={'inputs_sha256':inputs,'source_sha256':{f.name:sha(f) for f in (out/'source').glob('*.py')},'witnesses_sha256':sha(out/'witnesses.json'),'source_class_count':len(catalog.sources),'sink_class_count':len(catalog.sinks),'selected_paths_verified':len(rows),'paths_with_multiple_allowed_sink_physical_pins':sum(r['allowed_sink_physical_pin_count']>1 for r in rows),'wall_s':time.monotonic()-start,'limitations':['class membership does not establish all-pin reachability or packed-pin permutation','selected sketch pin is not predicted native pin certainty','no CPD or native legality claim']};(out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({k:v for k,v in receipt.items() if k not in ('inputs_sha256','source_sha256')}))
