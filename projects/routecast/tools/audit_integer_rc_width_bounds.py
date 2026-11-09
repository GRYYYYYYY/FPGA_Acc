"""Conservative bounds for fixed-budget nonnegative Pareto RC queries."""
import json
import shutil
from pathlib import Path
from fractions import Fraction
from prepared_csr import read, U64
from buffered_rc_context import load
from csr_exact_buffered_rc import ExactBufferedRC
from integer_rc_context import IntegerRC
from pre_route_endpoints import sha


def main():
 root=Path(__file__).resolve().parents[1]
 out=root/'experiments/integer_rc_width_bounds_2026-10-06'
 out.mkdir();(out/'sources').mkdir()
 names=['audit_integer_rc_width_bounds.py','integer_rc_context.py','csr_integer_budget_search.py','csr_exact_buffered_rc.py','buffered_rc_context.py','buffered_rc_node_classes.py','prepared_csr.py','pre_route_endpoints.py']
 for n in names:shutil.copyfile(root/'tools'/n,out/'sources'/n)
 proof=('For fixed nonnegative objective and delay, an accepted label cannot repeat an ancestor node: the ancestor or a transitive dominating label dominates the returning candidate. Thus accepted paths have at most N-1 edges; attempted candidates have at most N edges. Stored delay <= budget; pre-filter addition <= budget+max_increment. OtherNET unique demand <= totalNET-1, so edge objective <= max_scalar*totalNET and attempted objective <= N*max_scalar*totalNET. These bounds require unchanged per-query costs/eligibility/context and rejection of negative values; they do not bound number of Pareto labels or predecessor storage.')
 protocol={'sources':{n:sha(out/'sources'/n) for n in names},'proof':proof,'scope':'Two frozen cw32 cohorts, prepared graph/budget authentication, conservative arithmetic bounds only. Not an implementation, hardware feasibility, STA or performance proof.'}
 (out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n')
 results=[]
 for prefix,cohort in [('',[f'mult_{w}x{w}' for w in range(4,10)]),('constant_',[f'mult_{i:03d}' for i in range(1,7)])]:
  for name in cohort:
   base=root/f'experiments/{prefix}multiplier_family_predictions_cw32_2026-10-06'/name/'sparse_reset'
   receipt=json.loads((base/'receipt.json').read_text());assert sha(base/'prediction.json')==receipt['prediction_sha256']
   pred=json.loads((base/'prediction.json').read_text())
   context=root/f'experiments/{prefix}multiplier_cw32_exact_buffered_rc_classes_2026-10-06'/name
   parity=json.loads((context/'baseline_parity.json').read_text());assert sha(context/'baseline_budgets.json')==parity['baseline_budgets_sha256'];assert sha(base/'receipt.json')==parity['prediction_receipt_sha256']
   meta,f=read(root/f'experiments/{prefix}multiplier_family_length_switch_csr_cw32_2026-10-06'/name/'csr',pred['physical_graph_sha256'])
   rc=IntegerRC(ExactBufferedRC(f,*load(context,pred['physical_graph_sha256'])))
   budgets=[rc.encode(Fraction(*x['exact_delay_s'])) for x in json.loads((context/'baseline_budgets.json').read_text())]
   net_count=len({x['net_id'] for x in pred['connections']})
   assert net_count>0 and all(x>=0 for x in rc.increments)
   eligible=[i for i,c in enumerate(f['costs']) if c!=U64 and f['capacities'][f['dest_ranks'][i]]>0]
   max_scalar=max((int(f['costs'][i]) for i in eligible),default=0)
   max_inc=max((rc.increments[i] for i in eligible),default=0)
   bounds={'scale':rc.scale,'stored_delay':max(budgets),'attempted_delay':max(budgets)+max_inc,'edge_objective':max_scalar*net_count,'attempted_objective':meta['nodes']*max_scalar*net_count}
   row={'family':prefix or 'variable','design':name,'nodes':meta['nodes'],'nets':net_count,'bounds':bounds,'unsigned_bits':{k:max(1,v.bit_length()) for k,v in bounds.items()},'budget_parity_sha256':sha(context/'baseline_parity.json'),'baseline_receipt_sha256':sha(base/'receipt.json'),'graph_sha256':pred['physical_graph_sha256']}
   results.append(row);print(json.dumps(row),flush=True)
 assert all(sha(out/'sources'/n)==v for n,v in protocol['sources'].items())
 (out/'receipt.json').write_text(json.dumps({'protocol_sha256':sha(out/'protocol.json'),'results':results},indent=2)+'\n')

if __name__=='__main__':main()
