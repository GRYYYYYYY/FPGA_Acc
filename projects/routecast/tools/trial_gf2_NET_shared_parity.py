"""Unchanged shared-search implementation transferred to all GF2 capacity cases."""
import json,time
from pathlib import Path
from pre_route_endpoints import sha
from persistent_rc_context import PersistentRCContext
from net_shared_capacity_forecast import forecast
root=Path(__file__).resolve().parents[1];base=root/'experiments/gf2_capacity_forecast_2026-10-06'
p=json.loads((base/'protocol.json').read_text());r=json.loads((base/'receipt.json').read_text());assert r['protocol_sha256']==sha(base/'protocol.json')
out=root/'experiments/gf2_NET_shared_parity_2026-10-06';out.mkdir();cases=[]
for c in p['cases']:
 for mode in ['hard','soft']:
  f=base/f"gf2_d{c['data_width']}_w{c['channels']}_{mode}.json"
  row=next(x for x in r['rows'] if x['data_width']==c['data_width'] and x['channels']==c['channels'] and x['mode']==mode)
  assert sha(f)==row['candidate_sha256'];cases.append({**c,'mode':mode,'baseline':str(f),'baseline_sha256':sha(f)})
protocol={'cases':cases,'sources_sha256':{n:sha(root/'tools'/n) for n in ['net_shared_capacity_forecast.py','pressure_capacity_forecast.py','persistent_rc_context.py','trial_gf2_NET_shared_parity.py']},'scope':'All9 GF2 cases both hard/soft modes; unchanged implementation after mux ABBA. Full output parity excluding expanded counters required, includes failure semantics. Fresh/archive timing descriptive only.'}
(out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');rows=[]
for c in cases:
 assert sha(c['endpoint_path'])==c['endpoint_sha256'];ctx=PersistentRCContext(c['endpoint_path']);t=time.monotonic();q=forecast(ctx,c['mode']=='soft');elapsed=time.monotonic()-t
 file=out/f"gf2_d{c['data_width']}_w{c['channels']}_{c['mode']}.json";file.write_text(json.dumps(q,indent=2)+'\n');q=json.loads(file.read_text());old=json.loads(Path(c['baseline']).read_text())
 equal={k:v for k,v in q.items() if k!='events'}=={k:v for k,v in old.items() if k!='events'} and [{k:v for k,v in e.items() if k!='expanded'} for e in q['events']]==[{k:v for k,v in e.items() if k!='expanded'} for e in old['events']]
 row={'data_width':c['data_width'],'channels':c['channels'],'mode':c['mode'],'search_s':elapsed,'status':q['status'],'completed_connections':q['completed_connections'],'semantic_parity':equal,'output_sha256':sha(file)};rows.append(row)
 (out/'receipt.json').write_text(json.dumps({'protocol_sha256':sha(out/'protocol.json'),'rows':rows,'complete':len(rows)==18},indent=2)+'\n');print(row,flush=True)
