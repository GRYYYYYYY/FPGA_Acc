"""Observed component accounting; explicitly incomplete end-to-end paid evidence."""
import json,hashlib,re
from pathlib import Path
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'wbuart_map_instrumentation_cost_v1_2026-10-20'
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 D.mkdir(exist_ok=False);bindings={str(Path(__file__)):sha(__file__)};rows=[]
 for mode,folder in [('H0','wbuart_map_priority_control_v1_2026-10-20/H0'),('MAP','wbuart_map_priority_nonzero_v1_2026-10-20/MAP')]:
  path=E/folder/'receipt.json';r=read(path);audit=path.parent/'complete_event_audit.json';assert read(audit)['events']==2148
  exclusive=['model_setup_seconds','initial_seconds','cpp_prepare_seconds','search_seconds','occupancy_context_seconds','fallback_seconds','ledger_check_seconds'];total=r['total_paid_resident_seconds'];remaining=total-sum(r[k] for k in exclusive);assert remaining>=0 and 0<=r['heuristic_seconds']<=r['search_seconds']<=total
  rows.append({'mode':mode,'case':'w096/episode_01','initializer':'native_retained','timing':'warm_timing_round_updated','resident_seconds':total,'exclusive_measured_components':{k:r[k] for k in exclusive},'unattributed_resident_seconds':remaining,'heuristic_seconds_included_in_search':r['heuristic_seconds'],'search_seconds_excluding_heuristic':r['search_seconds']-r['heuristic_seconds'],'heuristic_fraction_of_resident':r['heuristic_seconds']/total,'heuristic_calls':r['heuristic_calls'],'scope':'One preflight instrumented process; adapter/table creation and matrix-hash validation before predict excluded. Unbalanced existing-source comparison cannot prove speedup.'})
  for p in [path,audit]:bindings[str(p)]=sha(p)
 batch=E/'wbuart_allnet_map_batch_v1_2026-10-20';tables=[]
 for group in ['source','target']:
  mp=batch/(group+'_manifest.json');bindings[str(mp)]=sha(mp)
  for c in read(mp)['cases']:
   if not c['allmap_enabled']:continue
   out=Path(c['output']);log=out/'native.log';text=log.read_text();m=re.search(r'ROUTECAST_ALLMAP targets=(\d+) nodes=(\d+) pins=(\d+) seconds=([0-9.]+)',text);assert m;nt,n,np=int(m[1]),int(m[2]),int(m[3]);tables.append({'case':c['target_case'],'targets':nt,'nodes':n,'pins':np,'payload_bytes':nt*n*8,'file_bytes':(out/'allmap.bin').stat().st_size,'native_query_export_seconds':float(m[4]),'scope':'Time inside post-lookahead native hook, includes enumeration/query/export; excludes native frontend/MAP initialization/full native process, subsequent hash/load/materialization.'});bindings[str(log)]=sha(log)
 assert len(tables)==12
 result={'status':'OBSERVED_INSTRUMENTATION_COMPONENTS_ACCOUNTED_COMPLETE_PAID_GAIN_UNPROVEN','preflight_rows':rows,'native_oracle_tables':tables,'required_unmeasured_or_unmatched_paid_items':['Native frontend/MAP initialization and exact routing dependency needed to construct oracle in deployed workflow','Binary schema validation, full content SHA checks, XML grammar and CID binding performed before predict','Balanced fixed-placement sketch on/off full workflow conversion, affected updates, exact routing and final quality','Fresh unseen-family full workflow repetitions with frozen seeds/configuration and hardware availability if claimed'],'interpretation':'Current Python MAP preflight spends about85% resident time constructing heuristic; replacing only that work still leaves measured search/bridge overhead. Standalone C++ vector timings do not certify full-model parity or total-time gain. No oracle costs may be silently excluded. Running frozen batch is unchanged.','bindings':bindings}
 (D/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print('COST_ACCOUNTED',len(rows),len(tables),rows[1]['heuristic_fraction_of_resident'])
if __name__=='__main__':main()
