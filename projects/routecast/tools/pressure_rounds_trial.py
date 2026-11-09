"""Three-round full-cohort frozen-demand development trial; no route labels."""
from collections import defaultdict
import json,shutil,time,signal
from pathlib import Path
from pre_route_endpoints import sha
from rr_graph import read_rr_graph
from frozen_pressure_sketch import FrozenPressureSketch
from rr_occupancy import Occupancy
from connection_golden import Result
from physical_prediction_audit import audit
out=Path('experiments/pressure_rounds_2026-10-04');parent=Path('experiments/frozen_pressure_2026-10-04')
if out.exists():raise ValueError('fresh output required')
pp=json.loads((parent/'protocol.json').read_text());pr=json.loads((parent/'receipt.json').read_text());assert pr['protocol_sha256']==sha(parent/'protocol.json')
for n,digest in pr['prediction_sha256'].items():assert sha(parent/f'{n}_prediction.json')==digest
out.mkdir();(out/'source').mkdir()
for f in Path(__file__).parent.glob('*.py'):shutil.copyfile(f,out/'source'/f.name)
p={'scope':'three frozen pressure rounds on two development designs; reuse verified round1, execute2and3; no early stopping, native labels or parameter adjustment','inputs':pp['inputs'],'round1':{n:{'path':str((parent/f'{n}_prediction.json').resolve()),'sha256':digest} for n,digest in pr['prediction_sha256'].items()},'parent_receipt_sha256':sha(parent/'receipt.json'),'alpha':256,'rounds':3,'rule':pp['rule'],'budget':'all nodes','cache':'all caches invalidated/new engine each round','background_cost':'report reused hybrid and round1 artifacts separately; not free in total pipeline','timeout_per_design_s':600,'source_sha256':{f.name:sha(f) for f in (out/'source').glob('*.py')}}
assert p['source_sha256']['frozen_pressure_sketch.py']==pp['source_sha256']['frozen_pressure_sketch.py']
(out/'protocol.json').write_text(json.dumps(p,indent=2)+'\n');reports=[]
def timeout(*args):raise TimeoutError('design600s timeout')
signal.signal(signal.SIGALRM,timeout)
for name,paths in p['inputs'].items():
    signal.alarm(600)
    for v in paths.values():assert sha(v['path'])==v['sha256']
    start=time.monotonic();g=read_rr_graph(paths['graph']['path']);e=json.loads(Path(paths['endpoints']['path']).read_text());load_s=time.monotonic()-start
    previous=json.loads(Path(p['round1'][name]['path']).read_text());assert previous['physical_graph_sha256']==g.sha256
    history=[json.loads(Path(paths['background_prediction']['path']).read_text())['node_occupancy'],previous['node_occupancy']];groups=defaultdict(list)
    for r in e['connections']:groups[r['source']].append(r)
    for round_id in (2,3):
        start=time.monotonic();engine=FrozenPressureSketch(g,{int(n):v for n,v in previous['node_occupancy'].items()},g.sha256,256,len(g.nodes));prep_s=time.monotonic()-start
        ledger=Occupancy(g);rows=[];visits=0;start=time.monotonic()
        for source,cohort in sorted(groups.items()):
            search=engine.search(source,{r['sink'] for r in cohort});visits+=search.edge_visits
            for r in cohort:
                path=search.paths.get(r['sink']);assert path is not None
                assert ledger.update(r['connection_id'],1,r['net_id'],source,r['sink'],path)==Result.COMMITTED
                rows.append({**r,'physical_edge_ids':path,'method':'pressure'})
        search_s=time.monotonic()-start;occupancy={str(n):v for n,v in ledger.occupancy.items() if v}
        prediction={'physical_graph_sha256':g.sha256,'context_sha256':engine.context_sha256,'connections':rows,'node_occupancy':occupancy,'methods':{'pressure':len(rows)},'requested':len(rows),'completed':len(rows)}
        audit_start=time.monotonic();checked=audit(g,e,prediction);audit_s=time.monotonic()-audit_start;old={r['connection_id']:r['physical_edge_ids'] for r in previous['connections']};changed=sum(tuple(r['physical_edge_ids'])!=tuple(old[r['connection_id']]) for r in rows)
        l1=lambda a,b:sum(abs(a.get(n,0)-b.get(n,0)) for n in set(a)|set(b))
        report={'design':name,'round':round_id,'graph_load_wall_s_once':load_s,'context_sha256':engine.context_sha256,'index_prepare_s':prep_s,'search_ledger_s':search_s,'independent_audit_s':audit_s,'edge_visits':visits,'changed_paths':changed,'occupancy_l1_vs_previous':l1(occupancy,history[-1]),'occupancy_l1_vs_two_rounds_ago':l1(occupancy,history[-2]),'overflow_nodes':len(ledger.overflow()),'overflow_units':sum(ledger.overflow().values()),'exact_repeat_of_earlier_occupancy':[i for i,v in enumerate(history) if v==occupancy],'audit':checked};reports.append(report)
        (out/f'{name}_round{round_id}.json').write_text(json.dumps(prediction)+'\n');print(json.dumps(report),flush=True);history.append(occupancy);previous=prediction
    for v in paths.values():assert sha(v['path'])==v['sha256']
    signal.alarm(0)
(out/'receipt.json').write_text(json.dumps({'protocol_sha256':sha(out/'protocol.json'),'reports':reports,'artifacts':{f.name:sha(f) for f in out.glob('*_round*.json')}},indent=2)+'\n')
