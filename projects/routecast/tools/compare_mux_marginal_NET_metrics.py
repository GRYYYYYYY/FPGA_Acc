"""Compare independently verified marginal and original full-cohort metrics."""
import json
from pathlib import Path
from pre_route_endpoints import sha
root=Path(__file__).resolve().parents[1];bases=[root/'experiments'/n for n in ['mux_crossbar_soft_metrics_2026-10-06','mux_marginal_NET_metrics_2026-10-06']];receipts=[]
for base in bases:
 v=json.loads((base/'verification.json').read_text());assert v['receipt_sha256']==sha(base/'receipt.json');r=json.loads((base/'receipt.json').read_text());assert r['all_cases_retained'] and len(r['rows'])==9;receipts.append(r)
rows=[]
for a,b in zip(receipts[0]['rows'],receipts[1]['rows']):
 assert (a['data_width'],a['channels'])==(b['data_width'],b['channels']) and a['status']==b['status']=='SCORED_COMPLETE'
 row={'data_width':a['data_width'],'channels':a['channels'],'rho_original':a['utilization_spearman'],'rho_marginal':b['utilization_spearman'],'rho_delta':b['utilization_spearman']-a['utilization_spearman'],'MAE_original':a['utilization_MAE'],'MAE_marginal':b['utilization_MAE'],'overflow_original':a['overflow_support'],'overflow_marginal':b['overflow_support']};rows.append(row);print(row,flush=True)
out=bases[1]/'comparison.json';out.write_text(json.dumps({'receipt_bindings':{str(b/'receipt.json'):sha(b/'receipt.json') for b in bases},'rows':rows,'scope':'All9 paired same-native labels, posthoc development comparison; failed32 native occupancy not legal target. No statistical/unseen-family/end-to-end claim.'},indent=2)+'\n')
