"""Optimistic stale checks, nonaliasing drafts and complete source-frame preservation."""
import copy,json,hashlib
from pathlib import Path
from group_vacancy_proposal_v3 import Snapshot,prepare
from group_draft_frame_v2 import materialize
from check_group_vacancy_proposal_v1 import fixture
R=Path(__file__).resolve().parents[1];D=R/'experiments/group_draft_frame_contract_v2_2026-10-20'
def main():
 D.mkdir(exist_ok=False);f,g,rc,slots,qs,old,new,crit,ledger=fixture();extra=copy.deepcopy(old[0][0]);extra.update(connection_id=2,net_id=2);ledger=dict(ledger)
 for node in [0,2,4]:ledger[node]+=1
 frame=dict(records=old[0]+old[1]+[extra],ledger={str(n):v for n,v in ledger.items()},epochs={'0':7,'1':9,'2':11},prices={});before=copy.deepcopy(frame);s=Snapshot(f,rc,slots,qs,old,ledger,crit,[1]*6,{}, {},0);draft,meta=materialize(s,new,frame,{0:7,1:9});assert meta['status']=='GROUP_DRAFT_MATERIALIZED';assert draft['epochs']=={'0':8,'1':10,'2':11};assert draft['records'][2]==extra and draft['records'][2] is not extra and frame==before;assert draft['prices']==frame['prices'];assert {q['connection_id'] for q in draft['records']}=={0,1,2};draft['records'][2]['answer']['delay']=999;assert frame==before
 stale=[]
 for label,mutate,status in [('epoch',lambda x:x['epochs'].update({'0':8}),'RETAIN_STALE_MEMBER_EPOCH'),('ledger',lambda x:x['ledger'].update({'0':3}),'RETAIN_STALE_LEDGER'),('history',lambda x:x['prices'].update({'2':1}),'RETAIN_STALE_HISTORY'),('records',lambda x:x['records'][0].update(budget_integer=11),'RETAIN_STALE_MEMBER_RECORDS')]:
  state=copy.deepcopy(frame);mutate(state);frozen=copy.deepcopy(state);none,event=materialize(s,new,state,{0:7,1:9});assert none is None and event['status']==status and frozen==state;stale.append(label)
 # A caller changing its own retained record cannot alter the detached snapshot.
 old[0][0]['budget_integer']=11;qs[0][0]['sink']=5;assert s.old[0][0]['budget_integer']==10 and s.queries[0][0]['sink']==4 and prepare(s,new)['accepted'];assert frame['records'][0]['budget_integer']==11;none,event=materialize(s,new,frame,{0:7,1:9});assert none is None and event['status']=='RETAIN_STALE_MEMBER_RECORDS';frame=before
 none,event=materialize(s,None,frame,{0:7,1:9});assert none is None and event['status']=='RETAIN_NO_COMPLETE_GROUP_PROPOSAL'
 f3,g3,rc3,slots3,qs3,old3,new3,crit3,ledger3=fixture(shared_new_channel=True);s3=Snapshot(f3,rc3,slots3,qs3,old3,ledger3,crit3,[1]*7,{}, {},0);badframe=dict(records=old3[0]+old3[1],ledger={str(n):v for n,v in ledger3.items()},epochs={'0':0,'1':0},prices={});frozen=copy.deepcopy(badframe);none,event=materialize(s3,new3,badframe,{0:0,1:0});assert none is None and not event['plan']['accepted'] and event['plan']['prospective_overflow_delta']==1 and badframe==frozen
 # The API takes no precomputed plan, so an external accepted=True cannot bypass prepare.
 invalids=[]
 for label,change in [('duplicate_CID',lambda x:x['records'].append(copy.deepcopy(x['records'][0]))),('epoch_coverage',lambda x:x['epochs'].pop('2')),('unknown_derived_schema',lambda x:x.update(independent_connection_ledger={}))]:
  state=copy.deepcopy(frame);change(state);frozen=copy.deepcopy(state)
  try:materialize(s,new,state,{0:7,1:9})
  except ValueError:invalids.append(label)
  else:raise AssertionError('invalid round-frame accepted')
  assert state==frozen
 try:materialize(s,new,frame,{0:7,'0':7,1:9})
 except ValueError:invalids.append('canonical_epoch_key_alias')
 else:raise AssertionError('aliased epoch keys accepted')
 files=[Path(__file__),R/'tools/group_draft_frame_v2.py',R/'tools/group_vacancy_proposal_v3.py'];result=dict(status='DETACHED_GROUP_DRAFT_STALE_CHECKS_EPOCHS_AND_COMPLETE_FRAME_CONTRACT_PASS',stale_states_rejected=stale,malformed_frames_rejected=invalids,source_snapshot_detached_from_caller_edits=True,recomputes_admission_not_external_plan=True,UNKNOWN_no_draft=True,outside_records_and_epochs_preserved=True,accepted_draft_nonaliasing_and_source_unchanged=True,bindings={str(p.resolve()):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},scope='Pure state object materialization at explicit fixed criticality and immutable graph, from admitted round-frame only. No external concurrent publication or latest-STA guarantee.')
 (D/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print(result['status'])
if __name__=='__main__':main()
