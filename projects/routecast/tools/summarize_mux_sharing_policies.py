"""Three-policy same-case summary after all independent physical/metric audits."""
import json
from pathlib import Path
from pre_route_endpoints import sha
root=Path(__file__).resolve().parents[1]
policies={'original':('mux_crossbar_soft_transfer_2026-10-06','mux_crossbar_soft_metrics_2026-10-06'),'free_reuse':('mux_marginal_NET_2026-10-06','mux_marginal_NET_metrics_2026-10-06'),'RC_preserving':('mux_RC_preserving_NET_2026-10-06','mux_RC_preserving_NET_metrics_2026-10-06')};tables={};bindings={}
for name,(routes,metrics) in policies.items():
 routebase=root/'experiments'/routes;metricbase=root/'experiments'/metrics
 for base in [routebase,metricbase]:
  v=json.loads((base/'verification.json').read_text());assert v['receipt_sha256']==sha(base/'receipt.json');bindings[str(base/'receipt.json')]=sha(base/'receipt.json')
 p=json.loads((routebase/'protocol.json').read_text());r=json.loads((metricbase/'receipt.json').read_text());assert len(r['rows'])==9;table={}
 for row in r['rows']:
  w=row['data_width'];ch=row['channels'];file=routebase/(f'gf2_d{w}_w{ch}_soft.json' if name=='original' else f'mux_w{w}_c{ch}.json');q=json.loads(file.read_text());assert q['status']=='COMPLETE_FORECAST';bindings[str(file)]=sha(file)
  table[w,ch]={'rho':row['utilization_spearman'],'MAE':row['utilization_MAE'],'overuse_precision':row['overflow_support']['precision'],'overuse_recall':row['overflow_support']['recall'],'overused_channels':row['overflow_support']['predicted'],'alltype_overflow':q['overflow_units'],'mean_connection_delay_ns':sum(x['answer']['delay'] for x in q['records'])/len(q['records'])/q['scale']*1e9,'max_connection_delay_ns':max(x['answer']['delay'] for x in q['records'])/q['scale']*1e9}
 tables[name]=table
keys=set(tables['original']);assert len(keys)==9 and all(set(t)==keys for t in tables.values())
rows=[{'data_width':w,'channels':ch,'policies':{name:t[w,ch] for name,t in tables.items()}} for w,ch in sorted(keys)]
out=root/'experiments/mux_RC_preserving_NET_metrics_2026-10-06/sharing_policy_summary.json';out.write_text(json.dumps({'bindings':bindings,'rows':rows,'scope':'Same nine posthoc development cases; no chosen-best policy, calibrated failure threshold or unseen-family gain. Native32 labels failed attempts; physical connection delay is not STA CPD.'},indent=2)+'\n')
for row in rows:print(row,flush=True)
