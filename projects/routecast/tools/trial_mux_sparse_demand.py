"""Whole-cohort sparse demand lookup exact forecast parity, archived baseline timing."""
import json,time
from pathlib import Path
from pre_route_endpoints import sha
from persistent_rc_context import PersistentRCContext
from sparse_demand_capacity_forecast import forecast
root=Path(__file__).resolve().parents[1];base=root/'experiments/mux_crossbar_soft_transfer_2026-10-06';p=json.loads((base/'protocol.json').read_text());r=json.loads((base/'receipt.json').read_text());v=json.loads((base/'verification.json').read_text());assert v['receipt_sha256']==sha(base/'receipt.json');out=root/'experiments/mux_sparse_demand_2026-10-06';out.mkdir();cases=[]
for c,row in zip(p['cases'],r['rows']):
 baseline=base/f"gf2_d{c['data_width']}_w{c['channels']}_soft.json";cases.append({**c,'baseline':str(baseline),'baseline_sha256':sha(baseline),'baseline_search_s':row['search_s']})
(out/'protocol.json').write_text(json.dumps({'cases':cases,'sources_sha256':{n:sha(root/'tools'/n) for n in ('sparse_demand_capacity_forecast.py','pressure_capacity_forecast.py','persistent_rc_context.py','trial_mux_sparse_demand.py')},'scope':'All9 cases, unchanged softpolicy; only wholeledgercopy replacedby pointlookup ledgerminusownunion. RequireentirecandidateJSONvalueequalityincludingpaths/delays/costs/events/expansions/ledger/failure. Fresh observationvsarchive timingnotpairedbenchmark.'},indent=2)+'\n');rows=[]
for c in cases:
 assert sha(c['endpoint_path'])==c['endpoint_sha256'] and sha(c['baseline'])==c['baseline_sha256'];t=time.monotonic();ctx=PersistentRCContext(c['endpoint_path']);setup=time.monotonic()-t;t=time.monotonic();q=forecast(ctx,True);elapsed=time.monotonic()-t;file=out/f"mux_w{c['data_width']}_c{c['channels']}.json";file.write_text(json.dumps(q,indent=2)+'\n');exact=q==json.loads(Path(c['baseline']).read_text());row={'data_width':c['data_width'],'channels':c['channels'],'setup_s':setup,'search_s':elapsed,'baseline_search_s':c['baseline_search_s'],'entire_forecast_exact':exact,'candidate_sha256':sha(file)};rows.append(row);(out/'receipt.json').write_text(json.dumps({'protocol_sha256':sha(out/'protocol.json'),'rows':rows,'all_cases_retained':len(rows)==len(cases)},indent=2)+'\n');print(row,flush=True)
