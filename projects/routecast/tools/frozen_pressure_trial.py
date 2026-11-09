"""Frozen one-pass demand-pressure trial; predictor-only background, no labels."""
from collections import defaultdict
import json,shutil,time,signal
from pathlib import Path
from pre_route_endpoints import sha
from rr_graph import read_rr_graph
from frozen_pressure_sketch import FrozenPressureSketch
from rr_occupancy import Occupancy
from connection_golden import Result
from physical_prediction_audit import audit
out=Path('experiments/frozen_pressure_2026-10-04')
if out.exists():raise ValueError('fresh output required')
cases={'diffeq':('experiments/pre_route_endpoints_2026-10-04/diffeq_endpoints.json','experiments/lazy_repair_serialization_fix_2026-10-04/lazy_2.json'),'elliptic':('experiments/elliptic_endpoints_2026-10-04/endpoints.json','experiments/elliptic_transfer_2026-10-04/prediction.json')}
out.mkdir();(out/'source').mkdir()
for f in Path(__file__).parent.glob('*.py'):shutil.copyfile(f,out/'source'/f.name)
inputs={}
for name,(ep,bg) in cases.items():
    e=json.loads(Path(ep).read_text());inputs[name]={k:{'path':str(Path(v).resolve()),'sha256':sha(v)} for k,v in {'endpoints':ep,'background_prediction':bg,'graph':e['inputs']['graph']['path']}.items()}
p={'scope':'one additional frozen pressure pass; development designs, not heldout families or negotiated routing','inputs':inputs,'alpha':256,'rule':'channel destination ceil(256*max(0,background unique-net demand-capacity+1)/capacity)','background':'previous two-round hybrid predictor occupancy, includes queried net itself; no native routes/timing labels','budget':'all nodes','timeout_per_case_s':600,'cache':'new per-context engine, no reused search caches','source_sha256':{f.name:sha(f) for f in (out/'source').glob('*.py')}}
(out/'protocol.json').write_text(json.dumps(p,indent=2)+'\n');reports=[]
def timeout(*args):raise TimeoutError('case exceeded frozen600s')
signal.signal(signal.SIGALRM,timeout)
for name,paths in inputs.items():
    signal.alarm(600);start=time.monotonic()
    for entry in paths.values():assert sha(entry['path'])==entry['sha256']
    g=read_rr_graph(paths['graph']['path']);e=json.loads(Path(paths['endpoints']['path']).read_text());bg=json.loads(Path(paths['background_prediction']['path']).read_text());assert bg['physical_graph_sha256']==g.sha256;assert e['graph_sha256']==g.sha256
    engine=FrozenPressureSketch(g,{int(n):v for n,v in bg['node_occupancy'].items()},g.sha256,256,len(g.nodes));prepared=time.monotonic()-start
    groups=defaultdict(list)
    for r in e['connections']:groups[r['source']].append(r)
    ledger=Occupancy(g);rows=[];traces=[];start=time.monotonic()
    for source,cohort in sorted(groups.items()):
        search=engine.search(source,{r['sink'] for r in cohort});traces.append({'source':source,'settled_nodes':search.settled_nodes,'edge_visits':search.edge_visits})
        for r in cohort:
            path=search.paths.get(r['sink']);assert path is not None
            assert ledger.update(r['connection_id'],1,r['net_id'],source,r['sink'],path)==Result.COMMITTED
            rows.append({**r,'physical_edge_ids':path,'method':'pressure'})
    search_s=time.monotonic()-start
    prediction={'physical_graph_sha256':g.sha256,'context_sha256':engine.context_sha256,'connections':rows,'node_occupancy':{str(n):v for n,v in ledger.occupancy.items() if v},'methods':{'pressure':len(rows)},'requested':len(rows),'completed':len(rows)}
    checked=audit(g,e,prediction);(out/f'{name}_prediction.json').write_text(json.dumps(prediction)+'\n')
    report={'design':name,'context_sha256':engine.context_sha256,'preparation_wall_s':prepared,'search_and_ledger_wall_s':search_s,'requested':len(rows),'completed':len(rows),'edge_visits':sum(r['edge_visits'] for r in traces),'overflow_nodes':len(ledger.overflow()),'changed_paths':sum(tuple(r['physical_edge_ids'])!=tuple({a['connection_id']:a for a in bg['connections']}[r['connection_id']]['physical_edge_ids']) for r in rows),'independent_audit':checked};reports.append(report);print(json.dumps(report),flush=True)
    for entry in paths.values():assert sha(entry['path'])==entry['sha256']
    signal.alarm(0)
(out/'receipt.json').write_text(json.dumps({'protocol_sha256':sha(out/'protocol.json'),'reports':reports,'prediction_sha256':{name:sha(out/f'{name}_prediction.json') for name in inputs}},indent=2)+'\n')
