"""Exhaustive small admission truth table, purity and boundary checks."""
import copy,json,hashlib,itertools
from pathlib import Path
from fractions import Fraction
from strict_joint_progress_admission_v1 import filter_plan
R=Path(__file__).resolve().parents[1];D=R/'experiments/strict_joint_progress_admission_contract_v1_2026-10-20'
def main():
 D.mkdir(exist_ok=False);count=0
 for od,pd,changed,accepted in itertools.product([Fraction(-1,3),Fraction(0),Fraction(1,7)],[-1,0,1],[False,True],[False,True]):
  old=[{'connection_id':0,'source':0,'sink':2,'answer':{'physical_edge_ids':[0,1]}}];new=copy.deepcopy(old)
  if changed:new[0]['answer']['physical_edge_ids']=[2,3]
  plan={'accepted':accepted,'status':'COMMITTED' if accepted else 'ORIGINAL_REJECTION','objective_delta':od,'prospective_overflow_delta':pd,'updates':{1:2}};before=copy.deepcopy((plan,old,new));result=filter_plan(plan,old,new);reject=accepted and changed and od==0 and pd==0
  assert result['accepted']==(accepted and not reject);assert result['status']==('RETAIN_NO_STRICT_PROGRESS' if reject else plan['status']);assert (plan,old,new)==before;count+=1
 try:filter_plan({'accepted':True},old,[])
 except ValueError:pass
 else:raise AssertionError('CID mismatch accepted')
 files=[Path(__file__),R/'tools/strict_joint_progress_admission_v1.py',R/'tools/run_wbuart_strict_joint_progress_v1.py',R/'tools/verify_wbuart_strict_joint_progress_v1.py',R/'experiments/strict_joint_progress_admission_design_v1_2026-10-20/protocol.json'];(D/'verification.json').write_text(json.dumps({'status':'ALL72_TRUTH_TABLE_BOUNDARIES_PURITY_AND_CID_REJECTION_PASS','cases':count,'scope':'Admission filter contract only; no physical pipeline qualification or quality claim.','bindings':{str(p.resolve()):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}},indent=2)+'\n');print('PASS',count)
if __name__=='__main__':main()
