"""Fixed quality gate over full exposed candidate cohort; not online search."""
import json,shutil
from pathlib import Path
from fractions import Fraction
from collections import defaultdict,Counter
from net_rc_admission import admit_rc_net
from pre_route_endpoints import sha
from prepared_csr import read
from streaming_prediction_audit import verify


def main():
 root=Path(__file__).resolve().parents[1];out=root/'experiments/adder_tree_online_dynamic_net_rc_admission_2026-10-06';out.mkdir();(out/'sources').mkdir()
 for n in ('audit_online_dynamic_net_rc_admission.py','net_rc_admission.py','streaming_prediction_audit.py','physical_prediction_audit.py','net_union_topology.py','prepared_csr.py','pre_route_endpoints.py'):shutil.copyfile(root/'tools'/n,out/'sources'/n)
 quality=root/'experiments/adder_tree_online_dynamic_net_quality_2026-10-06';qr=json.loads((quality/'receipt.json').read_text());protocol={'quality_receipt_sha256':sha(quality/'receipt.json'),'sources':{p.name:sha(p) for p in (out/'sources').iterdir()},'gate':'every connection exact RC <= same-placement baseline; candidate full NET unique demand overflow <= previously accepted state; scalar growth allowed; fixed ascending NET order','scope':'Post-outcome development admission, not budget-constrained online search, not native STA or pin legality. Does not use native QoR labels. Joint overflow nonincrease gate included; posthoc complete candidate mixture is not online endogenous-cost search.'};(out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');summary=[]
 for q in qr['results']:
  name=q['design'];dest=out/name;dest.mkdir();qualityfile=quality/name/'connections.json';assert sha(qualityfile)==q['connection_report_sha256'];metrics=json.loads(qualityfile.read_text());step=int(name.split('_')[1]);oldfile=(root/'experiments/adder_tree_family_predictions_2026-10-06/adder_tree_2L_032bits/sparse_reset/prediction.json') if step==0 else (root/'experiments/adder_tree_2L032_move_sequence_audit_2026-10-06'/f'step_{step}_prediction.json');assert sha(oldfile)==q['reference_prediction_sha256'];old=json.loads(oldfile.read_text());newfile=root/'experiments/adder_tree_online_dynamic_net_sequence_2026-10-06'/f'step_{step}_prediction.json';assert sha(newfile)==q['prediction_sha256'];new=json.loads(newfile.read_text());oldrows={r['connection_id']:r for r in old['connections']};newrows={r['connection_id']:r for r in new['connections']};groups=defaultdict(list)
  for r in old['connections']:groups[r['net_id']].append(r['connection_id'])
  metric={r['connection_id']:r for r in metrics};assert set(metric)==set(oldrows)==set(newrows)
  prepared=root/'experiments/adder_tree_family_length_switch_csr_2026-10-06/adder_tree_2L_032bits';m,f=read(prepared/'csr',old['physical_graph_sha256']);edge={eid:(src,f['dest_ranks'][slot]) for src in range(m['nodes']) for slot in range(f['row_offsets'][src],f['row_offsets'][src+1]) for eid in [f['edge_ids'][slot]]}
  def union(rows):
   nodes=set()
   for r in rows:
    nodes.add(r['source'])
    for eid in r['physical_edge_ids']:nodes.update(edge[eid])
   return nodes
  active=dict(oldrows);unions={net:union([oldrows[c] for c in ids]) for net,ids in groups.items()};occ=Counter(n for nodes in unions.values() for n in nodes);decisions=[]
  for net,ids in sorted(groups.items()):
   baseline={c:Fraction(metric[c]['old_rc_s_exact']) for c in ids};candidate={c:Fraction(metric[c]['new_rc_s_exact']) for c in ids};before=(dict(active),dict(occ));decision=admit_rc_net(baseline,candidate)
   if decision['accepted']:
    candidate_union=union([newrows[c] for c in ids]);staged=occ.copy();staged.subtract(unions[net]);staged.update(candidate_union);assert all(v>=0 for v in staged.values());old_over=sum(max(0,v-f['capacities'][n]) for n,v in occ.items());new_over=sum(max(0,v-f['capacities'][n]) for n,v in staged.items())
    if new_over>old_over:decision['accepted']=False;decision['capacity_rejected']=True
   if decision['accepted']:
    active.update({c:newrows[c] for c in ids});unions[net]=candidate_union;occ=staged
   else:assert before==(dict(active),dict(occ)) and all(active[c]==oldrows[c] for c in ids)
   decisions.append({'net_id':net,**decision})
  result={'physical_graph_sha256':old['physical_graph_sha256'],'connections':[active[c] for c in sorted(active)],'node_occupancy':{str(n):v for n,v in occ.items() if v},'requested':len(active),'completed':len(active),'methods':dict(Counter(r['method'] for r in active.values()))};ep=json.loads(((root/'experiments/adder_tree_family_endpoints_2026-10-06/adder_tree_2L_032bits/endpoints.json') if step==0 else root/'experiments/adder_tree_2L032_move_sequence_2026-10-06'/f'step_{step}_endpoints.json').read_text());fp=json.loads((root/'experiments/adder_tree_2L032_move_sequence_2026-10-06/protocol.json').read_text());audit=verify(fp['inputs']['rr_graph']['path'],ep,result,topology=True);assert audit['all_physical_and_union_checks_passed']
  (dest/'prediction.json').write_text(json.dumps(result)+'\n');(dest/'decisions.json').write_text(json.dumps(decisions,indent=2)+'\n');(dest/'audit.json').write_text(json.dumps(audit)+'\n');row={'design':name,'accepted_nets':sum(d['accepted'] for d in decisions),'rejected_nets':sum(not d['accepted'] for d in decisions),'overuse':audit['all_type_overuse_units'],'prediction_sha256':sha(dest/'prediction.json'),'decisions_sha256':sha(dest/'decisions.json'),'audit_sha256':sha(dest/'audit.json')};summary.append(row);print(json.dumps(row),flush=True)
 assert all(sha(out/'sources'/n)==h for n,h in protocol['sources'].items());(out/'receipt.json').write_text(json.dumps({'protocol_sha256':sha(out/'protocol.json'),'results':summary},indent=2)+'\n')
if __name__=='__main__':main()
