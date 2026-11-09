"""Predeclared full-cohort max4 history feedback; full rebuild each pass."""
import json,time
from pathlib import Path
from collections import Counter
from pre_route_endpoints import sha
from persistent_rc_context import PersistentRCContext
from negotiated_pressure_forecast import forecast
root=Path(__file__).resolve().parents[1];base=root/'experiments/gf2_capacity_forecast_2026-10-06';p=json.loads((base/'protocol.json').read_text());out=root/'experiments/gf2_negotiated_pressure_2026-10-06';out.mkdir();protocol={'cases':p['cases'],'sources_sha256':{n:sha(root/'tools'/n) for n in ('negotiated_pressure_forecast.py','persistent_rc_context.py','trial_gf2_negotiated_pressure.py')},'policy':'Initialfullsoftforecast,presentfactor1/history0; max4feedbacks. Add preceding all-type nodeoverflow tohistory; presentfactor2**pass. Fresh fullNET/CID orderedledger/parents eachpass,unchanged exactRC/no delaybudget. Stop incomplete orzerooverflow. No choosebestpass,finalpass retained.','scope':'Posthocdevelopment negotiation ablation acrossall9pressurecases; no native labelsasinputs or publishingsoftoverusedroutes. Fullrebuildcostnotincrementalbenefit.'};(out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');rows=[]
for c in p['cases']:
 w=c['data_width'];ch=c['channels'];d=out/f'gf2_d{w}_w{ch}';d.mkdir();t=time.monotonic();ctx=PersistentRCContext(c['endpoint_path']);setup=time.monotonic()-t;history=Counter();passes=[]
 for iteration in range(5):
  t=time.monotonic();q=forecast(ctx,True,dict(history),2**iteration);elapsed=time.monotonic()-t;file=d/f'pass{iteration}.json';file.write_text(json.dumps(q,indent=2)+'\n');passes.append({'pass':iteration,'status':q['status'],'connections':q['completed_connections'],'overflow_units':q['overflow_units'],'over_1ns_connections':q['over_1ns_connections'],'search_s':elapsed,'receipt_sha256':sha(file)})
  if q['failure'] is not None or q['overflow_units']==0:break
  history.update({int(n):max(0,v-ctx.rc.fields['capacities'][int(n)]) for n,v in q['ledger'].items()})
 (d/'receipt.json').write_text(json.dumps(q,indent=2)+'\n');rows.append({'data_width':w,'channels':ch,'setup_s':setup,'passes':passes,'final_sha256':sha(d/'receipt.json')});assert sha(c['endpoint_path'])==c['endpoint_sha256'];print(w,ch,[x['overflow_units'] for x in passes],q['status'],flush=True)
(out/'receipt.json').write_text(json.dumps({'protocol_sha256':sha(out/'protocol.json'),'rows':rows,'all_cases_retained':len(rows)==9},indent=2)+'\n')
