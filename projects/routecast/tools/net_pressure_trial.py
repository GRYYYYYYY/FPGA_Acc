"""Own-net pressure exclusion and matched net/source group split control."""
from collections import defaultdict
import json,time,shutil,signal
from pathlib import Path
from pre_route_endpoints import sha
from rr_graph import read_rr_graph
from net_pressure_sketch import NetPressure
from rr_occupancy import Occupancy
from connection_golden import Result
from physical_prediction_audit import audit
parent=Path('experiments/frozen_pressure_2026-10-04');out=Path('experiments/net_pressure_2026-10-04')
if out.exists():raise ValueError('fresh output required')
past=json.loads((parent/'protocol.json').read_text());out.mkdir();(out/'source').mkdir()
for f in Path(__file__).parent.glob('*.py'):shutil.copyfile(f,out/'source'/f.name)
p={'scope':'single full pressure pass on two development designs; matched split-groups retain-own/exclude-own control','inputs':past['inputs'],'alpha':256,'variants':['retain_own','exclude_own'],'group':'(net_id,SOURCE), all sinks of net/source','background':'unchanged prior hybrid prediction; unique-net node union, subtract queried net exactly once per node','cache':'new arc view per query; no cross-net/source/cost caches','budget':'all graph nodes','timeout_per_design_s':600,'primary':'resource accuracy and requested coverage, query group/work/time expansion vs previous SOURCE-only trial','source_sha256':{f.name:sha(f) for f in (out/'source').glob('*.py')}}
(out/'protocol.json').write_text(json.dumps(p,indent=2)+'\n');reports=[]
def timeout(*args):raise TimeoutError('design600s timeout')
signal.signal(signal.SIGALRM,timeout)
for name,paths in p['inputs'].items():
    signal.alarm(600)
    for v in paths.values():assert sha(v['path'])==v['sha256']
    start=time.monotonic();g=read_rr_graph(paths['graph']['path']);e=json.loads(Path(paths['endpoints']['path']).read_text());bg=json.loads(Path(paths['background_prediction']['path']).read_text());audit(g,e,bg);engine=NetPressure(g,bg,256);prep=time.monotonic()-start;groups=defaultdict(list)
    for r in e['connections']:groups[(r['net_id'],r['source'])].append(r)
    for variant in p['variants']:
        start=time.monotonic();ledger=Occupancy(g);rows=[];visits=settled=0;contexts={}
        for (net,source),cohort in sorted(groups.items()):
            result,key=engine.query(net,source,{r['sink'] for r in cohort},variant=='exclude_own');contexts[f'{net}:{source}']=key;visits+=result.edge_visits;settled+=result.settled_nodes
            for r in cohort:
                path=result.paths.get(r['sink']);assert path is not None
                assert ledger.update(r['connection_id'],1,net,source,r['sink'],path)==Result.COMMITTED
                rows.append({**r,'physical_edge_ids':path,'method':variant})
        wall=time.monotonic()-start;pred={'physical_graph_sha256':g.sha256,'connections':rows,'node_occupancy':{str(n):v for n,v in ledger.occupancy.items() if v},'methods':{variant:len(rows)},'requested':len(rows),'completed':len(rows)};checked=audit(g,e,pred)
        (out/f'{name}_{variant}.json').write_text(json.dumps(pred)+'\n');(out/f'{name}_{variant}_contexts.json').write_text(json.dumps(contexts)+'\n')
        report={'design':name,'variant':variant,'preparation_and_background_audit_s':prep,'query_search_ledger_s':wall,'net_source_groups':len(groups),'original_source_groups':len({s for n,s in groups}),'requested':len(rows),'edge_visits':visits,'settled_nodes':settled,'overflow_units':sum(ledger.overflow().values()),'independent_audit':checked};reports.append(report);print(json.dumps(report),flush=True)
    for v in paths.values():assert sha(v['path'])==v['sha256']
    signal.alarm(0)
(out/'receipt.json').write_text(json.dumps({'protocol_sha256':sha(out/'protocol.json'),'reports':reports,'artifacts':{f.name:sha(f) for f in out.glob('*.json') if f.name not in ('protocol.json','receipt.json')}},indent=2)+'\n')
