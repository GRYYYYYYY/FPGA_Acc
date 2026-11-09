"""Bound evidence for budget-constrained conflict repair; retain uncertainty."""
import json
from pathlib import Path
from pre_route_endpoints import sha

def run():
 b=Path('experiments/stereo_prospective_validation_2026-10-05');out=b/'conflict_budget_evidence_v2';out.mkdir()
 roots=['conflict_fixed_actual_pin_search','conflict_fixed_actual_pin_search_pruned','conflict_equivalent_pin_relaxed_search','conflict_equivalent_pin_selective_search','conflict_independent_delay_feasibility'];exhaustive=b/'conflict_independent_delay_exhaustive'
 if (exhaustive/'completion.json').exists():roots.append(exhaustive.name)
 evidence={};results={}
 for name in roots:
  r=b/name;completion=json.loads((r/'completion.json').read_text());receipt=json.loads((r/'receipt.json').read_text());protocol=json.loads((r/'protocol.json').read_text());rows=json.loads((r/'results.json').read_text())
  if completion['exit_code']!=0 or completion['receipt_sha256']!=sha(r/'receipt.json') or receipt['protocol_sha256']!=sha(r/'protocol.json') or receipt['results_sha256']!=sha(r/'results.json'):raise ValueError('unauthenticated experiment')
  if any(sha(p)!=h for p,h in protocol['inputs'].items()):raise ValueError('changed input')
  if any(sha(r/'source'/n)!=h for n,h in protocol['sources'].items()):raise ValueError('changed frozen source')
  evidence[name]={'receipt_sha256':sha(r/'receipt.json'),'completion_sha256':sha(r/'completion.json'),'status_counts':receipt['status_counts'],'wall_s':receipt['wall_s']};results[name]={x['connection_id']:x for x in rows}
 requestpath=b/'additional_high_fanout_physical_audit/conflict_repair_requests.json';requests=json.loads(requestpath.read_text());entries=[]
 for q in requests['requests']:
  cid=q['connection_id'];independent=results['conflict_independent_delay_feasibility'][cid]
  if exhaustive.name in results and cid in results[exhaustive.name]:independent=results[exhaustive.name][cid]
  pruned=results['conflict_equivalent_pin_selective_search'][cid]
  confirmed=independent['status']=='UNREACHABLE'
  if confirmed and pruned['status']!='UNREACHABLE':raise ValueError('contradictory feasibility results')
  entries.append({'connection_id':cid,'net_id':q['net_id'],'conflict_rr_nodes':q['conflict_rr_nodes'],'pruned_status':pruned['status'],'independent_status':independent['status'],'independently_confirmed_budget_infeasible':confirmed})
 resources=[]
 for n in (1321924,2272980):
  involved=[x for x in entries if n in x['conflict_rr_nodes']];forced={x['net_id'] for x in involved if x['independently_confirmed_budget_infeasible']}
  resources.append({'rr_node':n,'capacity':1,'independently_forced_net_ids':sorted(forced),'strict_policy_capacity_infeasibility_confirmed':len(forced)>1})
 report={'request_sha256':sha(requestpath),'evidence':evidence,'connections':entries,'resources':resources,'exhaustive_confirmation_pending':exhaustive.name not in results,'scope':'fixed SOURCE; SOURCE-to-OPIN, positive-capacity channels, architecture full-equivalent target IPIN-to-SINK; exact serialized buffered RC with zero Cinternal, source RC/2 included; original per-connection budgets; specified conflict resource blocked; other occupancy relaxed','limitations':['No native route-tree branch load or STA equivalence','No placement/source-class changes or budget relaxation evaluated','Global complete prediction, global capacity and legal background still pending','No repair commit, family transfer or end-to-end benefit demonstrated']}
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'connections':len(entries),'independent_confirmed':sum(x['independently_confirmed_budget_infeasible'] for x in entries),'strict_policy_capacity_infeasibility_confirmed':any(x['strict_policy_capacity_infeasibility_confirmed'] for x in resources),'pending':report['exhaustive_confirmation_pending']}),flush=True)
if __name__=='__main__':run()
