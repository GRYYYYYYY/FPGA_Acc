"""Cold Koios full-model build and pre-frozen maximum-fanout group probe."""
import json,time,shutil,os
from pathlib import Path
from collections import defaultdict,Counter
from fractions import Fraction
from pre_route_endpoints import sha
from rr_graph import read_rr_graph
from cached_bound_rc import CachedBoundRC
from path_rc import PathRC,State
from physical_prediction_audit import audit
from rr_occupancy import Occupancy
from connection_golden import Result
out=Path('experiments/koios_full_cached_rc_2026-10-04');cap=Path('experiments/koios_spmv_cost_binding_2026-10-04');front=Path('experiments/koios_spmv_endpoints_v2_2026-10-04')
if out.exists():raise ValueError('fresh output required')
r=json.loads((cap/'receipt.json').read_text());fr=json.loads((front/'receipt.json').read_text());inputs={k:{'path':str((cap/k).resolve()),'sha256':v} for k,v in r['outputs'].items()};inputs['endpoints']={'path':str((front/'endpoints.json').resolve()),'sha256':fr['outputs']['endpoints.json']};assert r['exit_code']==0 and all(sha(v['path'])==v['sha256'] for v in inputs.values());e=json.loads(Path(inputs['endpoints']['path']).read_text());groups=defaultdict(list)
for row in e['connections']:groups[row['net_id']].append(row)
assert len(e['connections'])==15138 and len(groups)==8998
out.mkdir();(out/'source').mkdir()
for f in Path(__file__).parent.glob('*.py'):shutil.copyfile(f,out/'source'/f.name)
p={'inputs':inputs,'scope':'all15138 connections/8998SOURCEgroups, predictor opens no native route labels','order':'ascending netID, group sinks as set; unchanged independent-source canonical shortest paths','connections':15138,'nets':8998,'node_budget':'entire physical graph','objective':'unchanged normalized halfRC+base/scale1e6/nearest-even, explicit8classbinding, no pressure/tree/lookahead/labels','cost_validation':'same source as completed clma full parity and Koios1001oracle probe; net2 exact probe-path check', 'metrics_frozen':['resource Spearman/top5percent/MAE','spatial Spearman/top20/MAE','overflowunits','allstage costs separately'],'source_sha256':{f.name:sha(f) for f in (out/'source').glob('*.py')}};(out/'protocol.json').write_text(json.dumps(p,indent=2)+'\n');print(json.dumps({'pid':os.getpid(),'stage':'load_graph','nets':8998,'connections':15138}),flush=True);start=time.monotonic();g=read_rr_graph(inputs['rr_graph.xml']['path']);load=time.monotonic()-start;print(json.dumps({'stage':'graph_loaded','load_s':load,'nodes':len(g.nodes),'edges':len(g.edges)}),flush=True);text=Path(inputs['rr_indexed_data.echo']['path']).read_text();csv=Path(inputs['routecast_node_cost_indices.csv']['path']).read_text();identity={'graph_sha256':g.sha256,'table_sha256':inputs['rr_indexed_data.echo']['sha256'],'bindings_sha256':inputs['routecast_node_cost_indices.csv']['sha256']};start=time.monotonic();model=CachedBoundRC(g,text,csv,identity);prep=time.monotonic()-start;print(json.dumps({'stage':'model_ready','preparation_s':prep,'cache_entries':model.cache_entries}),flush=True)
ledger=Occupancy(g);rows=[];visits=0;settled=0;failed=0;start=time.monotonic()
probe=Path('experiments/koios_cached_rc_probe_2026-10-04');pr=json.loads((probe/'receipt.json').read_text());assert pr['outputs']['prediction.json']==sha(probe/'prediction.json');gold={v['connection_id']:v for v in json.loads((probe/'prediction.json').read_text())['connections']}
for i,(net,cohort) in enumerate(sorted(groups.items()),1):
 sources={v['source'] for v in cohort};assert len(sources)==1;source=next(iter(sources));targets={v['sink'] for v in cohort};result=model.search(source,targets);assert not result.budget_exhausted;visits+=result.edge_visits;settled+=result.settled_nodes
 for row in cohort:
  path=result.paths.get(row['sink']);method='cached_bound_rc' if path is not None else 'failed'
  if path is not None:assert ledger.update(row['connection_id'],1,net,source,row['sink'],path)==Result.COMMITTED
  else:failed+=1
  if row['connection_id'] in gold:assert list(path)==gold[row['connection_id']]['physical_edge_ids']
  rows.append({**row,'physical_edge_ids':path,'method':method})
 if i%100==0:print(json.dumps({'stage':'search','completed_nets':i,'connections':len(rows),'failed':failed,'elapsed_s':time.monotonic()-start}),flush=True)
query=time.monotonic()-start;prediction={'physical_graph_sha256':g.sha256,'connections':rows,'node_occupancy':{str(n):v for n,v in ledger.occupancy.items() if v},'requested':len(rows),'completed':len(rows)-failed,'methods':dict(Counter(row['method'] for row in rows))}
for name,data in [('prediction.json',prediction),('endpoints.json',e)]: (out/name).write_text(json.dumps(data)+'\n')
checked=audit(g,e,prediction)
assert all(sha(v['path'])==v['sha256'] for v in inputs.values());receipt={'protocol_sha256':sha(out/'protocol.json'),'graph_load_s':load,'preparation_s':prep,'query_ledger_s':query,'edge_visits':visits,'settled_nodes':settled,'failed_connections':failed,'exact_prior_net2_probe_paths':741,'cache_entries':model.cache_entries,'all_edge_cost_queries':model.edge_cost_queries,'audit':checked,'inputs_unchanged':True,'outputs':{n:sha(out/n) for n in ('prediction.json','endpoints.json')}};(out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt),flush=True)
