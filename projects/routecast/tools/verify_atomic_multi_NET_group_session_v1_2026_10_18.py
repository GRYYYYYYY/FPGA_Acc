"""Detached preparation, stale ticket/price rejection and atomic reader checks."""
import copy,hashlib,json,random,threading
from pathlib import Path
from collections import Counter
from atomic_multi_NET_group_session_v1 import Session
from verify_criticality_multi_NET_group_admission_v2_2026_10_18 import fixture

def make():
 f,rc,slots,q,records=fixture(2,2,[1,1],{(0,0):1,(0,1):1,(1,0):1,(1,1):1});old=records([0,1]);ledger=Counter({i:1 for i in range(6)});crit={i:dict(criticality_numerator=1,criticality_denominator=2) for i in range(2)};s=Session(f,rc,slots,q,old,ledger,crit,{0:0,1:0});return s,records,f,rc,q,old,ledger,crit

def main():
 s,records,f,rc,q,old,ledger,crit=make();first=s.snapshot();ticket,plan=s.prepare(records([1,0]),{},generation=0,expected_epochs={0:0,1:0},price_epoch=0);assert plan['accepted'] and s.snapshot() is first
 # Caller mutation after construction/prepare cannot alter either snapshot.
 old[0][0]['answer']['physical_edge_ids'].clear();ledger.clear();q[0][0]['source']=999;rc.weights[:]=[99]*len(rc.weights);f['capacities'][:]=[0]*len(f['capacities']);crit[0]['criticality_numerator']=99
 _,records,*_=make()
 assert s.commit(ticket,generation=0,price_epoch=0)==1;assert first.generation==0 and first.epochs[0]==first.epochs[1]==0;assert s.snapshot().epochs[0]==s.snapshot().epochs[1]==1
 try:s.snapshot().records[0][0]['answer']['physical_edge_ids']+=(99,)
 except TypeError:pass
 else:raise AssertionError('mutable record snapshot')
 checked=[]
 def reject(name,fn):
  before=s.snapshot()
  try:fn()
  except (ValueError,RuntimeError,TypeError):checked.append(name)
  else:raise AssertionError(name)
  assert s.snapshot() is before
 reject('reused_ticket',lambda:s.commit(ticket,generation=1,price_epoch=0));reject('foreign_ticket',lambda:s.commit(object(),generation=1,price_epoch=0));reject('boolean_generation',lambda:s.prepare(records([0,1]),{},generation=True,expected_epochs={0:1,1:1},price_epoch=0));reject('stale_NET_epoch',lambda:s.prepare(records([0,1]),{},generation=1,expected_epochs={0:1,1:0},price_epoch=0));reject('stale_price',lambda:s.prepare(records([0,1]),{},generation=1,expected_epochs={0:1,1:1},price_epoch=1))
 bad=records([0,1]);bad[1][0]['budget_integer']=11;reject('late_second_NET_invalid_metadata',lambda:s.prepare(bad,{},generation=1,expected_epochs={0:1,1:1},price_epoch=0))
 t,_=s.prepare(records([0,1]),{},generation=1,expected_epochs={0:1,1:1},price_epoch=0);s.advance_price_epoch(generation=1);reject('ticket_invalidated_by_price_epoch',lambda:s.commit(t,generation=2,price_epoch=1));reject('old_generation_after_price_update',lambda:s.commit(t,generation=1,price_epoch=0))
 # Equal objective but higher overflow is retained without a pending ticket.
 before=s.snapshot();t,plan=s.prepare(records([0,0]),{},generation=2,expected_epochs={0:1,1:1},price_epoch=1);assert t is None and not plan['accepted'] and s.snapshot() is before
 # Competing prepared tickets cannot both publish the same generation.
 a,_=s.prepare(records([0,1]),{},generation=2,expected_epochs={0:1,1:1},price_epoch=1);b,_=s.prepare(records([0,1]),{},generation=2,expected_epochs={0:1,1:1},price_epoch=1);barrier=threading.Barrier(3);answers=[]
 def commit(t):
  barrier.wait()
  try:answers.append(('commit',s.commit(t,generation=2,price_epoch=1)))
  except RuntimeError:answers.append(('stale',None))
 threads=[threading.Thread(target=commit,args=(x,)) for x in [a,b]]
 for th in threads:th.start()
 barrier.wait()
 for th in threads:th.join()
 assert sorted(a[0] for a in answers)==['commit','stale'];assert s.snapshot().generation==3
 # A reader retains one immutable state while the main thread repeatedly publishes swaps.
 barrier=threading.Barrier(2);errors=[];reads=[]
 def reader():
  for _ in range(100):
   barrier.wait();view=s.snapshot()
   try:
    rebuilt=Counter()
    for net,recs in view.records.items():
     used=set()
     for record in recs:
      used.add(record['source'])
      # Fixture edge ordering: four SOURCE->resource arcs, then resource->SINK arcs.
      for eid in record['answer']['physical_edge_ids']:
       used.add([4,5,4,5,2,3,2,3][eid])
     rebuilt.update(used)
    assert dict(rebuilt)==dict(view.ledger) and view.epochs[0]==view.epochs[1];reads.append(view.generation)
   except Exception as e:errors.append(repr(e))
   barrier.wait()
 th=threading.Thread(target=reader);th.start()
 for i in range(100):
  view=s.snapshot();choice=[1,0] if i%2==0 else [0,1];t,p=s.prepare(records(choice),{},generation=view.generation,expected_epochs=dict(view.epochs),price_epoch=view.price_epoch);assert p['accepted'];barrier.wait();s.commit(t,generation=view.generation,price_epoch=view.price_epoch);barrier.wait()
 th.join();assert not errors and len(reads)==100
 view=s.snapshot();t,_=s.prepare({0:view.records[0],1:view.records[1]}, {},generation=view.generation,expected_epochs=dict(view.epochs),price_epoch=view.price_epoch);s.discard(t);reject('discarded_ticket',lambda:s.commit(t,generation=view.generation,price_epoch=view.price_epoch));s.close()
 try:s.snapshot()
 except RuntimeError:checked.append('closed_session')
 else:raise AssertionError('closed session accepted reader')
 r=Path(__file__).resolve().parents[1];out=r/'experiments/atomic_multi_NET_group_session_core_v1_2026-10-18';out.mkdir();files=[Path(__file__).resolve(),r/'tools/atomic_multi_NET_group_session_v1.py',r/'tools/criticality_multi_NET_group_admission_v2.py'];result=dict(status='serial_atomic_group_snapshot_publication_and_rejection_contract_pass',reader_snapshots_during_group_commits=100,competing_tickets_exactly_one_commits=True,detached_caller_inputs_and_prior_snapshots_unchanged=True,rejected_or_closed_cases=checked,whole_group_overflow_increase_rejected=True,bindings={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},scope='In-process Python serial lock/single snapshot publication prototype. No crash persistence, hardware atomicity, sparse optimized publisher, real graph search, native routing or forecast/fullflow gain.');(out/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print(result['status'],len(checked),'rejections',len(reads),'concurrent reads')
if __name__=='__main__':main()
