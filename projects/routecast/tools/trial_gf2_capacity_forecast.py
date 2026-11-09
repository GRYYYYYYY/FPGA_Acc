"""Freeze two policies across entire pressure cohort before outcome evaluation."""
import json,time
from pathlib import Path
from pre_route_endpoints import sha
from persistent_rc_context import PersistentRCContext
from pressure_capacity_forecast import forecast
root=Path(__file__).resolve().parents[1];base=root/'experiments/gf2_pressure_prediction_2026-10-06';r=json.loads((base/'receipt.json').read_text());out=root/'experiments/gf2_capacity_forecast_2026-10-06';out.mkdir();cases=[]
for row in r['rows']:
 w=row['data_width'];ch=row['channels'];ep=base/f'gf2_d{w}_w{ch}/endpoints.json';cases.append({'data_width':w,'channels':ch,'endpoint_path':str(ep),'endpoint_sha256':sha(ep)})
(out/'protocol.json').write_text(json.dumps({'cases':cases,'sources_sha256':{n:sha(root/'tools'/n) for n in ('pressure_capacity_forecast.py','persistent_rc_context.py','trial_gf2_capacity_forecast.py')},'policies':['hard_capacity_no_budget','soft_capacity_no_budget'],'order':'sortedNET/CID; complete Dijkstra no labelcap/delaybudget; consistent NETparents;exactRC*(1+otherNETdemand)','scope':'Posthoc two-development-policy ablation on all9cases, no native route/STA inputs. Softoveruse is forecast, not publishable legalroute; originalfrozenjointpolicy unchanged.'},indent=2)+'\n');rows=[]
for c in cases:
 for soft in (False,True):
  t=time.monotonic();ctx=PersistentRCContext(c['endpoint_path']);setup=time.monotonic()-t;t=time.monotonic();result=forecast(ctx,soft);search=time.monotonic()-t;mode='soft' if soft else 'hard';file=out/f"gf2_d{c['data_width']}_w{c['channels']}_{mode}.json";file.write_text(json.dumps(result,indent=2)+'\n');row={'data_width':c['data_width'],'channels':c['channels'],'mode':mode,'status':result['status'],'completed_connections':result['completed_connections'],'required_connections':result['required_connections'],'overflow_units':result['overflow_units'],'over_1ns_connections':result['over_1ns_connections'],'setup_s':setup,'search_s':search,'candidate_sha256':sha(file)};rows.append(row);assert sha(c['endpoint_path'])==c['endpoint_sha256'];print(row,flush=True)
(out/'receipt.json').write_text(json.dumps({'protocol_sha256':sha(out/'protocol.json'),'rows':rows,'all_cases_retained':len(rows)==18},indent=2)+'\n')
