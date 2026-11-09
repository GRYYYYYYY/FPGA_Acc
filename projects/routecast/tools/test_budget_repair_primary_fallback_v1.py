"""Genuine first partial success then forced UNKNOWN, original wholeNET fallback."""
import json,copy,hashlib
from pathlib import Path
from budget_repair_criticality_tree_v1 import Graph
from criticality_retained_net_primary_v1 import route
from criticality_resident_joint_adapter_v2 import fallback
from criticality_net_admission_v1 import validate
from test_weighted_budget_pareto_search_v1 import build
R=Path(__file__).resolve().parents[1];D=R/'experiments/budget_repair_primary_fallback_contract_v1_2026-10-19'
class RC:
 def __init__(self,raw,slots):self.raw=raw;self.slots=slots
 def initial(self,n):return 0
 def increment(self,e):return self.raw[e]
 def path(self,source,sink,path):return sum(self.raw[self.slots[e]] for e in path)
def main():
 D.mkdir(exist_ok=False);offsets,dest,raw=build(7,[(0,1,1),(1,3,1),(0,6,2),(6,3,2),(0,2,3),(2,4,2),(0,5,1),(5,4,1)]);f=dict(row_offsets=offsets,dest_ranks=dest,capacities=[1]*7,edge_ids=list(range(len(dest))));slots={e:e for e in f['edge_ids']};rc=RC(raw,slots)
 def edges(nodes):return [next(e for e in range(offsets[a],offsets[a+1]) if dest[e]==b) for a,b in zip(nodes,nodes[1:])]
 qs=[dict(connection_id=0,net_id=8,source=0,sink=3),dict(connection_id=1,net_id=8,source=0,sink=4)];old=[dict(qs[0],budget_integer=4,answer=dict(status='FOUND',physical_edge_ids=edges([0,6,3]),delay=4)),dict(qs[1],budget_integer=2,answer=dict(status='FOUND',physical_edge_ids=edges([0,5,4]),delay=2))];crit={i:dict(net=8,source_rr=0,target_rr=q['sink'],local_sink_pin=i+1,criticality_numerator=1,criticality_denominator=1 if i==0 else 2) for i,q in enumerate(qs)};base=[0]*7;prices={5:100};ledger={n:1 for n in [0,6,3,5,4]};before=copy.deepcopy([qs,old,ledger,crit]);g=Graph(f,raw,[0]*7);g.repair_label_limit=1;primary=route(g,qs,old,crit,prices,f['edge_ids'],ledger,f['capacities'],slots);assert not primary['complete'] and primary['first_failed_connection_id']==1;assert primary['search_results'][0]['committed'] and primary['search_results'][0]['path_slots']!=tuple(old[0]['answer']['physical_edge_ids']);assert primary['search_results'][1]['status']=='UNKNOWN_LABEL_LIMIT';assert primary['settled']=={3};assert 4 not in primary['parents'];state=copy.deepcopy([primary['parents'],primary['settled']]);answer=fallback(f,rc,slots,qs,old,primary['parents'],primary['settled'],prices,1,base,crit,10000);validate(f,rc,slots,qs,answer['records']);assert len(answer['records'])==2 and answer['records'][1]==old[1];assert [qs,old,ledger,crit]==before and [primary['parents'],primary['settled']]==state
 invalid=copy.deepcopy(old);invalid[1]['budget_integer']=1
 try:fallback(f,rc,slots,qs,invalid,primary['parents'],primary['settled'],prices,1,base,crit,10000)
 except ValueError:pass
 else:raise AssertionError('invalid old fallback budget accepted')
 g.close();files=[Path(__file__).resolve(),R/'tools/budget_repair_criticality_tree_v1.py',R/'tools/criticality_retained_net_primary_v1.py',R/'tools/criticality_resident_joint_adapter_v2.py'];(D/'verification.json').write_text(json.dumps(dict(status='GENUINE_PARTIAL_SUCCESS_THEN_UNKNOWN_ORIGINAL_WHOLE_NET_FALLBACK_VALIDATED',first_connection_changed=True,second_forced_UNKNOWN=True,complete_fallback_paths_budgets_shared_parent_valid=True,unknown_connection_original_path_preserved=True,caller_records_ledger_and_partial_tree_unchanged=True,invalid_old_fallback_rejected=True,bindings={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},scope='Fixture label cap1 forces UNKNOWN, not actual production exhaustion. Existing wholeNET choice may retain improved first CID while safely retaining old UNKNOWN CID; not a claim entire old NET must be restored.'),indent=2)+'\n');print('PARTIAL_SUCCESS_UNKNOWN_FALLBACK_CONTRACT_PASS')
if __name__=='__main__':main()
