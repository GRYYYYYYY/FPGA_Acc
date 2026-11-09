"""Compare XML-audited per-connection RC delay and whole-ledger volume."""
import json,statistics
from pathlib import Path
from pre_route_endpoints import sha
root=Path(__file__).resolve().parents[1];a=root/'experiments/mux_crossbar_soft_transfer_2026-10-06';b=root/'experiments/mux_bundle_pressure_2026-10-06'
for base in [a,b]:
 v=json.loads((base/'verification.json').read_text());assert v['receipt_sha256']==sha(base/'receipt.json')
p=json.loads((b/'protocol.json').read_text());rows=[]
for c in p['cases']:
 w=c['data_width'];ch=c['channels'];oldfile=Path(c['baseline']);newfile=b/f'mux_w{w}_c{ch}.json';assert sha(oldfile)==c['baseline_sha256'];old=json.loads(oldfile.read_text());new=json.loads(newfile.read_text());assert old['scale']==new['scale']
 pairs=list(zip(old['records'],new['records']));assert len(pairs)==old['required_connections']==new['required_connections']
 for x,y in pairs:assert all(x[k]==y[k] for k in ['net_id','connection_id','source','sink'])
 delta=[y['answer']['delay']-x['answer']['delay'] for x,y in pairs];row={'data_width':w,'channels':ch,'connections':len(pairs),'paths_changed':sum(x['answer']['physical_edge_ids']!=y['answer']['physical_edge_ids'] for x,y in pairs),'delay_increased':sum(d>0 for d in delta),'delay_decreased':sum(d<0 for d in delta),'mean_delay_delta_ns':statistics.mean(delta)/new['scale']*1e9,'maximum_delay_original_ns':max(x['answer']['delay'] for x,y in pairs)/new['scale']*1e9,'maximum_delay_bundlepressure_ns':max(y['answer']['delay'] for x,y in pairs)/new['scale']*1e9,'bindings':{str(f):sha(f) for f in [oldfile,newfile]}};rows.append(row);print(row,flush=True)
(b/'path_comparison.json').write_text(json.dumps({'rows':rows,'scope':'Forecast perconnection exactRC delays only, not native CPD or STA. Both forecasts originally XML audited; no speedup or timingquality proof.'},indent=2)+'\n')
