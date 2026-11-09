"""Hash-bound full-cohort feedback evidence, native-only timing."""
import json
from pathlib import Path
from pre_route_endpoints import sha
from prepared_csr import read
from incremental_channel_pressure import ChannelPressure

def main():
 root=Path(__file__).resolve().parents[1];out=root/'experiments/multiplier_cw32_rc_budget_pressure_trial_2026-10-06';receipt=json.loads((out/'receipt.json').read_text());assert sha(out/'protocol.json')==receipt['protocol_sha256'];ad=root/'experiments/multiplier_cw32_rc_budgeted_nets_2026-10-06';ar=json.loads((ad/'receipt.json').read_text());quality=root/'experiments/multiplier_cw32_rc_budgeted_quality_2026-10-06';qr=json.loads((quality/'receipt.json').read_text());rows=[]
 for name,h in receipt['case_receipts'].items():
  d=out/name;assert sha(d/'receipt.json')==h;cr=json.loads((d/'receipt.json').read_text());assert sha(d/'inputs.json')==cr['inputs_sha256'];inputs=json.loads((d/'inputs.json').read_text());assert all(sha(v['path'])==v['sha256'] for v in inputs['inputs'].values());assert sha(ad/name/'receipt.json')==inputs['prediction_receipt_sha256'];a=next(r for r in ar['results'] if r['design']==name);assert a['all_final_rc_budgets_met'] and sha(ad/name/'prediction.json')==a['prediction_sha256'];assert sha(ad/name/'audit.json')==a['audit_sha256']==inputs['prediction_audit_receipt_sha256'];pred=json.loads((ad/name/'prediction.json').read_text());q=next(r for r in qr['results'] if r['design']==name);assert q['rc_increased']==0;assert sha(quality/name/'connections.json')==q['connection_report_sha256']
  m,f=read(root/'experiments/multiplier_family_length_switch_csr_cw32_2026-10-06'/name/'csr',inputs['inputs']['rr_graph']['sha256']);cache=ChannelPressure(f['types'],f['capacities']);occ={int(k):v for k,v in pred['node_occupancy'].items()};cache.refresh(occ,occ);assert cache.payload(pred['physical_graph_sha256'])==(d/'candidate.pressure').read_text();assert sha(d/'candidate.pressure')==inputs['pressure_sha256']
  by={mode:[r for r in cr['rows'] if r['mode']==mode] for mode in ('off','on')}
  for mode,rr in by.items():
   assert len(rr)==2 and len({r['route_sha256'] for r in rr})==1
   for r in rr:
    tag=f"{r['run']:02d}_{mode}";log=d/(tag+'.log');assert sha(log)==r['log_sha256'];assert sha(root/'work/multiplier_cw32_rc_budget_pressure_trial_2026-10-06'/name/tag/'design.route')==r['route_sha256'];text=log.read_text();assert ('RouteCast pressure applied' in text)==(mode=='on')
    if mode=='on':assert f'RouteCast pressure applied: {len(cache.rows)} channel nodes' in text
    if r['success']:
     p=json.loads((d/(tag+'_physical.json')).read_text());assert p['inputs_sha256']=={'graph':pred['physical_graph_sha256'],'route':r['route_sha256']} and p['overflow_units']==0 and p['all_printed_branch_arc_switch_and_union_checks_pass']
  old=json.loads((root/'experiments/multiplier_cw32_pressure_trial_2026-10-06'/name/'receipt.json').read_text());assert by['off'][0]['route_sha256']==old['rows'][0]['route_sha256'];rows.append({'design':name,'success':{mode:by[mode][0]['success'] for mode in by},'overused':{mode:by[mode][0]['final_overused_nodes'] for mode in by},'cpd':{mode:by[mode][0]['cpd_ns'] for mode in by},'wirelength':{mode:by[mode][0]['wirelength'] for mode in by},'mean_native_s':{mode:sum(r['native_route_s'] for r in rr)/len(rr) for mode,rr in by.items()}})
 (out/'verified_summary.json').write_text(json.dumps({'receipt_sha256':sha(out/'receipt.json'),'verifier_sha256':sha(__file__),'rows':rows,'scope':'Single ABBA native-only timings; prior search and RC/audit costs excluded, no end-to-end benefit claim.'},indent=2)+'\n');print(json.dumps(rows))
if __name__=='__main__':main()
