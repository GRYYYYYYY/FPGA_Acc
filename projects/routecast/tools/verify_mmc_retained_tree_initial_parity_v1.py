"""Require byte-identical complete initial state and floors against control."""
import json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent/"native_resume_prototype"))
from pre_route_endpoints import sha
from source_binding_v2 import closure
R=Path(__file__).resolve().parents[1]
def main():
 out=R/'experiments/mmc_retained_tree_full_schedule_v1_2026-10-13'
 control=R/'experiments/mmc_delayed_history_ablation_v1_2026-10-13'
 bindings=closure([Path(__file__)])
 def load(p):
  bindings[str(p)]=sha(p)
  return json.loads(p.read_text())
 assert load(control/'pipeline_terminal.json')['all_stages_completed']
 proof=load(control/'model/initial_physical_verification.json')
 assert proof['all_original_queries_xml_fraction_rc_budgets_singleparent_and_uniqueNET_and_independent_ledgers_pass']
 assert all(sha(p)==h for p,h in proof['bindings'].items())
 bindings.update(proof['bindings'])
 equal={}
 for name in ['initial.json','floors.json']:
  a=out/'model'/name;b=control/'model'/name
  x=load(a);y=load(b)
  assert x==y and bindings[str(a)]==bindings[str(b)]
  if name=='initial.json':
   assert x['completed_connections']==x['required_connections']==115572
  equal[name]=True
 assert all(sha(p)==h for p,h in bindings.items())
 dest=out/'initial_parity_v1.json'
 assert not dest.exists()
 dest.write_text(json.dumps(dict(bindings=bindings,entire_initial_and_floors_equal=all(equal.values()),files=equal,control=str(control),scope='Complete JSON and byte SHA equality; no timing or quality assertion.'),indent=2)+'\n')
 print('Complete initial/floors parity PASS',flush=True)
if __name__=='__main__':main()
