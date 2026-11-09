import json,sys
from pathlib import Path
from array import array
R=Path.cwd();sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from soft_demand_bounded_bridge_v1 import Search
binary=R/'experiments/soft_demand_bounded_build_v1_2026-10-08/search.so';f={'row_offsets':array('Q',[0,1,2,2]),'dest_ranks':array('Q',[1,2]),'capacities':array('Q',[1,1,1])}
class RC:
 increments=[2,2]
 def initial(self,node):return 0
s=Search(f,RC(),binary);s.prepare({},0)
try:s.search(0,{2},3)
except RuntimeError as e:assert 'status -4' in str(e)
else:raise AssertionError('insufficient bound accepted')
r=s.search(0,{2},4);assert r[2]=={2} and list(s.raw)==[0,2,4] and list(s.settled)==[1,1,1];s.close();out=R/'experiments/soft_demand_bounded_contract_v1_2026-10-08';(out/'failure_recovery.json').write_text(json.dumps({'bindings':{str(Path(__file__)):sha(Path(__file__)),str(binary):sha(binary)},'insufficient_bound_rejected_minus4':True,'next_certified_query_recovers_all_outputs':True},indent=2)+'\n');print('PASS insufficient bound/recovery')
