"""Reconstruct consumed pool payloads and verify actual archived native evidence."""
from pathlib import Path
from fractions import Fraction
import json
from pre_route_endpoints import sha
from prepared_csr import read
from pooled_channel_pressure import rows,payload

def main():
 root=Path(__file__).resolve().parents[1];out=root/'experiments/multiplier_cw32_pooled_pressure_trial_2026-10-06';receipt=json.loads((out/'receipt.json').read_text());assert sha(out/'protocol.json')==receipt['protocol_sha256'];summary=[]
 for name,h in receipt['case_receipts'].items():
  dest=out/name;assert sha(dest/'receipt.json')==h;case=json.loads((dest/'receipt.json').read_text());assert sha(dest/'inputs.json')==case['inputs_sha256'];inp=json.loads((dest/'inputs.json').read_text());assert all(sha(v['path'])==v['sha256'] for v in inp['inputs'].values());assert sha(dest/'candidate.pressure')==inp['pressure_sha256']
  predroot=root/'experiments/multiplier_family_predictions_cw32_2026-10-06'/name/'sparse_reset';pr=json.loads((predroot/'receipt.json').read_text());assert sha(predroot/'receipt.json')==inp['prediction_receipt_sha256'];assert sha(predroot/'prediction.json')==pr['prediction_sha256'];pred=json.loads((predroot/'prediction.json').read_text());prepared=root/'experiments/multiplier_family_length_switch_csr_cw32_2026-10-06'/name;m,f=read(prepared/'csr',inp['inputs']['rr_graph']['sha256']);pressure,proofs=rows(f,{int(k):v for k,v in pred['node_occupancy'].items()});assert payload(m['nodes'],inp['inputs']['rr_graph']['sha256'],pressure)==(dest/'candidate.pressure').read_text();assert json.loads((dest/'pool_proofs.json').read_text())==json.loads(json.dumps(proofs))
  for proof in proofs:assert sum(f['capacities'][n]*(pressure[n][1]-1) for n in proof['nodes'])==Fraction(proof['excess'])
  by={mode:[r for r in case['rows'] if r['mode']==mode] for mode in ('off','on')}
  for mode,rr in by.items():
   assert len(rr)==2 and len({r['route_sha256'] for r in rr})==1
   for r in rr:
    tag=f"{r['run']:02d}_{mode}";log=dest/(tag+'.log');assert sha(log)==r['log_sha256'];route=root/'work/multiplier_cw32_pooled_pressure_trial_2026-10-06'/name/tag/'design.route';assert sha(route)==r['route_sha256'];text=log.read_text();assert ('RouteCast pressure applied' in text)==(mode=='on')
    if mode=='on':assert f'RouteCast pressure applied: {len(pressure)} channel nodes' in text
    if r['success']:
     phys=json.loads((dest/(tag+'_physical.json')).read_text());assert phys['inputs_sha256']=={'graph':inp['inputs']['rr_graph']['sha256'],'route':r['route_sha256']};assert phys['overflow_units']==0 and phys['all_printed_branch_arc_switch_and_union_checks_pass']
  old=json.loads((root/'experiments/multiplier_cw32_pressure_trial_2026-10-06'/name/'receipt.json').read_text());assert by['off'][0]['route_sha256']==old['rows'][0]['route_sha256']
  summary.append({'design':name,'off_success':by['off'][0]['success'],'on_success':by['on'][0]['success'],'off_overused':by['off'][0]['final_overused_nodes'],'on_overused':by['on'][0]['final_overused_nodes'],'off_cpd':by['off'][0]['cpd_ns'],'on_cpd':by['on'][0]['cpd_ns'],'off_wirelength':by['off'][0]['wirelength'],'on_wirelength':by['on'][0]['wirelength'],'pressure_rows':len(pressure),'active_pools':len(proofs),'mean_native_s':{mode:sum(r['native_route_s'] for r in rr)/len(rr) for mode,rr in by.items()}})
 report={'receipt_sha256':sha(out/'receipt.json'),'verifier_sha256':sha(__file__),'rows':summary,'payload_reconstruction_and_exact_capacity_weighted_excess_conservation':True,'scope':'Native-only timing, one ABBA cycle, exposed development cohort; no full-pipeline or unseen generalization claim.'};(out/'verified_summary.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(summary))
if __name__=='__main__':main()
