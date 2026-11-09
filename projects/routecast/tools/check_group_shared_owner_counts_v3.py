"""Exact multiplicity of overlapping old owners and cross-NET CID validation."""
import copy,json,hashlib
from pathlib import Path
from check_group_vacancy_proposal_v3 import fixture
from group_vacancy_proposal_v3 import Snapshot,prepare,propose
R=Path(__file__).resolve().parents[1];D=R/'experiments/group_shared_owner_counts_contract_v3_2026-10-20'
def main():
 D.mkdir(exist_ok=False);f,g,rc,slots,qs,detour,shared,crit,_=fixture(shared_new_channel=True);old=copy.deepcopy(shared);ledger={0:1,1:1,4:1,5:1,6:2};crit={n:dict(q,criticality_numerator=0,criticality_denominator=1) for n,q in crit.items()};before=copy.deepcopy((old,ledger));s=Snapshot(f,rc,slots,qs,old,ledger,crit,[1]*7,{}, {},0);assert s.oldcount[6]==2 and s.outside.get(6,0)==0 and s.get(6)==1;keep=prepare(s,old);assert keep['accepted'] and keep['prospective_overflow_delta']==0;release=prepare(s,detour);assert release['accepted'] and release['prospective_overflow_delta']==-1 and release['updates'][6]==0;fresh,meta=propose(s,g);assert fresh is not None and meta['plan']['accepted'] and meta['plan']['prospective_overflow_delta']==-1;assert before==(old,ledger)
 badqs=copy.deepcopy(qs);badold=copy.deepcopy(old);badqs[1][0]['connection_id']=0;badold[1][0]['connection_id']=0
 try:Snapshot(f,rc,slots,badqs,badold,ledger,crit,[1]*7,{}, {},0)
 except ValueError:pass
 else:raise AssertionError('cross NET duplicate CID admitted')
 badcrit=copy.deepcopy(crit);badcrit[1]['target_rr']=4
 try:Snapshot(f,rc,slots,qs,old,ledger,badcrit,[1]*7,{}, {},0)
 except ValueError:pass
 else:raise AssertionError('stale criticality identity admitted')
 files=[Path(__file__),R/'tools/group_vacancy_proposal_v3.py',R/'tools/check_group_vacancy_proposal_v3.py'];(D/'verification.json').write_text(json.dumps(dict(status='SHARED_OLD_OWNER_MULTIPLICITY_RELEASE_EXISTING_PRESSURE_AND_CID_CONTRACT_PASS',shared_node_old_owner_count=2,outside_owner_count=0,existing_overflow_removed=1,cross_NET_duplicate_CID_rejected=True,criticality_identity_drift_rejected=True,inputs_unchanged=True,bindings={str(p.resolve()):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}),indent=2)+'\n');print('SHARED_OLD_OWNER_MULTIPLICITY_RELEASE_EXISTING_PRESSURE_AND_CID_CONTRACT_PASS')
if __name__=='__main__':main()
