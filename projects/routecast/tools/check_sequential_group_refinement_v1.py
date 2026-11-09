"""Exercise real loop: off parity, one changed draft, no-op epochs, UNKNOWN."""
import json,copy,hashlib
from pathlib import Path
from check_group_vacancy_proposal_v1 import fixture
from sequential_group_refinement_v1 import refine,digest
R=Path(__file__).resolve().parents[1];D=R/'experiments/sequential_group_refinement_contract_v1_2026-10-20'
def main():
 D.mkdir(exist_ok=False);f,g,rc,slots,qs,old,new,crit,ledger=fixture();rc.scale=10**18;state=dict(records=old[0]+old[1],ledger={str(n):v for n,v in ledger.items()},epochs={'0':0,'1':0},prices={});before=copy.deepcopy(state);queries=qs[0]+qs[1];schedule=[dict(members=[0,1]) for _ in range(3)]
 off,a=refine(f,rc,slots,g,queries,crit,[1]*6,{},state,schedule,D/'off',False);assert off==before and state==before
 on,b=refine(f,rc,slots,g,queries,crit,[1]*6,{},state,schedule,D/'on',True);assert state==before and b['counts']=={'GROUP_DRAFT_MATERIALIZED':1,'RETAIN_IDENTICAL_PROPOSAL':2} and on['epochs']=={'0':1,'1':1};assert {q['connection_id']:q for q in on['records']}=={q['connection_id']:q for recs in new.values() for q in recs};events=[json.loads(x) for x in (D/'on/events.jsonl').read_text().splitlines()];assert events[-1]['state_digest_after']==digest(on);assert events[0]['expected_epochs']=={'0':0,'1':0} and events[1]['expected_epochs']=={'0':1,'1':1}
 unchanged,c=refine(f,rc,slots,g,queries,crit,[1]*6,{},state,schedule,D/'unknown',True,max_labels=1);assert unchanged==before and c['counts']=={'NO_COMPLETE_GROUP_PROPOSAL':3}
 files=[Path(__file__),R/'tools/sequential_group_refinement_v1.py',R/'tools/group_vacancy_proposal_v3.py',R/'tools/group_draft_frame_v2.py'];(D/'verification.json').write_text(json.dumps(dict(status='SEQUENTIAL_OFF_PARITY_CHANGED_DRAFT_NOOP_AND_UNKNOWN_LOOP_CONTRACT_PASS',bindings={str(p.resolve()):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}),indent=2)+'\n');print('SEQUENTIAL_OFF_PARITY_CHANGED_DRAFT_NOOP_AND_UNKNOWN_LOOP_CONTRACT_PASS')
if __name__=='__main__':main()
