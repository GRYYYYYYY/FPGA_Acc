"""Batch counterexamples and exact pure-state/legacy-single-NET contracts."""
import copy,json,hashlib
from pathlib import Path
from types import SimpleNamespace
from group_vacancy_proposal_v1 import Snapshot,prepare,propose
from criticality_objective_admission_v1 import prepare as legacy
R=Path(__file__).resolve().parents[1];D=R/'experiments/group_vacancy_proposal_contract_v1_2026-10-20'
def fixture(no_B_detour=False,shared_new_channel=False):
 arcs=[(0,2,5),(0,3,1),(1,2,1),(1,3,5),(2,4,5),(2,5,1),(3,4,1),(3,5,5)]
 if no_B_detour:arcs.remove((1,2,1))
 n=7 if shared_new_channel else 6
 if shared_new_channel:arcs.extend([(0,6,1),(1,6,1),(6,4,1),(6,5,1)])
 arcs.sort();offsets=[0];dest=[];inc=[];ids=[];lookup={}
 for u in range(n):
  for a,b,w in arcs:
   if a==u:lookup[a,b]=len(dest);dest.append(b);inc.append(w);ids.append(len(ids))
  offsets.append(len(dest))
 f=dict(row_offsets=offsets,dest_ranks=dest,edge_ids=ids,capacities=[1]*n);g=SimpleNamespace(n=n,offsets=offsets,dest=dest,inc=inc,initial=[0]*n,repair_bounds=None);rc=SimpleNamespace(initial=lambda node:0,increment=lambda edge:inc[edge]);slots={i:i for i in ids};queries={0:[dict(connection_id=0,net_id=0,source=0,sink=4)],1:[dict(connection_id=1,net_id=1,source=1,sink=5)]};old={};new={};crit={}
 for net,source,sink,oldchan,newchan in [(0,0,4,2,3),(1,1,5,3,2)]:
  q=queries[net][0];path=[lookup[source,oldchan],lookup[oldchan,sink]];old[net]=[dict(q,budget_integer=10,answer=dict(status='FOUND',physical_edge_ids=path,delay=10))];crit[net]=dict(net=net,source_rr=source,target_rr=sink,criticality_numerator=1,criticality_denominator=2,local_sink_pin=1)
  if not no_B_detour or net==0:
   channel=6 if shared_new_channel else newchan;path=[lookup[source,channel],lookup[channel,sink]];new[net]=[dict(old[net][0],answer=dict(status='FOUND',physical_edge_ids=path,delay=2))]
 ledger={i:1 for i in range(6)};return f,g,rc,slots,queries,old,new,crit,ledger

def main():
 D.mkdir(exist_ok=False);f,g,rc,slots,qs,old,new,crit,ledger=fixture();state=dict(records=old,ledger=ledger,epochs={0:7,1:9});before=copy.deepcopy(state);s=Snapshot(f,rc,slots,qs,old,ledger,crit,[1]*6,{}, {},0)
 plan=prepare(s,new);assert plan['accepted'] and plan['prospective_overflow_delta']==0 and plan['objective_delta']==-8 and plan['updates']=={}
 for n in qs:
  one=Snapshot(f,rc,slots,{n:qs[n]},{n:old[n]},ledger,crit,[1]*6,{}, {},0);a=prepare(one,{n:new[n]});b=legacy(f,rc,slots,qs[n],old[n],new[n],ledger,crit,one);assert a['prospective_overflow_delta']==b['prospective_overflow_delta']==1 and not a['accepted'] and not b['accepted'];assert a['old_score']==b['old_score'] and a['candidate_score']==b['candidate_score']
 candidate,meta=propose(s,g);assert meta['plan']['accepted'] and candidate==new and state==before
 none,unknown=propose(s,g,max_labels=1);assert none is None and unknown['events'][0]['search_events'][-1]['status']=='UNKNOWN_LABEL_LIMIT' and state==before
 f2,g2,rc2,slots2,qs2,old2,_,crit2,ledger2=fixture(no_B_detour=True);state2=copy.deepcopy((old2,ledger2));s2=Snapshot(f2,rc2,slots2,qs2,old2,ledger2,crit2,[1]*6,{}, {},0);none,failure=propose(s2,g2);assert none is None and failure['failed_NET']==1 and failure['events'][0]['complete'] and failure['partial_trees_discarded'];assert state2==(old2,ledger2)
 f3,g3,rc3,slots3,qs3,old3,new3,crit3,ledger3=fixture(shared_new_channel=True);s3=Snapshot(f3,rc3,slots3,qs3,old3,ledger3,crit3,[1]*7,{}, {},0);joint=prepare(s3,new3);assert not joint['accepted'] and joint['prospective_overflow_delta']==1
 for n in qs3:
  one=Snapshot(f3,rc3,slots3,{n:qs3[n]},{n:old3[n]},ledger3,crit3,[1]*7,{}, {},0);assert prepare(one,{n:new3[n]})['accepted']
 corruptions=0
 for bad in [{0:new[0]},dict(new,**{})]:
  bad=copy.deepcopy(bad)
  if len(bad)==2:bad[0][0]['budget_integer']=11
  try:prepare(s,bad)
  except ValueError:corruptions+=1
  else:raise AssertionError('candidate corruption accepted')
 missing=dict(ledger);missing[2]=0
 try:Snapshot(f,rc,slots,qs,old,missing,crit,[1]*6,{}, {},0)
 except ValueError:corruptions+=1
 else:raise AssertionError('missing owner accepted')
 assert state==before
 files=[Path(__file__),R/'tools/group_vacancy_proposal_v1.py',R/'tools/capacity_admissible_tree_v2.py',R/'tools/criticality_net_admission_v1.py',R/'tools/criticality_objective_admission_v1.py'];result=dict(status='PURE_GROUP_RELEASE_SEARCH_ADMISSION_AND_FAILURE_CONTRACTS_PASS',individually_blocked_exchange_joint_admitted=True,group_vacancy_finds_exchange=True,legacy_single_NET_score_and_pressure_equal=True,individually_admissible_proposals_joint_conflict_rejected=True,UNKNOWN_preserves_inputs=True,later_NET_failure_discards_earlier_scratch_tree=True,caller_records_ledger_epochs_unchanged=True,corruptions_rejected=corruptions,bindings={str(p.resolve()):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},scope='Pure separately defined batch criterion only; no runtime commit, concurrent atomicity, forecast gain or production qualification.')
 (D/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':main()
