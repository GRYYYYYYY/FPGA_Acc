"""Pre-frozen all-buffered RC-only full-search ablation on two designs."""
from collections import defaultdict
import json,time,shutil
from pathlib import Path
from pre_route_endpoints import sha
from rr_graph import read_rr_graph
from slim_fast_normalized_rc_net_pressure import SlimFastNormalizedRCNetPressure
from rr_occupancy import Occupancy
from connection_golden import Result
from physical_prediction_audit import audit
out=Path('experiments/slim_fast_normalized_rc_net_pressure_search_2026-10-04')
if out.exists():raise ValueError('fresh output required')
out.mkdir();(out/'source').mkdir()
for f in Path(__file__).parent.glob('*.py'):shutil.copyfile(f,out/'source'/f.name)
inputs={}
for design,path in [('diffeq','experiments/pre_route_endpoints_2026-10-04/diffeq_endpoints.json'),('elliptic','experiments/elliptic_endpoints_2026-10-04/endpoints.json')]:
 ep=Path(path);endpoints=json.loads(ep.read_text());inputs[design]={'endpoints':{'path':str(ep.resolve()),'sha256':sha(ep)},'graph':endpoints['inputs']['graph']}
for design in inputs:
 capture_path=Path('experiments/baseline_timing_echo_2026-10-04/protocol.json') if design=='diffeq' else Path('experiments/elliptic_base_echo_2026-10-04/protocol.json')
 table_path=Path('experiments/vpr_cost_diagnosis_2026-10-04/rr_indexed_data.echo') if design=='diffeq' else Path('experiments/elliptic_base_echo_2026-10-04/rr_indexed_data.echo')
 capture=json.loads(capture_path.read_text())
 assert capture['inputs']['graph']['sha256']==inputs[design]['graph']['sha256']
 inputs[design]['cost_table']={'path':str(table_path.resolve()),'sha256':sha(table_path)}
 inputs[design]['capture_protocol']={'path':str(capture_path.resolve()),'sha256':sha(capture_path)}
for design in inputs:
 background=Path('experiments/normalized_rc_base_search_2026-10-04')/f'{design}_prediction.json'
 inputs[design]['background']={'path':str(background.resolve()),'sha256':sha(background)}
protocol={'timing_interpretation':'verification run overlaps separate memory-accounting process; timings not performance evidence','pressure_factor':1,'pressure_scope':'channel base term only, frozen previous normalized blend prediction, own net unique-node union excluded, single pass','inputs':inputs,'scale':10**6,'scope':'equal half RC/norm+base/norm; graph+endpoints+indexed tables only, frozen predicted demand only, no native routes/criticality/delay labels; all buffered required','rounding':'blend and pressure separately nearest ties even; combined max per-edge error1e-6 normalized cost units','budget':'all nodes','source_sha256':{f.name:sha(f) for f in (out/'source').glob('*.py')}}
(out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');receipts={}
for design,paths in inputs.items():
 assert all(sha(v['path'])==v['sha256'] for v in paths.values())
 e=json.loads(Path(paths['endpoints']['path']).read_text());start=time.monotonic();g=read_rr_graph(paths['graph']['path']);assert g.sha256==e['graph_sha256'];background=json.loads(Path(paths['background']['path']).read_text());background_audit=audit(g,e,background);engine=SlimFastNormalizedRCNetPressure(g,Path(paths['cost_table']['path']).read_text(),paths['graph']['sha256'],background);prep=time.monotonic()-start
 groups=defaultdict(list)
 for row in e['connections']:groups[(row['net_id'],row['source'])].append(row)
 ledger=Occupancy(g);rows=[];visits=0;start=time.monotonic()
 for (net,source),cohort in sorted(groups.items()):
  result,context=engine.query(net,source,{r['sink'] for r in cohort},True);visits+=result.edge_visits
  for row in cohort:
   path=result.paths.get(row['sink']);assert path is not None
   assert ledger.update(row['connection_id'],1,row['net_id'],source,row['sink'],path)==Result.COMMITTED
   rows.append({**row,'physical_edge_ids':path,'method':'normalized_rc_net_pressure'})
 elapsed=time.monotonic()-start;pred={'physical_graph_sha256':g.sha256,'connections':rows,'node_occupancy':{str(n):v for n,v in ledger.occupancy.items() if v},'methods':{'normalized_rc_net_pressure':len(rows)},'requested':len(rows),'completed':len(rows)}
 checked=audit(g,e,pred)
 prior_dir=Path('experiments/normalized_rc_net_pressure_search_2026-10-04');prior_pred=json.loads((prior_dir/f'{design}_prediction.json').read_text());prior_receipt=json.loads((prior_dir/f'{design}_receipt.json').read_text())
 assert prior_receipt['prediction_sha256']==sha(prior_dir/f'{design}_prediction.json')
 assert json.loads(json.dumps(pred))==prior_pred and visits==prior_receipt['edge_visits']
 output=out/f'{design}_prediction.json';output.write_text(json.dumps(pred)+'\n')
 receipts[design]={'exact_prior_prediction_and_edge_visits':True,'net_source_groups':len(groups),'background_audit':background_audit,'preparation_s':prep,'search_ledger_s':elapsed,'edge_visits':visits,'audit':checked,'prediction_sha256':sha(output),'input_hashes_unchanged':all(sha(v['path'])==v['sha256'] for v in paths.values())}
 (out/f'{design}_receipt.json').write_text(json.dumps(receipts[design],indent=2)+'\n');print(design+' '+json.dumps(receipts[design]),flush=True)
(out/'receipt.json').write_text(json.dumps({'protocol_sha256':sha(out/'protocol.json'),'designs':receipts},indent=2)+'\n')
