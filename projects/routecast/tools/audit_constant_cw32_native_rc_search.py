"""Full frozen-cohort exact lattice parity with independent Fraction search."""
import json,time,shutil
from pathlib import Path
from fractions import Fraction
from collections import Counter,defaultdict
from prepared_csr import read,U64
from buffered_rc_context import load
from csr_exact_buffered_rc import ExactBufferedRC
from integer_rc_context import IntegerRC
from native_integer_rc_search import NativeIntegerRC
from csr_integer_budget_search import query
from pre_route_endpoints import sha

def main():
 root=Path(__file__).resolve().parents[1];out=root/'experiments/constant_multiplier_cw32_native_rc_parity_2026-10-06';out.mkdir();(out/'sources').mkdir()
 for n in ('audit_constant_cw32_native_rc_search.py','native_integer_rc_search.py','integer_rc_context.py','csr_integer_budget_search.py','csr_exact_buffered_rc.py','prepared_csr.py','buffered_rc_context.py','buffered_rc_node_classes.py','pre_route_endpoints.py'):shutil.copyfile(root/'tools'/n,out/'sources'/n)
 protocol={'cpp_source_sha256':sha(root/'tools/rc_budget_native/search.cpp'),'native_binary_sha256':sha(root/'build/rc_budget_native_2026-10-06/search.so'),'cohort':[f'mult_{i:03d}' for i in range(1,7)],'sources':{p.name:sha(p) for p in (out/'sources').iterdir()},'scope':'Exact LCM-scaled delay, all first-pass queries and wholeNET admission same as archived Fraction driver. No integer-width cap/hardware claim. One execution wall time, no paired performance gain claim.'};(out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');reports=[]
 for name in protocol['cohort']:
  start=time.monotonic();dest=out/name;dest.mkdir();parent=root/'experiments/constant_multiplier_cw32_rc_budgeted_nets_2026-10-06'/name;prior=json.loads((parent/'receipt.json').read_text());assert sha(parent/'queries.jsonl')==prior['queries_sha256'];truth={r['connection_id']:r['result'] for r in map(json.loads,(parent/'queries.jsonl').read_text().splitlines())};baseline=root/'experiments/constant_multiplier_family_predictions_cw32_2026-10-06'/name/'sparse_reset';br=json.loads((baseline/'receipt.json').read_text());assert sha(baseline/'prediction.json')==br['prediction_sha256'];pred=json.loads((baseline/'prediction.json').read_text());context=root/'experiments/constant_multiplier_cw32_exact_buffered_rc_classes_2026-10-06'/name;parity=json.loads((context/'baseline_parity.json').read_text());assert sha(context/'baseline_budgets.json')==parity['baseline_budgets_sha256'] and sha(baseline/'receipt.json')==parity['prediction_receipt_sha256'];budgets={r['connection_id']:Fraction(*r['exact_delay_s']) for r in json.loads((context/'baseline_budgets.json').read_text())};m,f=read(root/'experiments/constant_multiplier_family_length_switch_csr_cw32_2026-10-06'/name/'csr',pred['physical_graph_sha256']);rc=ExactBufferedRC(f,*load(context,pred['physical_graph_sha256']));t=time.monotonic();integer=IntegerRC(rc);native=NativeIntegerRC(integer);init_s=time.monotonic()-t;groups=defaultdict(list);edge={f['edge_ids'][i]:(n,f['dest_ranks'][i]) for n in range(m['nodes']) for i in range(f['row_offsets'][n],f['row_offsets'][n+1])}
  for r in pred['connections']:groups[r['net_id']].append(r)
  def union(rows):
   nodes=set()
   for r in rows:
    nodes.add(r['source'])
    for e in r['physical_edge_ids']:nodes.update(edge[e])
   return nodes
  unions={n:union(rows) for n,rows in groups.items()};occ=Counter(n for nodes in unions.values() for n in nodes);overflow=lambda values:sum(max(0,v-f['capacities'][n]) for n,v in values.items());checked=0;max_delay=0;max_objective=0;t=time.monotonic()
  for net,rows in sorted(groups.items()):
   other=occ.copy();other.subtract(unions[net]);native.set_other(other);candidate=[]
   for r in rows:
    result=native.query(r['source'],r['sink'],integer.encode(budgets[r['connection_id']]),10000);old=truth[r['connection_id']];assert result['status']==old['status'] and result['physical_edge_ids']==old['physical_edge_ids'] and result['cost']==old['cost'];assert Fraction(result['delay'],integer.scale)==Fraction(old['delay']);candidate.append({**r,'physical_edge_ids':result['physical_edge_ids']});checked+=1;max_delay=max(max_delay,result['delay']);max_objective=max(max_objective,result['cost'])
   staged=other.copy();newunion=union(candidate);staged.update(newunion)
   if overflow(staged)<=overflow(occ):occ=staged;unions[net]=newunion
  report={'design':name,'queries_exact_same_path_cost_delay':checked,'final_overflow':overflow(occ),'scale_bits':integer.scale.bit_length(),'max_found_delay_bits':max_delay.bit_length(),'max_found_objective_bits':max_objective.bit_length(),'max_increment_bits':max(integer.increments).bit_length(),'reference_receipt_sha256':sha(parent/'receipt.json'),'baseline_receipt_sha256':sha(baseline/'receipt.json'),'budget_parity_sha256':sha(context/'baseline_parity.json'),'context_conversion_s':init_s,'search_and_state_s':time.monotonic()-t,'driver_wall_s':time.monotonic()-start};assert report['final_overflow']==prior['final_overflow'];reports.append(report);print(json.dumps(report),flush=True)
 assert sha(root/'tools/rc_budget_native/search.cpp')==protocol['cpp_source_sha256'] and sha(root/'build/rc_budget_native_2026-10-06/search.so')==protocol['native_binary_sha256']
 assert all(sha(out/'sources'/n)==h for n,h in protocol['sources'].items());(out/'receipt.json').write_text(json.dumps({'protocol_sha256':sha(out/'protocol.json'),'results':reports},indent=2)+'\n')
if __name__=='__main__':main()
