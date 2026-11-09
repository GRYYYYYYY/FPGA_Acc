"""Fresh background acquisition cost with exact archived path/union comparison."""
import json,time,shutil
from pathlib import Path
from pre_route_endpoints import sha
from rr_graph import read_rr_graph
from prepared_templates import PreparedTemplates
from hybrid_repair import repair
from lazy_region_search import LazyRegionalSearch
out=Path('experiments/pressure_background_cost_2026-10-04')
if out.exists():raise ValueError('fresh output required')
epath=Path('experiments/pre_route_endpoints_2026-10-04/diffeq_endpoints.json');bgpath=Path('experiments/lazy_repair_serialization_fix_2026-10-04/lazy_2.json');ep=json.loads(epath.read_text());graph=Path(ep['inputs']['graph']['path']);out.mkdir();(out/'source').mkdir()
for f in Path(__file__).parent.glob('*.py'):shutil.copyfile(f,out/'source'/f.name)
p={'scope':'fresh diffeq background graph/load/template/predict/repair acquisition, exact prior path/union replay; separate staged cost not same-run pipeline','inputs':{k:{'path':str(v.resolve()),'sha256':sha(v)} for k,v in {'endpoints':epath,'graph':graph,'expected':bgpath}.items()},'refinement_rounds':2,'margin':1,'source_sha256':{f.name:sha(f) for f in (out/'source').glob('*.py')}}
(out/'protocol.json').write_text(json.dumps(p,indent=2)+'\n');start=time.monotonic();g=read_rr_graph(graph);prepared=PreparedTemplates(g,2);candidate=prepared.predict(ep);result=repair(g,ep,candidate,search_type=LazyRegionalSearch);wall=time.monotonic()-start;expected=json.loads(bgpath.read_text());normalize=lambda v:{r['connection_id']:r for r in v['connections']}
assert json.loads(json.dumps(normalize(result)))==json.loads(json.dumps(normalize(expected)));assert result['node_occupancy']==expected['node_occupancy']
(out/'receipt.json').write_text(json.dumps({'protocol_sha256':sha(out/'protocol.json'),'background_acquisition_s':wall,'exact_paths_methods_and_union':True,'scope':p['scope']},indent=2)+'\n');print(wall)
