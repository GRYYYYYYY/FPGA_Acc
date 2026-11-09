"""Group-only copies preserve plans, paths and UNKNOWN/partial failure transcripts."""
import json,hashlib,copy
from pathlib import Path
from check_group_vacancy_proposal_v1 import fixture
import group_vacancy_proposal_v2 as old_api
import group_vacancy_proposal_v3 as new_api
R=Path(__file__).resolve().parents[1];D=R/'experiments/group_criticality_copy_equivalence_v1_2026-10-20'
def main():
 D.mkdir(exist_ok=False);rows=[]
 for mode,options in [('exchange',{}),('later_failure',{'no_B_detour':True}),('shared_new_conflict',{'shared_new_channel':True})]:
  f,g,rc,slots,qs,old,new,crit,ledger=fixture(**options);full=dict(crit);full.update({1000+i:dict(crit[0]) for i in range(20000)});snapshots=[api.Snapshot(f,rc,slots,qs,old,ledger,full,[1]*g.n,{}, {},0) for api in (old_api,new_api)];assert len(snapshots[0].criticalities)==20002 and len(snapshots[1].criticalities)==2
  if set(new)==set(qs):assert old_api.prepare(snapshots[0],new)==new_api.prepare(snapshots[1],new)
  for limit in [1,10000]:assert old_api.propose(snapshots[0],g,limit)==new_api.propose(snapshots[1],g,limit)
  full[0]['criticality_numerator']=0;assert snapshots[1].criticalities[0]['criticality_numerator']==1;rows.append(dict(mode=mode,original_copied_rows=20002,new_copied_rows=2,plans_and_all_search_transcripts_identical=True))
 files=[Path(__file__),R/'tools/group_vacancy_proposal_v2.py',R/'tools/group_vacancy_proposal_v3.py'];(D/'verification.json').write_text(json.dumps(dict(status='GROUP_ONLY_CRITICALITY_COPY_EXACT_EQUIVALENCE_PASS',rows=rows,bindings={str(p.resolve()):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},scope='Semantic and copied-row reduction contract, not end-to-end speed claim.'),indent=2)+'\n');print('GROUP_ONLY_CRITICALITY_COPY_EXACT_EQUIVALENCE_PASS')
if __name__=='__main__':main()
