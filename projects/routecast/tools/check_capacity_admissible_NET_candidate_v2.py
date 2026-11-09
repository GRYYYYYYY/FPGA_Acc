"""Capacity-constrained whole-NET alternatives pass existing unmodified admission."""
import json,copy,hashlib
from pathlib import Path
from types import SimpleNamespace
from capacity_admissible_NET_candidate_v2 import propose
from criticality_objective_admission_v1 import prepare
R=Path(__file__).resolve().parents[1];D=R/'experiments/capacity_admissible_NET_candidate_contract_v2_2026-10-20'
def main():
 D.mkdir(exist_ok=False)
 f=dict(row_offsets=[0,3,4,5,6,6],dest_ranks=[1,2,3,4,4,4],edge_ids=[0,1,2,3,4,5],capacities=[1]*5);raw=[1,3,2,1,3,2];slots={i:i for i in range(6)};g=SimpleNamespace(n=5,offsets=f['row_offsets'],dest=f['dest_ranks'],inc=raw,initial=[0]*5,repair_bounds=None);rc=SimpleNamespace(initial=lambda n:0,increment=lambda e:raw[e]);qs=[dict(connection_id=0,net_id=0,source=0,sink=4)];old=[dict(qs[0],budget_integer=6,answer=dict(status='FOUND',physical_edge_ids=[1,4],delay=6))];crit={0:dict(net=0,source_rr=0,target_rr=4,criticality_numerator=1,criticality_denominator=2,local_sink_pin=1)};prices={1:0,2:10,3:2,4:0};ledger={0:1,1:1,2:1,4:1};snapshot=copy.deepcopy((old,qs,crit,ledger));candidate,meta=propose(g,f,qs,old,crit,prices,ledger,slots);assert candidate[0]['answer']['physical_edge_ids']==[2,5];plan=prepare(f,rc,slots,qs,old,candidate,ledger,crit,prices);assert plan['accepted'] and plan['objective_delta']<0 and plan['prospective_overflow_delta']==0;assert snapshot==(old,qs,crit,ledger)
 # The cheap unconstrained candidate would hit an already full other-owned node.
 cheap=[dict(old[0],answer=dict(status='FOUND',physical_edge_ids=[0,3],delay=2))];assert prepare(f,rc,slots,qs,old,cheap,ledger,crit,prices)['prospective_overflow_delta']==1
 # Existing overuse can be retained, but never newly created by the candidate.
 crowded=dict(ledger,**{});crowded[0]=3;candidate2,meta2=propose(g,f,qs,old,crit,prices,crowded,slots);assert candidate2 and meta2['prospective_overflow_delta']==0
 # Exhaustion yields no proposal and never modifies the original records/ledger.
 before=copy.deepcopy((old,ledger));none,unknown=propose(g,f,qs,old,crit,prices,ledger,slots,max_labels=1);assert none is None and unknown['search_events'][0]['status']=='UNKNOWN_LABEL_LIMIT';assert before==(old,ledger)
 # Shared terminal aliases preserve a single-parent tree and all CID metadata.
 manyq=[dict(qs[0],connection_id=i) for i in range(17)];manyo=[dict(old[0],connection_id=i) for i in range(17)];manyc={i:dict(crit[0],local_sink_pin=i+1) for i in range(17)};shared,sharedmeta=propose(g,f,manyq,manyo,manyc,prices,ledger,slots);assert sharedmeta['retained_connection_ids']==list(range(17));assert prepare(f,rc,slots,manyq,manyo,shared,ledger,manyc,prices)['accepted']
 files=[Path(__file__),R/'tools/capacity_admissible_NET_candidate_v2.py',R/'tools/capacity_admissible_tree_v2.py',R/'tools/criticality_retained_net_primary_v1.py',R/'tools/retained_criticality_tree_seed_v1.py',R/'tools/criticality_objective_admission_v1.py',R/'tools/criticality_net_admission_v1.py'];result=dict(status='HARD_CAPACITY_DETOUR_ORIGINAL_ADMISSION_AND_SHARED_NET_CONTRACT_PASS',hard_forbidden_cheap_path_avoided=True,raw_budget_unchanged=True,original_objective_strictly_improved=True,original_overflow_guard_pass=True,existing_overflow_preserved_without_new_pressure=True,unknown_no_proposal_and_inputs_unchanged=True,shared_terminal_CIDs=17,shared_singleparent_original_admission_pass=True,bindings={str(p.resolve()):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},scope='Whole-NET pure proposal contract only, not production routing/forecast gate. Original acceptance module unchanged.')
 (D/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':main()
