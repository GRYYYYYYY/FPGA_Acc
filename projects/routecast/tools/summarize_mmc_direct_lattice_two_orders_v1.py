"""Authenticate two complete audit orders; retain descriptive timing scope."""
import json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
roots=[R/'experiments/mmc_complete_direct_lattice_audits_v1_2026-10-10',R/'experiments/mmc_complete_direct_lattice_audits_reverse_v2_2026-10-10']
bindings=closure([Path(__file__)]);rows=[]
def authenticated(path):
 data=json.loads(path.read_text())
 for section in ['bindings','files']:
  for p,h in data.get(section,{}).items():
   assert sha(p)==h,(path,p)
   bindings[p]=h
 bindings[str(path)]=sha(path)
 return data
for d,order in zip(roots,[['control','direct'],['direct','control']]):
 v=authenticated(d/'verification.json');protocol=authenticated(d/'protocol.json')
 assert protocol['order']==order and [x['mode'] for x in v['rows']]==order
 assert v['all_three_complete_proof_outputs_equal_except_source_bindings']
 times={x['mode']:x['local_subprocess_seconds'] for x in v['rows']}
 assert all(x['exit_code']==0 and x['local_subprocess_seconds']>0 for x in v['rows'])
 assert v['observed_single_pair_direct_over_cached_control']==times['direct']/times['control']
 contexts={}
 for mode in order:
  s=authenticated(d/mode/'shared_audit_receipt.json')
  assert s['all_three_complete_audits_pass'] and s['complete_audit_bodies_AST_preserved'] and s['fresh_independent_graph_context']
  stats=s['diagnostics'];assert stats['contexts']==stats['context_loads']==1 and stats['independent_xml_parses']==2 and stats['accesses']==3
  contexts[mode]=stats
 for name in ['initial_physical_verification.json','sketch_physical_verification.json','verification.json']:
  proofs=[authenticated(d/mode/name) for mode in ['control','direct']]
  assert {k:v for k,v in proofs[0].items() if k!='bindings'}=={k:v for k,v in proofs[1].items() if k!='bindings'}
 for filename in ['initial.json','floors.json','round0.json','round1.json','sketch.json']:
  hashes=[sha(root/mode/filename) for root in roots for mode in ['control','direct']]
  assert len(set(hashes))==1,filename
 rows.append(dict(order=order,seconds=times,direct_minus_control_seconds=times['direct']-times['control'],ratio=times['direct']/times['control'],context_diagnostics=contexts,cache_diagnostics=v['cache_diagnostics']))
assert rows[0]['cache_diagnostics']==rows[1]['cache_diagnostics']
corruption=R/'experiments/direct_lattice_full_frame_fault_v1_2026-10-10/verification.json'
c=authenticated(corruption);assert c['wrong_exact_scale_rejected_by_actual_full_frame_delay_assertion']
assert all(sha(p)==h for p,h in bindings.items())
D=R/'experiments/mmc_direct_lattice_two_orders_summary_v1_2026-10-10';D.mkdir()
result=dict(bindings=bindings,both_orders_complete_audits_equal_and_inputs_authenticated=True,rows=rows,observed_direct_faster_in_both_orders=all(x['ratio']<1 for x in rows),scope='Two complete development audit observations with opposite order. Full prediction states byte matched, fresh independent contexts, all three proof bodies retained, exact outputs equal except source bindings. Not randomized repetitions, population stability, strict heldout or full workflow time gain. Corruption witness is complete XTEA initial-frame wrong lattice scalar only, not MMC full event/fallback fault coverage.')
(D/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='bindings'},indent=2))
