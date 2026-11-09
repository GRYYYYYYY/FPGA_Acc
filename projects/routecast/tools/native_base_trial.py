"""Frozen normalized native base-cost-only ablation, graph/endpoints only."""
from collections import defaultdict
import json,time,shutil
from pathlib import Path
from pre_route_endpoints import sha
from rr_graph import read_rr_graph
from native_indexed_cost import NativeBaseSketch
from rr_occupancy import Occupancy
from connection_golden import Result
from physical_prediction_audit import audit
out=Path('experiments/native_base_cost_2026-10-04')
if out.exists():raise ValueError('fresh output required')
epath=Path('experiments/pre_route_endpoints_2026-10-04/diffeq_endpoints.json');e=json.loads(epath.read_text());paths={'graph':Path(e['inputs']['graph']['path']),'endpoints':epath,'cost_table':Path('experiments/vpr_cost_diagnosis_2026-10-04/rr_indexed_data.echo'),'cost_capture_protocol':Path('experiments/baseline_timing_echo_2026-10-04/protocol.json')};capture=json.loads(paths['cost_capture_protocol'].read_text());assert capture['inputs']['graph']['sha256']==sha(paths['graph'])
out.mkdir();(out/'source').mkdir()
for f in Path(__file__).parent.glob('*.py'):shutil.copyfile(f,out/'source'/f.name)
p={'scope':'single design native normalized base-cost ablation; consumes no native final route/timing labels','inputs':{k:{'path':str(v.resolve()),'sha256':sha(v)} for k,v in paths.items()},'fixed_scale':1000000,'cost':'round normalized indexed destination base cost only; no congestion/criticality/RC/switch delay/path tree/lookahead','budget':'all nodes','source_sha256':{f.name:sha(f) for f in (out/'source').glob('*.py')}}
(out/'protocol.json').write_text(json.dumps(p,indent=2)+'\n');start=time.monotonic();g=read_rr_graph(paths['graph']);engine=NativeBaseSketch(g,paths['cost_table'].read_text(),capture['inputs']['graph']['sha256']);prep=time.monotonic()-start;groups=defaultdict(list)
for row in e['connections']:groups[row['source']].append(row)
ledger=Occupancy(g);rows=[];visits=0;start=time.monotonic()
for source,cohort in sorted(groups.items()):
    result=engine.search(source,{r['sink'] for r in cohort});visits+=result.edge_visits
    for row in cohort:
        path=result.paths.get(row['sink']);assert path is not None;assert ledger.update(row['connection_id'],1,row['net_id'],source,row['sink'],path)==Result.COMMITTED;rows.append({**row,'physical_edge_ids':path,'method':'native_base_only'})
wall=time.monotonic()-start;prediction={'physical_graph_sha256':g.sha256,'connections':rows,'node_occupancy':{str(n):v for n,v in ledger.occupancy.items() if v},'methods':{'native_base_only':len(rows)},'requested':len(rows),'completed':len(rows)};checked=audit(g,e,prediction);(out/'prediction.json').write_text(json.dumps(prediction)+'\n')
r={'protocol_sha256':sha(out/'protocol.json'),'preparation_s':prep,'search_ledger_s':wall,'edge_visits':visits,'audit':checked,'prediction_sha256':sha(out/'prediction.json'),'input_hashes_unchanged':all(sha(v['path'])==v['sha256'] for v in p['inputs'].values())};(out/'receipt.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r))
