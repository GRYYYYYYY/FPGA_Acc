"""Fault-injected label-limit AFTER successful staging must restore full warm NET."""
import json,copy,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent/'native_resume_prototype'))
import budget_constrained_native_reuse_initializer_v1 as initializer
from compiled_criticality_tree_v1 import Graph,BINARY
from check_native_channel_reuse_initializer_v2 import csr,record
from source_binding_v2 import closure
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];D=R/'experiments/budget_constrained_native_reuse_fallback_contract_v1_2026-10-19'
def main():
 D.mkdir(exist_ok=False);f,inc,s=csr(8,{(0,1):1,(0,2):1,(0,3):1,(1,4):2,(1,5):2,(1,6):2,(1,7):2,(2,6):1,(3,7):1});g=Graph(f,inc,[0]*8);kinds=['SOURCE']+['CHANX']*3+['SINK']*4;old=[record(0,0,4,[s[0,1],s[1,4]],inc),record(1,0,5,[s[0,1],s[1,5]],inc)];q=[dict(connection_id=0,net_id=0,source=0,sink=6),dict(connection_id=1,net_id=0,source=0,sink=7)];warm={0:record(0,0,6,[s[0,2],s[2,6]],inc)['answer'],1:record(1,0,7,[s[0,3],s[3,7]],inc)['answer']};snapshot=copy.deepcopy(old);real=initializer.expand;staged=[]
 def injected(*args,**kwargs):
  if not staged:
   a=real(*args,**kwargs);assert a['committed'] and list(a['path_slots'])!=warm[0]['physical_edge_ids'];staged.append(a);return a
  return dict(status='UNKNOWN_LABEL_LIMIT',committed=False,labels_created=10000,expanded=10,label_limit=10000)
 try:
  initializer.expand=injected;result=initializer.initialize(g,f,kinds,q,old,{0:10,1:10},range(len(inc)),lambda:copy.deepcopy(warm))
 finally:initializer.expand=real
 assert result['whole_NET_fallback'] and result['fallback_reason']=='UNKNOWN_LABEL_LIMIT' and result['answers']==warm and old==snapshot;assert [r['status'] for r in result['repair_searches']]==['COMMITTED','UNKNOWN_LABEL_LIMIT']
 try:initializer.initialize(g,f,kinds,q,old,{0:1,1:1},range(len(inc)),lambda:copy.deepcopy(warm))
 except ValueError:pass
 else:raise AssertionError('invalid baseline budget admitted')
 assert old==snapshot;g.close();(D/'verification.json').write_text(json.dumps(dict(status='PARTIAL_SUCCESS_THEN_UNKNOWN_ROLLS_BACK_TO_ENTIRE_AUDITED_WARM_NET',unknown_is_fault_injected_control_flow_fixture=True,real_label_exhaustion_covered_in_core_contract=True,invalid_warm_fallback_rejected=True,source_records_unchanged=True,bindings={**closure([Path(__file__)]),str(BINARY):sha(BINARY)},scope='Atomic control-flow regression, not real-work exhaustion or performance evidence. Production label limit10000 remains fixed.'),indent=2)+'\n');print('PASS partial success->UNKNOWN fullNET rollback; invalid fallback rejected')
if __name__=='__main__':main()
