"""Frozen first100net implementation equivalence probe against archived blend."""
import json,time,shutil
from pathlib import Path
from collections import defaultdict
from pre_route_endpoints import sha
from rr_graph import read_rr_graph
from cached_bound_rc import CachedBoundRC
from exact_goal_astar import ExactGoalAStar
from physical_prediction_audit import audit
from rr_occupancy import Occupancy
from connection_golden import Result
out=Path('experiments/clma_goal_astar_probe_2026-10-04');cap=Path('experiments/clma_cost_binding_2026-10-04');front=Path('experiments/clma_constant_policy_2026-10-04/endpoints.json');gold=Path('experiments/clma_normalized_transfer_2026-10-04/blend_prediction.json')
if out.exists():raise ValueError('fresh output required')
p=json.loads((cap/'protocol.json').read_text());r=json.loads((cap/'receipt.json').read_text());inputs={'graph':p['inputs']['graph'],'table':{'path':str((cap/'rr_indexed_data.echo').resolve()),'sha256':r['reports']['rr_indexed_data.echo']},'binding':{'path':str((cap/'routecast_node_cost_indices.csv').resolve()),'sha256':r['reports']['routecast_node_cost_indices.csv']},'endpoints':{'path':str(front.resolve()),'sha256':sha(front)},'reference':{'path':str(gold.resolve()),'sha256':sha(gold)}};assert all(sha(v['path'])==v['sha256'] for v in inputs.values());e=json.loads(front.read_text());groups=defaultdict(list)
for row in e['connections']:groups[row['net_id']].append(row)
selected={n:groups[n] for n in sorted(groups)[:100]};out.mkdir();(out/'source').mkdir()
for f in Path(__file__).parent.glob('*.py'):shutil.copyfile(f,out/'source'/f.name)
proto={'inputs':inputs,'scope':'implementation probe only, frozen first100ascendingnetIDs; exact archived canonical paths required','heuristic':'directed dest-to-source bbox expansion bound, target min for16orless, zero fallback above16','source_sha256':{f.name:sha(f) for f in (out/'source').glob('*.py')}};(out/'protocol.json').write_text(json.dumps(proto,indent=2)+'\n');start=time.monotonic();g=read_rr_graph(inputs['graph']['path']);model=CachedBoundRC(g,Path(inputs['table']['path']).read_text(),Path(inputs['binding']['path']).read_text(),{'graph_sha256':g.sha256,'table_sha256':inputs['table']['sha256'],'bindings_sha256':inputs['binding']['sha256']});a=ExactGoalAStar(model);prep=time.monotonic()-start;goldmap={row['connection_id']:row for row in json.loads(gold.read_text())['connections']};ledger=Occupancy(g);rows=[];edgework=0;start=time.monotonic()
for net,cohort in selected.items():
 source=cohort[0]['source'];result=a.search(source,{row['sink'] for row in cohort});edgework+=result.edge_visits
 for row in cohort:
  path=result.paths[row['sink']];assert list(path)==goldmap[row['connection_id']]['physical_edge_ids'];assert ledger.update(row['connection_id'],1,net,source,row['sink'],path)==Result.COMMITTED;rows.append({**row,'physical_edge_ids':path,'method':'exact_goal_astar'})
query=time.monotonic()-start;prediction={'physical_graph_sha256':g.sha256,'connections':rows,'node_occupancy':{str(n):v for n,v in ledger.occupancy.items() if v},'requested':len(rows),'completed':len(rows),'methods':{'exact_goal_astar':len(rows)}};checked=audit(g,{**e,'connections':[r for cohort in selected.values() for r in cohort]},prediction);(out/'prediction.json').write_text(json.dumps(prediction)+'\n');assert all(sha(v['path'])==v['sha256'] for v in inputs.values());receipt={'protocol_sha256':sha(out/'protocol.json'),'nets':100,'connections':len(rows),'all_paths_exact_archived_control':True,'alpha':a.alpha,'bbox_classes':a.bbox_classes,'preparation_including_graph_s':prep,'query_ledger_s':query,'edge_visits':edgework,'audit':checked,'inputs_unchanged':True,'prediction_sha256':sha(out/'prediction.json'),'timing_scope':'overlapsKoiosjob, no performance claim'};(out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt),flush=True)
